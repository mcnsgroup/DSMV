# ReadRTD is a simple script to read values from the RTD board
#
# Requires the Arduino sketch RTD_experiment.ino loaded on the RTD-Board.
# 
# Lukas Freudenberg (lfreudenberg@uni-osnabrueck.de)
# Philipp Rahe (prahe@uni-osnabrueck.de)
# 01.04.2022, ver1.0.0
# 
# Changelog
#   - 01.04.2022: Initial version
# 
# Permission is hereby granted, free of charge, to any person 
# obtaining a copy of this software and associated documentation 
# files (the "Software"), to deal in the Software without 
# restriction, including without limitation the rights to use, copy,
# modify, merge, publish, distribute, sublicense, and/or sell 
# copies of the Software, and to permit persons to whom the Software 
# is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be 
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, 
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES 
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND 
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT 
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING 
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR 
# OTHER DEALINGS IN THE SOFTWARE.


# Import the serial library for python
import serial

# Print available ports on this system
import serial.tools.list_ports
ports = serial.tools.list_ports.comports()
print('Available ports:')
print('-------------------------------------------')
for port in ports:
    print(port.name)
print('-------------------------------------------')

# Configure serial port
ser = serial.Serial()
ser.port = '/dev/ttyUSB0'
ser.baudrate = 9600
ser.bytesize = serial.EIGHTBITS
ser.parity = serial.PARITY_NONE
ser.stopbits = serial.STOPBITS_ONE

# Open serial port
ser.open()
# Discard the first line, as it can be incomplete
ser.readline()
print('Connected to serial port: ' + ser.name)
print('-------------------------------------------')

print('Received data: ')
# Read N lines and print to shell
Nlines = 10
for i in range(0,Nlines):
    line = ser.readline()
    print(line)
print('-------------------------------------------')

# Close serial port
ser.close()

