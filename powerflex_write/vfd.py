"""
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied.  See the License for the
specific language governing permissions and limitations
under the License.
"""

import minimalmodbus
import os
import time

from tkinter import messagebox

"""
Used to write parameters to a VFD using minimalmodbus.  Typically, just the IP Address

Calling write will search the output directory for files names that start with
"VFD".  The file is parsed, getting each parameter, writing them one at a time.

A successful write will move file to the completed directory.  Unsuccessful writes
will leave the file, which will need to be inspected for a typo.  These files are typically
auto-generated, so there shouldn't be typos unless they have been manually edited.
"""
class Writer:

    def __init__(self, parent):
        self.parent = parent

    def write(self, com_port, path, callback):

        self.com_port = com_port
        self.path = path
        self.current_dir = os.path.abspath(os.getcwd() + "/" + self.path) 
        self.completed_dir = os.path.abspath(self.current_dir + '/completed')

        try:
            self.parent.log.info("Writer - Starting connection to drive")
            self.comm = minimalmodbus.Instrument(self.com_port, 100)
            self.comm.serial.baudrate = 9600
            self.comm.serial.timeout = 0.5
            self.comm.mode = minimalmodbus.MODE_RTU
        except:
            self.parent.log.info("Writer - Failed to open {}, quitting".format(com_port))

        self.callback = callback
        # process all of the drive files
        n = self._process_drives()

    def _process_drives(self):
        """
        Start processing files
        """
        drive_list = self._get_text_files()
        retry = True

        # create completed directory
        if not os.path.exists(self.completed_dir):
            self.parent.log.info("Writer - creating completed directory")
            os.makedirs(self.completed_dir)

        for drive in drive_list:
            while retry:
                # prompt the user to plug into a drive
                self.parent.log.info("Writer - Waiting to connect to {}".format(drive[:-4]))
                messagebox.showinfo("Information","Connect to {} then press OK to continue".format(drive[:-4]))

                self.parent.log.info("Writer - Writing to {}".format(drive[:-4]))
                p1 = os.path.abspath(self.current_dir + '/' + drive)
                p2 = os.path.abspath(self.completed_dir + '/' + drive)
                result = self._parse_file(p1)

                if result == True:
                    # failed to write, notify the user
                    self.parent.log.info("Writer - Failed to write to {}. Make sure there were no typo's in the file".format(drive[:-4]))
                    retry = self._yes_or_no()
                else:
                    try:
                        os.rename(p1, p2)
                        self.callback(drive)
                        retry = False
                    except OSError:
                        self.parent.log.info("Writer - File {} already exists in completed directory".format(drive))
                        retry = False

            retry = True
        self.parent.log.info("Writer - Finished writing all drive files")
        messagebox.showinfo("Information", "Writing VFD parameters complete!")

    def _get_text_files(self):
        """
        Find all text files in the current directory
        and return them as a list
        """
        drive_files = []
        for text_file in os.listdir(self.current_dir):
            if text_file.endswith('.vfd'):
                drive_files.append(text_file)

        drive_files.sort()
        self.parent.log.info("Writer - Retrieved VFD files")
        return drive_files

    def _yes_or_no(self):
        """
        Prompt user with yes/no retry when failing to write to a drive
        """
        self.parent.log.info("Writer - Asking user to retry")
        reply = messagebox.askquestion("Information", "Failed to write to drive, do you want to try again?")
        self.parent.log.info("Writer - User chose {} to retry".format(reply))
        if reply == 'yes':
            return True
        elif reply == 'no':
            return False
        else:
            return False

    def _parse_file(self, file_name):
        """
        Processes each parameter in a text file
        and sends the write command
        """
        with open(file_name, 'r') as parm_file:
            drive_model = ''
            for line in parm_file:
                if line == '\n':
                    pass
                elif line.startswith('*'):
                    drive_model = line[1:].strip()
                elif line.startswith('#'):
                    pass
                else:
                    s = line.split(':')
                    result = self._write_parameter(drive_model, int(s[0]), int(s[2]))
                    if result == True:
                        return True
        return False

    def _write_parameter(self, model, parameter, value):
        """
        Write the individual parameter to the drive
        """
        self.parent.log.info("Writer - Writing {} to parameter {}".format(value, parameter))
        time.sleep(0.1)
        try:
            self.comm.write_register(parameter, value)
            return False
        except Exception as e:
            self.parent.log.info("Writer - {}".format(e))
            return True
        