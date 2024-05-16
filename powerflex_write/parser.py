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

import l5x
import re
import sys
from collections import OrderedDict

"""
Read L5X files and generate I/O lists, rung text or VFD parameter lists

I/O lists are useful to copy/paste into your HMI application I/O screen
message files.  They are formatted in a similar way as the local message
files.  The list is based on your tag name and alias' in your program.

Rung text file is useful to copy/paste rung text into your program to map
the I/O to the HMI objects.  Add a new rung, double click to edit the rung
text, paste the copied text from the rung_text.txt output file, press
Enter on the keyboard.

VFD output files contain the VFD IP Address, formatted to writing the parameters
to the VFD using the RS485 cable and the DSI port.
"""


class Parse:

    def __init__(self, parent):
        self.parent = parent

        self.file_name = ""
        self.prj = None

        self.vfds = []

    def generate_vfd_files(self, file_name):
        """
        Get a list of all the VFDs and generate parameter
        list files for them
        """
        self.file_name = file_name
        self.prj = l5x.Project(self.file_name)
        vfds = []

        for m in self.prj.modules.names:
            if m.startswith("VFD"):
                vfd_name = m
                vfd_address = self.prj.modules[m].ports[2].address
                vfds.append((vfd_name, vfd_address))
        self.parent.log.info("Parser - VFDs retrieved from L5X")
        self._vfd_file(vfds)

    def _vfd_file(self, modules):
        """
        Save our VFD list to files, which can be used to write
        the parameters to.
        """
        self.parent.log.info("Parser - Generating VFD output files")
        for m in modules:
            addr = m[1].split(".")
            tmp = m[0].split("_")
            fn = "output/{}_{}_{}.vfd".format(tmp[0], addr[3], tmp[1])
            with open(fn, "w") as f:
                f.write("*PF525\n")
                f.write("128:En Addr Sel:1\n")
                f.write("129:En IP Addr Cfg 1:{}\n".format(addr[0]))
                f.write("130:En IP Addr Cfg 2:{}\n".format(addr[1]))
                f.write("131:En IP Addr Cfg 3:{}\n".format(addr[2]))
                f.write("132:En IP Addr Cfg 4:{}\n".format(addr[3]))
                f.write("133:En Subnet Cfg 1:255\n")
                f.write("134:En Subnet Cfg 2:255\n")
                f.write("135:En Subnet Cfg 3:255\n")

        self.parent.log.info("Parser - {} VFD files generated".format(len(modules)))
