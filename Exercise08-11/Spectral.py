# Spectral starts a GUI for the spectral analysis of the oscilloscope functionality of the DSMV board
#
# Requires the Arduino sketch DisplayDSMVGenerate.ino loaded on the Teensy 4.0.
# See SpectralGUI.py for further information. 
# 
# Lukas Freudenberg (lfreudenberg@uni-osnabrueck.de)
# Philipp Rahe (prahe@uni-osnabrueck.de)
# 10.06.2022, ver1.18
# 
# Changelog
#   - 10.06.2022: Changed data format for saved files from .txt to .csv,
#                 added x-data to .csv files,
#                 fixed a bug that caused the data of the time series to be saved instead of that of the spectra,
#                 added keypad-return and focus-out binds to missing settings,
#                 changed modelling transfer function to complex data for high pass 1st order filter,
#                 fixed a bug that caused the spectra to be shifted by one frequency bin,
#                 fixed a bug that caused the normalization index to not be updated
#   - 09.06.2022: Changed modelling of transfer function to complex data for all filters except high pass 1st order,
#                 added missing phase models,
#                 changed color of models to green
#                 fixed a bug that caused the phase to not be updated when necessary
#   - 08.06.2022: Added functionality to display modeled frequency responses and phases
#                 fixed a bug that caused the reading to not continue after a filter settings update
#   - 07.06.2022: Added normalization option to unit list,
#                 added functionality to average impulse responses if applicable,
#                 fixed a bug that caused the spectrum to average twice
#   - 03.06.2022: Fixed a number of bugs related to power struggle between the event handlers
#   - 01.06.2022: First merger features with ImpulseResponseGUI and FilterGUI,
#                 fixed a bug that caused the updating of settings to interfere with the reading of data
#   - 31.05.2022: Fixed a bug that caused the spectral data to not be saved properly as text file
#   - 30.05.2022: Changed value displays to DSMVLib version,
#                 fixed a bug that caused the data tip to be displyed for a disabled window,
#                 changed initial legend to empty
#   - 24.05.2022: fixed a bug that prevented the data buffer to be resized correctly,
#                 fixed a bug that caused the wrong data to be saved,
#                 fixed a bug that caused the program to stop reading data if updated too frequently
#   - 23.05.2022: Fixed a bug that caused the serial buffer to overflow,
#                 added functionality to disable phases on initilizing the GUI,
#                 phase apperance change,
#                 fixed a bug that caused the serial connection to not be monitored at the beginning,
#                 fixed a bug that falsely caused the reading to start after a serial reconnect
#   - 20.05.2022: Changed data reading from board to polling
#   - 19.05.2022: Added functionality to display phases of the spectra
#   - 17.05.2022: Changed appearance of the peak annotation for the spectra
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
