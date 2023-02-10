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

        self.io_modules = []
        self.vfds = []

        self.safety_io = r'Rack[0-9]:[0-9]+:[I|O].Pt[0-9]+.Data'
        self.standard_io = r'Rack[0-9]+:[I|O].Data\[[0-9]+\].[0-9]'
        self.weird_io = r'Rack[0-9]:[0-9]+:[I|O].[0-9]+'

    def generate_io_list(self, file_name):
        self.file_name = file_name
        self.prj = l5x.Project(self.file_name)
        # retrieve the tags that are important to us
        tags = self._get_tags()
        # get all the I/O modules used by our tags
        mods = self._get_io_modules()
        # generate an I/O list based on the modules and tags
        self._generate_list(mods, tags)
        # generate the rung text for the I/O list
        self._generate_rungs(mods)

    def generate_phenolic_list(self, file_name, filters=[]):
        self.file_name = file_name
        self.prj = l5x.Project(self.file_name)

        tags = self.prj.controller.tags
        tag_names = tags.names

        final = []
        for t in tag_names:
            for f in filters:
                if t.startswith(f):
                    final.append(t)

        return final

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

    def _get_tags(self):
        """
        Return a list of alias I/O addresses and
        tag names
        """
        self.parent.log.info("Parser - Gathering tag list")
        tags = self.prj.controller.tags
        tag_names = tags.names

        d = {}
        for name in tag_names:
            try:
                d[tags[name].alias_for] = name
            except (Exception, ):
                pass

        od = OrderedDict(sorted(d.items()))
        self.parent.log.info("Parser - Tag list gathered")
        return od

    def _get_io_modules(self):
        """
        Just get our I/O modules
        """
        self.parent.log.info("Parser - Getting I/O modules from L5X")
        modules = []
        for m in self.prj.modules.names:
            x = re.search("Rack[0-9]+Slot[0-9]+", m)
            if x:
                # cat_num = self.prj.modules[m].ports[1].type
                try:
                    snn = self.prj.modules[m].snn
                    snn = "safety"
                except (Exception, ):
                    snn = "standard"
                rack = int(m[4:5])
                slot = int(self.prj.modules[m].ports[1].address)
                module = Module(m, rack, slot, "None", snn)
                modules.append(module)
        self.parent.log.info("Parser - I/O modules retrieved")
        if len(modules) == 0:
            self.parent.log.info("Error:Parser - No I/O modules found")
        return modules

    def _generate_list(self, modules, addresses):
        """
        Generate a blank I/O list
        """
        self.parent.log.info("Parser - Creating the I/O list output file")
        with open("output/io_list.txt", "w") as f:
            for module in modules:
                line = "{}\n".format(module.name)
                f.write(line)
                for i in range(8):
                    tag = self._get_tag_from_alias(module, i, addresses)

                    line = "{}\t{}\n".format(i+1, tag)
                    f.write(line)
                f.write("\n")
        self.parent.log.info("Parser - I/O list created")

    def _get_tag_from_alias(self, m, p, addresses):
        """
        Find the tag name based on the rack, slot and I/O point
        """
        for address, tag in addresses.items():
            rack = None
            module_class = self._get_module_type(address)
            if module_class == "standard":
                rack = int(address[4:5])
                waste, slot, point = address.split(".")
                point = int(point)
                slot = int(slot[5:-1])
                mod_type = address.split(":")[1][:1]
            elif module_class == "safety":
                rack = int(address[4:5])
                slot = int(address.split(":")[1])
                point = address.split(".")[1]
                point = int(point[2:-4])
                mod_type = address.split(":")[2][:1]
            elif module_class == "weird":
                rack = int(address[4:5])
                slot = int(address.split(":")[1])
                point = int(address.split(".")[1])
                mod_type = address.split(":")[2][:1]

            if rack == m.rack and slot == m.slot and point == p:
                m.mod_type = mod_type
                return tag

        return "SPARE"

    def _get_module_type(self, address):
        """
        Get the module type.  This will be used to determine
        how to format the rung text
        """
        if re.search(self.standard_io, address):
            module_type = "standard"
        elif re.search(self.safety_io, address):
            module_type = "safety"           
        elif re.search(self.weird_io, address):
            module_type = "weird"
        else:
            module_type = "unknown"

        return module_type

    def _generate_rungs(self, modules):
        """
        Save formatted rung text that can be pasted into your
        logix program
        """
        txt = []
        self.parent.log.info("Parser - Generating rung text output file")
        for module in modules:
            if module.mod_class == "safety":
                branch = []
                for i in range(8):
                    m = 'Rack{}:{}:{}.Pt0{}Data'.format(module.rack, module.slot, module.mod_type, i)
                    s = 'Rack{}Slot{}.PVStatus{}.0'.format(module.rack, module.slot, i)
                    if i < 7:
                        b = 'XIC {} OTE {} NXB '.format(m, s)
                    else:
                        b = 'XIC {} OTE {} '.format(m, s)

                    branch.append(b)
                    test = ''.join(b for b in branch)
                test = "BST CM_IOStatus {} None 0 0 NXB {} BND\n".format(module.name, test)
            else:
                io_name = "Rack{}:{}.Data[{}]".format(module.rack, module.mod_type, module.slot)
                test = "CM_IOStatus {} {} 0 0\n".format(module.name, io_name)
            txt.append(test)

        # write the rung text to a file
        with open("output/rung_text.txt", "w") as f:
            for line in txt:
                f.write(line)
        self.parent.log.info("Parser - Rung text output file generated")

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
            # fn = "output/{}.txt".format(m[0])
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


class Module:

    def __init__(self, name, rack, slot, mod_type, mod_class):
        self.name = name
        self.rack = int(rack)
        self.slot = int(slot)
        self.mod_type = mod_type
        self.mod_class = mod_class
