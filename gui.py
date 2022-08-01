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

import logging
import os
import powerflex_write.enhanced_listbox
import powerflex_write.parser
import powerflex_write.vfd
import serial.tools.list_ports
import subprocess
import tkinter as tk

from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk


class Window(tk.Frame):

    def __init__(self, main=None):
        tk.Frame.__init__(self, main)
        self.main = main

        self.l5x_file = tk.StringVar()
        self.l5x_file.set("")

        self.port_val = tk.StringVar()
        self.port_val.set("")

        self.output_val = tk.StringVar()
        self.output_val.set("output/")

        self.files = tk.StringVar()
        self.file_name = self.l5x_file.get()
        #self.selected_file = ""

        self.parser = powerflex_write.parser.Parse(self)
        self.writer = powerflex_write.vfd.Writer(self)     

        # make the output directory to put generated files
        if not os.path.exists("output"):
            os.mkdir("output")

        self.files = self.get_vfd_files() 

        self.log_file = "{}logjammin.log".format(self.output_val.get())
        logging.basicConfig(filename=self.log_file, filemode="w", format='%(asctime)s - %(message)s')
        self.log = logging.getLogger()
        self.log.setLevel(logging.DEBUG)

        self.init_window()

    def init_window(self):
        self.log.info("GUI - Initializing UI")
        # update title
        self.main.title("Write Powerflex Parameters")

        # create a menu
        menu = tk.Menu(self.main)
        self.main.config(menu=menu)

        # Add file dropdown with exit
        file = tk.Menu(menu)
        file.add_command(label="Open L5X", command=self.file_open)
        file.add_command(label="Open Log", command=self.open_log)
        file.add_command(label="Refresh Com", command=self.refresh_com)
        file.add_command(label="Exit", command=self.close)
        menu.add_cascade(label="File", menu=file)

        # frame for file/open
        self.frame1 = tk.LabelFrame(self.main, text="Choose L5X")
        self.frame1.pack(fill=tk.BOTH, padx=5, pady=5)

        self.l5x_entry = tk.Entry(self.frame1, textvariable=self.l5x_file)
        self.l5x_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        self.open = tk.Button(self.frame1, text="...", command=self.file_open)
        self.open.pack(side=tk.LEFT, expand=tk.NO, padx=5, pady=5)

        self.start_vfd = tk.Button(self.frame1, text="Generate VFD Files", command=self.generate_vfd)
        self.start_vfd.pack(side=tk.BOTTOM, padx=5, pady=5)
        self.start_vfd['state'] = 'disabled'

        # frame for writing VFD parameters
        self.frame3 = tk.LabelFrame(self.main, text="Write VFD")
        self.frame3.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.com_lbl = tk.Label(self.frame3, text="COM Port:")
        self.com_lbl.grid(row=0, column=0, pady=2, sticky="e")

        self.com_port = ttk.Combobox(self.frame3, textvariable=self.port_val)
        self.com_port.grid(row=0, column=1, pady=2, sticky="w")
        self.refresh_com()

        self.out_lbl = tk.Label(self.frame3, text="Output Dir:")
        self.out_lbl.grid(row=1, column=0, pady=2, stick="e")

        self.output_dir = tk.Entry(self.frame3, textvariable=self.output_val)
        self.output_dir.grid(row=1, column=1, pady=2, sticky="w")

        self.write_parm = tk.Button(self.frame3, text="Write VFD Parameters", command=self.write_vfd)
        self.write_parm.grid(row=2, column=0, padx=5, pady=5)

        self.refresh_com = tk.Button(self.frame3, text="Refresh COM Ports", command=self.refresh_com)
        self.refresh_com.grid(row=2, column=1, padx=5, pady=5)

        self.frame4 = tk.LabelFrame(self.main, text="Files")
        self.frame4.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.files_list = powerflex_write.enhanced_listbox.EnhancedListbox(self, self.frame4, selectmode="multiple")
        self.files_list.pack(fill=tk.BOTH, padx=5, pady=5)
        self.refresh_file_list()

        self.log.info("GUI - UI Loaded")

    def file_open(self):
        """
        Handle opening a L5X file
        """
        filetypes = [('L5X files', '*.L5X')]
        self.log.info("GUI - Opening file")
        self.file_name = filedialog.askopenfilename(filetypes=filetypes)
        self.log.info("GUI - File {} opened".format(self.file_name))

        if self.file_name:
            self.log.info("GUI - Parsing file {}".format(self.file_name))
            self.l5x_file.set(self.file_name)
            self.log.info("GUI - File {} parsed".format(self.file_name))

            self.start_vfd['state'] = 'normal'

    def generate_vfd(self):
        """
        Generate files for writing IP address to VFDs
        """
        self.log.info("GUI - Generate VFD files requested")
        self.parser.generate_vfd_files(self.file_name)
        messagebox.showinfo("Information","VFD files generated")
        self.refresh_file_list()

    def refresh_file_list(self):
        """
        Clear out our file list, then refresh it
        """
        self.files_list.delete(0,tk.END)
        self.files = self.get_vfd_files() 
        for f in self.files:
            self.files_list.insert(tk.END, f)

    def write_vfd(self):
        """
        Write VFD parameters from generated files
        """
        self.log.info("GUI - Write VFD parameters requested")
        self.writer.write(self.port_val.get(), self.output_dir.get(), self.write_callback)

    def write_callback(self, name):
        """
        Called each time a drive is successfully written to.
        Delete the name from the list
        """
        idx = self.files_list.get(0, tk.END).index(name)
        self.files_list.delete(idx)

    def refresh_com(self):
        """
        update our com port combo box with available
        ports
        """
        self.log.info("GUI - Refreshing com ports")
        ports = serial.tools.list_ports.comports()
        stuff = []
        for port, desc, hwid in sorted(ports):
            self.log.info("GUI - Found COM port: {}".format(port))
            stuff.append(port)
        self.com_port["values"] = stuff
        try:
            self.com_port.current(len(ports)-1)
        except:
            pass

    def get_vfd_files(self):
        """
        Find all text files in the current directory
        and return them as a list
        """
        drive_files = []
        for text_file in os.listdir(self.output_val.get()):
            if text_file.endswith('.vfd'):
                drive_files.append(text_file)

        drive_files.sort()
        return drive_files

    def open_log(self):
        """
        Open log file from menu
        """
        self.log.info("GUI - Opening log file with notepad")
        subprocess.call(["notepad.exe", self.log_file])

    def close(self):
        """
        Exit app
        """
        self.log.info("GUI - User exit requested")
        exit()


root = tk.Tk()
root.geometry("460x360")
root.resizable(False, False)
app = Window(root)
root.mainloop()