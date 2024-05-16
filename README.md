# powerflex_write
Tool to write parameters to powerflex drives via the DSI port

Powerflex VFD's have a DSI port, which we can connect to using minimalmodbus and
RS485 USB adapter.  We'll take formatted flat files, get the parameter number and
value, then write each parameter to the drive.  You can quickly write many parameters
to speed up drive commissioning.  I usually use it to write only the IP Address, then
do the rest in LogixDesigner.

Create a .vfd file for each drive to write to.  The drive must start with the model number
preceded by an asterisk.  Then you list drive parameters with the following syntax:  
```
Drive Parameter:Description:Value  
```
The description is only used for information.  You can see the supplied VFD_Test.vfd file
for an example of writing the IP address.  Place the .vfd files in the output/ directory of
the project, run the gui.  The output directory doesn't exist by default, it is created when
you first start the gui.
```console
python gui.py
```
Select the com port for your USB adapter, click Write VFD Parameters.  The first file will be
read, you will get a prompt to plug into the drive.  Plug in and press Ok, the parameters will
write and you will be prompted when that drive is complete.  You will then be prompted to plug
into the next drive.  Drives that complete writing every parameter will be moved to the
completed directory.  Drives that fail will remain so that they can be corrected.

__Note:__ The "Generate VFD Files" was purpose written for our drive naming convention.  This feature will
find all I/O tree modules that start with "VFD" and generate a file with just the IP address settings
in it.  I genereally use this tool to only write the IP address settings, then I load the reset of the
parameters from Studio5000.  In the future, I may add a entery so you can specify a prefix to search for.

## Requirements
- python 3
- minimalmodbus
- l5x
- pyserial
- RS485 USB adapter
- AK-UO-RJ45-TB2P

## The cable
I picked up a RS485 adapter from Amazon, one with 2 terminals attached to the USB to make it
easier to wire up.  I used Belden 9463 (DH+ cable) to wire the USB adapter to the 2 wire
RJ45 connector.  You might tin the wires, they can get brittle over time, some heat shrink
helps too.

## Acknowledgements
* **Jonas Berg** - *minimalmodbus*  - [phys](https://github.com/pyhys)
* **jvalenzuelai** - *l5x* - [jvalenzuela](https://github.com/jvalenzuela)


