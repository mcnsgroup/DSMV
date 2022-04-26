# DisplayRTDTemp starts a GUI for displaying the values read from the Board as a temperature time series.
#
# Requires the Arduino sketch RTD_experiment.ino loaded on the RTD-Board.
# See RTDTempGUI.py for further information. 
# 
# Lukas Freudenberg (lfreudenberg@uni-osnabrueck.de)
# Philipp Rahe (prahe@uni-osnabrueck.de)
# 26.04.2022, ver1.6
# 
# Changelog
#   - 26.04.2022: Moved enumerated file saving to DSMVLib module,
#                 shortened descriptions to fit on smaller screens,
#                 fixed a bug with the computation of the resistance for the MAX31865
#   - 25.04.2022: Added controls for all values in the precircutry of the AD7819,
#                 added functionality to save plot data as plain text,
#                 removed console output for debugging in a previous version
#   - 19.04.2022: Added support for displaying data in different units,
#                 added GUI controls for computation of the derived values,
#                 changed building of the GUI to modular function from DSMVLib,
#                 moved functions for temperature conversion into DisplayRTDTemp file
#   - 08.04.2022: Removed command line output,
#                 changed run control appearence to better reflect functionality,
#                 added version indicator in GUI,
#                 changed GUI manager to grid and optimized frame management,
#                 added support for consecutive file naming when saving,
#                 changed save label to unicode symbol,
#                 corrected axis labels,
#                 improved histogram responsiveness,
#                 added option for fixed bin size of one,
#                 added data points to time series plots
#   - 31.03.2022: Update to utilize PyPI version of the DSMVLib package
#   - 27.01.2022: Added functionality for saving plots as vector images,
#                 added indication for when the GUI isn't usable due to a disconnect
#   - 20.01.2022: Added title to the control window
#   - 19.01.2022: Minor change to keep compatibility with DSMVLib module
#   - 14.01.2022: Minor change to keep compatibility with DSMVLib module
#   - 11.01.2022: Ported to Python
#   - 03.05.2021: Initial version
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
import RTDTempGUI

#%%
# Initialize the gui
gui = RTDTempGUI.RTDTempGUI()
# %%
