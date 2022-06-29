# LockIn starts a GUI for the LockIn functionality of the DSMV board.
# 
# Requires the Arduino sketch LockIn.ino loaded on the Teensy 4.0.
# See LockInGui.py for further information.
# 
# Lukas Freudenberg (lfreudenberg@uni-osnabrueck.de)
# Philipp Rahe (prahe@uni-osnabrueck.de)
# 28.06.2022, ver1.3
# 
# Changelog:
#   - 28.06.2022: Rebuilt from SpectralGUI.py
#   - 31.03.2022: Ported to Python
#	- 07.07.2021: first version
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

# Import the GUI class
import LockInGUI

# Initialize the gui
gui = LockInGUI.LockInGUI()