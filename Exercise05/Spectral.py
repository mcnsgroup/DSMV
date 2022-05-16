# Spectral starts a GUI for the spectral analysis of the oscilloscope functionality of the DSMV board
#
# Requires the Arduino sketch DisplayDSMV.ino loaded on the Teensy 4.0.
# See SpectralGUI.py for further information. 
# 
# Lukas Freudenberg (lfreudenberg@uni-osnabrueck.de)
# Philipp Rahe (prahe@uni-osnabrueck.de)
# 16.05.2022, ver1.7
# 
# Changelog
#   - 16.05.2022: Fixed a bug that caused the wrong data to be saved,
#                 fixed a bug that caused the data tips for the spectra to break 
#                 after disabling the respective spectrum,
#                 added option to disable power integrator
#                 UI appearance changes
#   - 13.05.2022: Merged features with SpectralProcessingGUI.py,
#                 added data tip for maximum in spectrum,
#                 added entry box and switch for custom number of frequencies,
#                 added functionality to display the values of a point clicked on the plots
#                 added functionality to update entry boxes on keypad return key and focus out,
#                 decreased maximum sampling- and processingrate from 90000 to 80000Hz
#                 fixed a bug that caused the serial buffer to overflow,
#                 UI appearance changes
#   - 03.05.2022: Moved entry box processing to DSMVLib module,
#                 added version indicator in GUI
#   - 27.01.2022: Added functionality for saving plots as vector images
#   - 26.01.2022: Fixed a bug that prevented correct restoration of settings, 
#                 added indication for when the GUI isn't usable due to a disconnect or initialization
#   - 24.01.2022: Switched to fft implementation from numpy due to own
#                 implementation not performing as well as in Matlab
#                 and automated serial connection to board
#   - 20.01.2022: Ported to Python
#   - 12.05.2021: Initial version
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
import SpectralGUI

# Initialize the gui
gui = SpectralGUI.SpectralGUI()
