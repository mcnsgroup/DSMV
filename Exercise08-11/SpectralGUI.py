# SpectralGUI includes a GUI for the spectral analysis of the oscilloscope functionality of the DSMV board
#
# Requires the Arduino sketch DisplayDSMVGenerate.ino loaded on the Teensy 4.0.
# 
# There are two spectra being displayed,
# one for each of the selectable filter windows.
# The filter windows can be added externally with the following
# convention:
# File name:
#   Window[Name of the window].py, eg. WindowBlackman.py
# Inputs:
#   N: length of the window
# Returns:
#   window: the window as a vector
#   enbw: the enbw of the window (given by the sum of the squared
#   values divided by the square of the sum of all values)
# 
# Lukas Freudenberg (lfreudenberg@uni-osnabrueck.de)
# Philipp Rahe (prahe@uni-osnabrueck.de)
# 29.06.2022, ver1.25.1
# 
# Changelog
#   - 29.06.2022: Fixed a bug that caused a command to not be read by the board sometimes,
#                 fixed a bug that caused the arithmetic to not be set correctly
#   - 28.06.2022: Fixed a bug that caused a filter property entry box to be displayed for the IIR filter,
#                 changed normalization for filters with no index to maximum,
#                 changed y-axis label for normalized spectrum to |H(f)|
#   - 27.06.2022: Fixed a bug that caused the impulse response averaging to not reset,
#                 changed arithmetic to format of a filter property,
#                 added automatic normalization index to bandpass filter,
#                 removed normalized spectrum option for IIR filter,
#                 fixed a bug that caused the reading to not resume after a reconnect when not in spectral mode
#   - 22.06.2022: Changed visual appearance to use tabs for all controls,
#                 added functionality to respect filter window in model for FIR filters
#   - 21.06.2022: Added arithmetic options for different handlings of modulo,
#                 changed data tips for spectra to entire axis data tip,
#                 fixed a bug that caused the model state buttons to still trigger if disabled,
#                 fixed a bug that caused the model state buttons to not be disabled and enabled when appropriate,
#                 fixed a bug that caused the second spectrum to be displayed when not in spectal mode,
#                 fixed a bug that caused the filter order to accept odd numbers
#   - 20.06.2022: Fixed a bug that caused the arithmetic to not update,
#                 changed the arithmetic to combobox selector
#   - 17.06.2022: Added functionality to switch between H(z) and H(s) model for non-FIR filters,
#                 fixed a bug that caused the normalized spectrum to crash if the selected filter has no index to normalize at,
#                 optimized startup and reconnect time
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
#   - 08.06.2022: Added functionality to display modeled amplitude responses and phases
#                 fixed a bug that caused the reading to not continue after a filter settings update
#   - 07.06.2022: Added normalization option to unit list,
#                 added functionality to average impulse responses if applicable,
#                 fixed a bug that caused the spectrum to average twice,
#                 fixed a bug that caused the phase plot to not update properly
#                 added hierarchy control to all parameters
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
#   - 17.05.2022: Changed appearance of the peak annotation for the spectra,
#                 simplified code for legend assembly,
#                 added functionality to suppress DC component in spectra
#                 by subtracting average value of time series,
#                 fixed a bug that caused the spectra not to be averaged when PSD or PS were selected,
#                 fixed a bug that caused the save message to be displayed at the wrong position
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
#                 changed building of the GUI to modular function from DSMVLib,
#                 added version indicator in GUI,
#                 added functionality to save plot data as plain text,
#                 added support for consecutive file naming when saving,
#                 update to utilize PyPI version of the DSMVLib package,
#                 added vertical tkinter menu bar from DSMVLib package,
#                 changed save label to unicode symbol
#   - 27.01.2022: Added functionality for saving plots as vector images
#   - 26.01.2022: Fixed a bug that prevented correct restoration of settings, 
#                 added indication for when the GUI isn't usable due to a disconnect or initialization
#   - 24.01.2022: Switched to fft implementation from numpy due to own
#                 implementation not performing as well as in Matlab,
#                 automated serial connection to board
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

# Import official modules
import numpy as np
from matplotlib.pyplot import *
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import *
from tkinter import ttk
import struct
import time
import glob
import os
import math
# Import custom modules
from DSMVLib import DSMVLib as L

class SpectralGUI:
    # Constructor method
    def __init__(self, mode="Spectral GUI"):
        # Initialize variables defining which version of the GUI is being shown
        # Initialize all components
        # Create control window
        self.window = Tk()
        L.window = self.window
        self.window.title(mode)
        self.window.columnconfigure(1, weight=1)
        self.window.rowconfigure((1, 2), weight=1)
        # Get file path
        self.dir = os.path.relpath(__file__)
        self.dir = self.dir[0:len(self.dir)-14]
        # Initialize the port for the Board
        self.port = 0
        try:
            self.port = L.sPort()
        except L.SerialDisconnect:
            quit()
        self.disconnected = False
        self.readNext = False
        self.samplerateDefault = 1000.0
        self.samplerate = self.samplerateDefault
        self.dataSizeDefault = 100
        self.dataSize = self.dataSizeDefault
        self.oversamplesDefault = 1
        self.oversamples = self.oversamplesDefault
        self.procDefault = 20000.0
        self.transformSize1 = math.floor(self.dataSizeDefault / 2)
        self.transformSize2 = math.floor(self.dataSizeDefault / 2)
        self.proc = self.procDefault
        self.port.clearBuffer()
        self.readNext = True
        # Initialize data buffer
        self.data = [0] * self.dataSize
        # List with all UI elements
        self.uiElements = []
        # List with the grid parameters of all UI elements
        self.uiGridParams = []
        # create label for version number
        self.vLabel = Label(master=self.window, text="DSMV\nEx. 05-11\nv1.25.1")
        self.uiElements.append(self.vLabel)
        self.uiGridParams.append([0, 0, 1, 1, "NS"])
        # create frame for controls
        self.controlFrame = Frame()
        self.uiElements.append(self.controlFrame)
        self.uiGridParams.append([0, 1, 1, 2, "WE"])
        self.controlFrame.columnconfigure((0, 1), weight=1)
        # create frame for the board settings
        self.boardFrame = Frame(master=self.controlFrame, relief=RIDGE, borderwidth=2)
        self.uiElements.append(self.boardFrame)
        self.uiGridParams.append([0, 0, 1, 1, "NESW"])
        self.boardFrame.rowconfigure(1, weight=1)
        self.boardFrame.columnconfigure(0, weight=1)
        # Create Label for board settings
        self.boardLabel = Label(master=self.boardFrame, text="Acquisition and Processing")
        self.uiElements.append(self.boardLabel)
        self.uiGridParams.append([0, 0, 1, 1, ""])
        # Create frame for the individual labels and entry boxes
        self.boardSFrame = Frame(master=self.boardFrame, relief=RIDGE, borderwidth=2)
        self.uiElements.append(self.boardSFrame)
        self.uiGridParams.append([1, 0, 1, 1, "NESW"])
        self.boardSFrame.columnconfigure(1, weight=1)
        # Initialize operation mode
        self.mode = "AD4020 spectral analysis"
        self.spectral = True
        # Create label for the operation mode selector
        self.modeLabel = Label(master=self.boardSFrame, text="Operation Mode")
        self.uiElements.append(self.modeLabel)
        self.uiGridParams.append([0, 0, 1, 1, "E"])
        # List of different operation modes
        modeList = ["AD4020 spectral analysis", "LTC2500 spectral analysis", "Internal ADC spectral analysis", "Pulse response & signal processing", 
                    "Step up response & signal processing", "Step down response & signal processing"]
        # Create combo box for operation mode selector
        self.modeSelect = ttk.Combobox(master=self.boardSFrame, values = modeList, state="readonly")
        self.uiElements.append(self.modeSelect)
        self.uiGridParams.append([0, 1, 1, 1, "WE"])
        self.modeSelect.bind('<<ComboboxSelected>>', self.handle_updateMode)
        self.modeSelect.set(modeList[0])
        # Create label for the samplerate entry box
        self.freqLabel = Label(master=self.boardSFrame, text="f_s (Hz)")
        self.uiElements.append(self.freqLabel)
        self.uiGridParams.append([1, 0, 1, 1, "E"])
        # Variable to control content of the samplerate entry box
        self.samplerateV = StringVar()
        self.samplerateV.set(str(self.samplerate))
        # Create samplerate entry box
        self.freqEntry = Entry(master=self.boardSFrame, textvariable=self.samplerateV, justify=RIGHT)
        self.uiElements.append(self.freqEntry)
        self.uiGridParams.append([1, 1, 1, 1, "WE"])
        self.freqEntry.bind("<Return>", self.handle_updateFreq)
        self.freqEntry.bind("<KP_Enter>", self.handle_updateFreq)
        self.freqEntry.bind("<FocusOut>", self.handle_updateFreq)
        # Minimum samplerate
        self.samplerateMin = 1
        # Maximum samplerate
        self.samplerateMax = 80000
        # Create label for the data size entry box
        self.sizeLabel = Label(master=self.boardSFrame, text="N")
        self.uiElements.append(self.sizeLabel)
        self.uiGridParams.append([2, 0, 1, 1, "E"])
        # Variable to control content of the data size entry box
        self.dataSizeV = StringVar()
        self.dataSizeV.set(str(self.dataSize))
        # Create data size entry box
        self.sizeEntry = Entry(master=self.boardSFrame, textvariable=self.dataSizeV, justify=RIGHT)
        self.uiElements.append(self.sizeEntry)
        self.uiGridParams.append([2, 1, 1, 1, "WE"])
        self.sizeEntry.bind("<Return>", self.handle_updateSize)
        self.sizeEntry.bind("<KP_Enter>", self.handle_updateSize)
        self.sizeEntry.bind("<FocusOut>", self.handle_updateSize)
        # Minimum data size
        self.dataSizeMin = 1
        # Maximum data size
        self.dataSizeMax = 32768
        # Create label for the oversamples entry box
        self.oversLabel = Label(master=self.boardSFrame, text="N_o")
        self.uiElements.append(self.oversLabel)
        self.uiGridParams.append([3, 0, 1, 1, "E"])
        # Variable to control content of the oversamples entry box
        self.oversamplesV = StringVar()
        self.oversamplesV.set(str(self.oversamples))
        # Create oversamples entry box
        self.oversEntry = Entry(master=self.boardSFrame, textvariable=self.oversamplesV, justify=RIGHT)
        self.uiElements.append(self.oversEntry)
        self.uiGridParams.append([3, 1, 1, 1, "WE"])
        self.oversEntry.bind("<Return>", self.handle_updateOvers)
        self.oversEntry.bind("<KP_Enter>", self.handle_updateOvers)
        self.oversEntry.bind("<FocusOut>", self.handle_updateOvers)
        # Minimum oversamples
        self.oversMin = 1
        # Maximum oversamples
        self.oversMax = 65536
        # Create label for the processing rate entry box
        self.procLabel = Label(master=self.boardSFrame, text="f_p (Hz)")
        self.uiElements.append(self.procLabel)
        self.uiGridParams.append([4, 0, 1, 1, "E"])
        # Variable to control content of the processing rate entry box
        self.procV = StringVar()
        self.procV.set(str(self.proc))
        # Create samplerate entry box
        self.procEntry = Entry(master=self.boardSFrame, textvariable=self.procV, justify=RIGHT)
        self.uiElements.append(self.procEntry)
        self.uiGridParams.append([4, 1, 1, 1, "WE"])
        self.procEntry.bind("<Return>", self.handle_updateProc)
        self.procEntry.bind("<KP_Enter>", self.handle_updateProc)
        self.procEntry.bind("<FocusOut>", self.handle_updateProc)
        # Minimum processing frequency
        self.procMin = 1
        # Maximum processing frequency
        self.procMax = 80000
        self.tabsystem = ttk.Notebook(self.controlFrame)
        self.uiElements.append(self.tabsystem)
        self.uiGridParams.append([0, 1, 1, 1, "NESW"])
        # Create frame for the display settings
        self.displayFrame = Frame(master=self.tabsystem)
        self.tabsystem.add(self.displayFrame, text='Display settings')
        self.displayFrame.columnconfigure((2, 3), weight=1)
        # Number of averaged spectra
        self.averaged = 1
        # Initialize averaging state
        self.averaging = BooleanVar()
        self.averaging.set(False)
        # Create label for the averaging selector
        self.averagingLabel = Label(master=self.displayFrame, text="Spectrum")
        self.uiElements.append(self.averagingLabel)
        self.uiGridParams.append([0, 0, 1, 2, "E"])
        # Create frame for the averaging selector and spectral unit
        self.avgUnitFrame = Frame(master=self.displayFrame)
        self.uiElements.append(self.avgUnitFrame)
        self.uiGridParams.append([0, 2, 1, 3, "NESW"])
        self.avgUnitFrame.columnconfigure(3, weight=1)
        # Create averaging selector buttons
        self.singleButton = Radiobutton(self.avgUnitFrame, text="Single", variable = self.averaging, value = False)
        self.uiElements.append(self.singleButton)
        self.uiGridParams.append([0, 0, 1, 1, "E"])
        self.averagedButton = Radiobutton(self.avgUnitFrame, text="Averaged", variable = self.averaging, value = True)
        self.uiElements.append(self.averagedButton)
        self.uiGridParams.append([0, 1, 1, 1, "W"])
        # Possible spectrum unit labels
        self.psdLabel = "$\mathrm{PSD\/ D}^\mathrm{V}\mathrm{\/(V}^2\mathrm{/Hz)}$"
        self.psLabel = "$\mathrm{PS\/ S}^\mathrm{V}\mathrm{\/(V}^2\mathrm{)}$"
        self.asdLabel = "$\mathrm{ASD\/ d}^\mathrm{V}\mathrm{\/(V}^2\mathrm{/}\sqrt{\mathrm{Hz}}\mathrm{)}$"
        self.asLabel = "$\mathrm{AS\/ s}^\mathrm{V}\mathrm{\/(V)}$"
        self.normLabel = "|H(f)| (normalized)"
        # List of different spectrum unit labels
        self.unitLabels = [self.psdLabel, self.psLabel, self.asdLabel, self.asLabel, self.normLabel]
        # List of different spectrum units
        self.unitList = ["Power Spectral Density", "Power Spectrum", "Amplitude Spectral Density", "Amplitude Spectrum", "Normalized Spectrum"]
        # Create combo box for spectrum unit selector
        self.unitSelect = ttk.Combobox(master=self.avgUnitFrame, values=self.unitList, state="readonly")
        self.uiElements.append(self.unitSelect)
        self.uiGridParams.append([0, 3, 1, 1, "WE"])
        self.unitSelect.bind('<<ComboboxSelected>>', self.handle_updateUnit)
        self.unitSelect.set(self.unitList[0])
        # Initialize y-scale state
        self.yscale = StringVar()
        self.yscale.set("Logarithmic")
        # Create label for the y-scale selector
        self.yscaleLabel = Label(master=self.displayFrame, text="Y-scale (Spectrum)")
        self.uiElements.append(self.yscaleLabel)
        self.uiGridParams.append([1, 0, 1, 2, "E"])
        # Create frame for the y-scale selector
        self.scaleFrame = Frame(master=self.displayFrame)
        self.uiElements.append(self.scaleFrame)
        self.uiGridParams.append([1, 2, 1, 2, "NESW"])
        # Create y-scale selector buttons
        self.logButton = Radiobutton(self.scaleFrame, text="Logarithmic", variable = self.yscale, value = "Logarithmic")
        self.uiElements.append(self.logButton)
        self.uiGridParams.append([0, 0, 1, 1, "E"])
        self.logButton.bind("<Button-1>", self.handle_logScale)
        self.linButton = Radiobutton(self.scaleFrame, text="Linear", variable = self.yscale, value = "Linear")
        self.uiElements.append(self.linButton)
        self.uiGridParams.append([0, 1, 1, 1, "W"])
        self.linButton.bind("<Button-1>", self.handle_linScale)
        # Create label for the window selectors
        self.windowLabel = Label(master=self.displayFrame, text="Windows")
        self.uiElements.append(self.windowLabel)
        self.uiGridParams.append([2, 0, 1, 2, "E"])
        # Create list of available window functions
        pathFiles=sorted(glob.glob(self.dir + "Window*.py"))
        self.windowFiles = [os.path.basename(f) for f in pathFiles]
        for f in self.windowFiles:
            exec("import " + f[0:len(f)-3])
        self.windows = [wf[6:len(wf)-3] for wf in self.windowFiles]
        # Add the disabled option
        self.windows += ["Disabled"]
        func = self.windowFiles[0]
        self.winFunc1 = func[0:len(func)-3] + "." + func[0:len(func)-3]
        self.winFunc2 = func[0:len(func)-3] + "." + func[0:len(func)-3]
        # Variables for the current windows
        self.window1 = StringVar()
        self.window2 = StringVar()
        self.window1.set(self.windows[0])
        self.window2.set("Disabled")
        # Create combo box for window selector 1
        self.windowSelect1 = ttk.Combobox(master=self.displayFrame, values = self.windows, textvariable=self.window1, state="readonly")
        self.uiElements.append(self.windowSelect1)
        self.uiGridParams.append([2, 2, 1, 1, "WE"])
        self.windowSelect1.bind('<<ComboboxSelected>>', self.handle_updateWindow1)
        # Create combo box for window selector 2
        self.windowSelect2 = ttk.Combobox(master=self.displayFrame, values = self.windows, textvariable=self.window2, state="readonly")
        self.uiElements.append(self.windowSelect2)
        self.uiGridParams.append([2, 3, 1, 1, "WE"])
        self.windowSelect2.bind('<<ComboboxSelected>>', self.handle_updateWindow2)
        # Initialize subtraction state
        self.subtract = StringVar()
        self.subtract.set("Disabled")
        # Create label for the subtraction selector
        self.subtractLabel = Label(master=self.displayFrame, text="Subtract average")
        self.uiElements.append(self.subtractLabel)
        self.uiGridParams.append([3, 0, 1, 2, "E"])
        # Create frame for the subtraction selector
        self.subtractFrame = Frame(master=self.displayFrame)
        self.uiElements.append(self.subtractFrame)
        self.uiGridParams.append([3, 2, 1, 2, "NESW"])
        # Create subtraction selector buttons
        self.subDisButton = Radiobutton(self.subtractFrame, text="Disabled", variable = self.subtract, value = "Disabled")
        self.uiElements.append(self.subDisButton)
        self.uiGridParams.append([0, 0, 1, 1, "E"])
        self.subDisButton.bind("<Button-1>", self.handle_subDis)
        self.subEnButton = Radiobutton(self.subtractFrame, text="Enabled", variable = self.subtract, value = "Enabled")
        self.uiElements.append(self.subEnButton)
        self.uiGridParams.append([0, 1, 1, 1, "W"])
        self.subEnButton.bind("<Button-1>", self.handle_subEn)
        # Initialize transform size status state
        self.transformSizeStatus = StringVar()
        self.transformSizeStatus.set("N_FT-1=N/2")
        # Create transform size status selector buttons
        self.NButton = Radiobutton(self.displayFrame, text="N_FT-1=N/2", variable = self.transformSizeStatus, value = "N_FT-1=N/2")
        self.uiElements.append(self.NButton)
        self.uiGridParams.append([4, 0, 1, 1, "W"])
        self.NButton.bind("<Button-1>", self.handle_lockedTransform)
        self.N_FTButton = Radiobutton(self.displayFrame, text="N_FT-1", variable = self.transformSizeStatus, value = "N_FT-1")
        self.uiElements.append(self.N_FTButton)
        self.uiGridParams.append([4, 1, 1, 1, "E"])
        self.N_FTButton.bind("<Button-1>", self.handle_customTransform)
        # Variable to control content of the transform size 1 entry box
        self.transformSize1V = StringVar()
        self.transformSize1V.set(str(self.transformSize1))
        # Variable to control content of the transform size 2 entry box
        self.transformSize2V = StringVar()
        self.transformSize2V.set(str(self.transformSize2))
        # Create transform size 1 entry box
        self.transformSize1Entry = Entry(master=self.displayFrame, textvariable=self.transformSize1V, justify=RIGHT)
        self.uiElements.append(self.transformSize1Entry)
        self.uiGridParams.append([4, 2, 1, 1, "WE"])
        self.transformSize1Entry.bind("<Return>", self.handle_updateTransformSize1)
        self.transformSize1Entry.bind("<KP_Enter>", self.handle_updateTransformSize1)
        self.transformSize1Entry.bind("<FocusOut>", self.handle_updateTransformSize1)
        self.transformSize1Entry["state"] = DISABLED
        # Create transform size 2 entry box
        self.transformSize2Entry = Entry(master=self.displayFrame, textvariable=self.transformSize2V, justify=RIGHT)
        self.uiElements.append(self.transformSize2Entry)
        self.uiGridParams.append([4, 3, 1, 1, "WE"])
        self.transformSize2Entry.bind("<Return>", self.handle_updateTransformSize2)
        self.transformSize2Entry.bind("<KP_Enter>", self.handle_updateTransformSize2)
        self.transformSize2Entry.bind("<FocusOut>", self.handle_updateTransformSize2)
        self.transformSize2Entry["state"] = DISABLED
        # Minimum transform size
        self.transformSizeMin = 1
        # Maximum transform size
        self.transformSizeMax = 16384
        # Value for phase state
        self.phaseState = "Disabled"
        # Strinng variable for phase state
        self.phaseStateV = StringVar()
        self.phaseStateV.set(self.phaseState)
        # Create label for the phase selector
        self.showPhaseLabel = Label(master=self.displayFrame, text="Show phase")
        self.uiElements.append(self.showPhaseLabel)
        self.uiGridParams.append([5, 0, 1, 2, "E"])
        # Create frame for the phase selector
        self.phaseFrame = Frame(master=self.displayFrame)
        self.uiElements.append(self.phaseFrame)
        self.uiGridParams.append([5, 2, 1, 2, "NESW"])
        # Create phase selector buttons
        self.phaseDisButton = Radiobutton(self.phaseFrame, text="Disabled", variable = self.phaseStateV, value = "Disabled")
        self.uiElements.append(self.phaseDisButton)
        self.uiGridParams.append([0, 0, 1, 1, "E"])
        self.phaseDisButton.bind("<Button-1>", self.handle_phaseDis)
        self.phaseEnButton = Radiobutton(self.phaseFrame, text="Enabled", variable = self.phaseStateV, value = "Enabled")
        self.uiElements.append(self.phaseEnButton)
        self.uiGridParams.append([0, 1, 1, 1, "W"])
        self.phaseEnButton.bind("<Button-1>", self.handle_phaseEn)
        # Create frame for the filter settings
        self.filterFrame = Frame(master=self.tabsystem)
        self.tabsystem.add(self.filterFrame, text='Filter settings')
        #self.uiElements.append(self.filterFrame)
        #self.uiGridParams.append([0, 1, 1, 1, "NESW"])
        self.filterFrame.columnconfigure((1, 3), weight=1)
        # Create frame for the individual widgets
        # Create label for the signal filter selector
        self.filterSelectLabel = Label(master=self.filterFrame, text="Signal Filter")
        self.uiElements.append(self.filterSelectLabel)
        self.uiGridParams.append([0, 0, 1, 1, "E"])
        # List of different signal filters
        self.filters = ["Scaling", "Moving average", "Low pass filter 1st order", "High pass filter 1st order",
                        "FIR bandpass filter", "FIR bandstop filter", "FIR low pass filter", "FIR high pass filter",
                        "Low pass filter 2nd order", "Low pass filter 3rd order", "Programmable IIR filter"]
        # Create combo box for filter selector
        self.filterSelect = ttk.Combobox(master=self.filterFrame, values = self.filters, state="readonly")
        self.uiElements.append(self.filterSelect)
        self.uiGridParams.append([0, 1, 1, 3, "WE"])
        self.filterSelect.bind("<<ComboboxSelected>>", self.handle_updateFilter)
        self.filterDefault = "Scaling"
        filterDefIndex = self.filters.index(self.filterDefault)
        self.filterIndex = filterDefIndex
        self.filterSelect.set(self.filters[filterDefIndex])
        # Names for the filter property 1
        self.prop1Names = ["Gain", "Number of samples", "Cutoff frequency", "Cutoff frequency", "Lower frequency",
                           "Lower frequency", "Cutoff frequency", "Cutoff frequency", "Cutoff frequency", "Cutoff frequency", ""]
        # Visibility of filter property 1
        self.prop1Visible = [True, True, True, True, True, True, True, True, True, True, False]
        # Create label for the filter property 1 entry box
        self.prop1Label = Label(master=self.filterFrame, text=self.prop1Names[filterDefIndex])
        self.uiElements.append(self.prop1Label)
        self.uiGridParams.append([1, 0, 1, 1, "E"])
        # Value type for the filter property 1
        self.prop1Type = ["Float", "Integer", "Float", "Float", "Float", "Float", "Float", "Float", "Float", "Float", ""]
        # Default values for the filter property 1 (later current values)
        self.prop1Value = [1.0, 1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, None]
        # Minimum values for the filter property 1
        self.prop1Min = [-np.inf, 1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, None]
        # Maximum values for the filter property 1
        self.prop1Max = [np.inf, 256, np.inf, np.inf, np.inf, np.inf, np.inf, np.inf, np.inf, np.inf, None]
        # Variable to control content of the filter property 1 entry box
        self.prop1V = StringVar()
        self.prop1V.set(str(self.prop1Value[filterDefIndex]))
        # Create filter property 1 entry box
        self.prop1Entry = Entry(master=self.filterFrame, textvariable=self.prop1V, justify=RIGHT)
        self.uiElements.append(self.prop1Entry)
        self.uiGridParams.append([1, 1, 1, 1, "WE"])
        self.prop1Entry.bind("<Return>", self.handle_updateProp1)
        self.prop1Entry.bind("<KP_Enter>", self.handle_updateProp1)
        self.prop1Entry.bind("<FocusOut>", self.handle_updateProp1)
        # Names for the filter property 2
        self.prop2Names = ["", "", "", "", "Upper frequency", "Upper frequency", "", "", "", "", ""]
        # Visibility of filter property 2
        self.prop2Visible = [False, False, False, False, True, True, False, False, False, False, False]
        # Create label for the filter property 2 entry box
        self.prop2Label = Label(master=self.filterFrame, text=self.prop2Names[filterDefIndex])
        self.uiElements.append(self.prop2Label)
        self.uiGridParams.append([2, 0, 1, 1, "E"])
        # Value type for the filter property 2
        self.prop2Type = ["", "", "", "", "Float", "Float", "", "", "", "", ""]
        # Default values for the filter property 2 (later current values)
        self.prop2Value = [None, None, None, None, 0.0, 0.0, None, None, None, None, None]
        # Minimum values for the filter property 1
        self.prop2Min = [None, None, None, None, 0.0, 0.0, None, None, None, None, None]
        # Maximum values for the filter property 1
        self.prop2Max = [None, None, None, None, np.inf, np.inf, None, None, None, None, None]
        # Variable to control content of the filter property 2 entry box
        self.prop2V = StringVar()
        self.prop2V.set(str(self.prop2Value[self.filters.index(self.filterDefault)]))
        # Create filter property 2 entry box
        self.prop2Entry = Entry(master=self.filterFrame, textvariable=self.prop2V, justify=RIGHT)
        self.uiElements.append(self.prop2Entry)
        self.uiGridParams.append([2, 1, 1, 1, "WE"])
        self.prop2Entry.bind("<Return>", self.handle_updateProp2)
        self.prop2Entry.bind("<KP_Enter>", self.handle_updateProp2)
        self.prop2Entry.bind("<FocusOut>", self.handle_updateProp2)
		# Names for the filter property 3
        self.prop3Names = ["", "", "", "", "Filter order", "Filter order", "Filter order", "Filter order", "", "", ""]
        # Visibility of filter property 3
        self.prop3Visible = [False, False, False, False, True, True, True, True, False, False, False]
        # Create label for the filter property 3 entry box
        self.prop3Label = Label(master=self.filterFrame, text=self.prop3Names[filterDefIndex])
        self.uiElements.append(self.prop3Label)
        self.uiGridParams.append([3, 0, 1, 1, "E"])
        # Value type for the filter property 3
        self.prop3Type = ["", "", "", "", "Integer", "Integer", "Integer", "Integer", "", "", ""]
        # Default values for the filter property 3 (later current values)
        self.prop3Value = [None, None, None, None, 2, 2, 2, 2, None, None, None]
        # Minimum values for the filter property 3
        self.prop3Min = [None, None, None, None, 2, 2, 2, 2, None, None, None]
        # Maximum values for the filter property 3
        self.prop3Max = [None, None, None, None, 140, 140, 140, 140, None, None, None]
        # Variable to control content of the filter property 3 entry box
        self.prop3V = StringVar()
        self.prop3V.set(str(self.prop3Value[filterDefIndex]))
        # Create filter property 3 entry box
        self.prop3Entry = Entry(master=self.filterFrame, textvariable=self.prop3V, justify=RIGHT)
        self.uiElements.append(self.prop3Entry)
        self.uiGridParams.append([3, 1, 1, 1, "WE"])
        self.prop3Entry.bind("<Return>", self.handle_updateProp3)
        self.prop3Entry.bind("<KP_Enter>", self.handle_updateProp3)
        self.prop3Entry.bind("<FocusOut>", self.handle_updateProp3)
        # Names for the filter property 4
        self.prop4Names = ["", "", "", "", "Filter Window", "Filter Window", "Filter Window", "Filter Window", "", "", ""]
        # Visibility of filter property 4
        self.prop4Visible = [False, False, False, False, True, True, True, True, False, False, False]
        # Create label for the filter property 4 combo box
        self.prop4Label = Label(master=self.filterFrame, text=self.prop4Names[filterDefIndex])
        self.uiElements.append(self.prop4Label)
        self.uiGridParams.append([4, 0, 1, 1, "E"])
        # Value type for the filter property 4
        self.prop4Type = ["", "", "", "", "String", "String", "String", "String", "", "", ""]
        # Default values for the filter property 4 (later current values)
        self.prop4Value = [None, None, None, None, "Rectangle", "Rectangle", "Rectangle", "Rectangle", None, None, None]
        # Minimum values for the filter property 4
        self.prop4Min = [None, None, None, None, None, None, None, None, None, None, None]
        # Maximum values for the filter property 4
        self.prop4Max = [None, None, None, None, None, None, None, None, None, None, None]
        # Variable to control content of the filter property 4 entry box
        self.prop4V = StringVar()
        self.prop4V.set(str(self.prop4Value[filterDefIndex]))
        # List of different window functions
        self.windows = ["Rectangle", "Hamming"]
        # Create combo box for window selector
        self.windowSelect = ttk.Combobox(master=self.filterFrame, values = self.windows, state="readonly")
        self.uiElements.append(self.windowSelect)
        self.uiGridParams.append([4, 1, 1, 1, "WE"])
        self.windowSelect.bind("<<ComboboxSelected>>", self.handle_updateWindow)
        self.windowSelect.set(str(self.prop4Value[self.filterIndex]))
        
        
        # Names for the filter property 5
        self.prop5Names = ["", "", "", "", "Arithmetic", "Arithmetic", "Arithmetic", "Arithmetic", "", "", ""]
        # Visibility of filter property 5
        self.prop5Visible = [False, False, False, False, True, True, True, True, False, False, False]
        # Create label for the filter property 5 combo box
        self.prop5Label = Label(master=self.filterFrame, text=self.prop5Names[filterDefIndex])
        self.uiElements.append(self.prop5Label)
        self.uiGridParams.append([5, 0, 1, 1, "E"])
        # Value type for the filter property 5
        self.prop5Type = ["", "", "", "", "String", "String", "String", "String", "", "", ""]
        # Default values for the filter property 5 (later current values)
        self.prop5Value = [None, None, None, None, "Integer double buffer", "Integer double buffer", "Integer double buffer", "Integer double buffer", None, None, None]
        # Minimum values for the filter property 5
        self.prop5Min = [None, None, None, None, None, None, None, None, None, None, None]
        # Maximum values for the filter property 5
        self.prop5Max = [None, None, None, None, None, None, None, None, None, None, None]
        # Variable to control content of the filter property 5 entry box
        self.prop5V = StringVar()
        self.prop5V.set(str(self.prop5Value[filterDefIndex]))
        # Values for arithmetic
        self.arithmetics = ["Integer double buffer", "Integer if modulo", "Integer modulo", "Float double buffer", "Float if modulo", "Float modulo"]
        # Create combo box for arithmetic selector
        self.arithmeticSelect = ttk.Combobox(master=self.filterFrame, values = self.arithmetics, state="readonly")
        self.uiElements.append(self.arithmeticSelect)
        self.uiGridParams.append([5, 1, 1, 1, "WE"])
        self.arithmeticSelect.bind("<<ComboboxSelected>>", self.handle_updateArithmetic)
        self.arithmeticSelect.set(str(self.prop5Value[self.filterIndex]))
        # Value for model state
        self.modelState = "Disabled"
        # String variable for model state
        self.modelStateV = StringVar()
        self.modelStateV.set(self.modelState)
        # Create label for the model selector
        self.modelLabel = Label(master=self.filterFrame, text="Model")
        self.uiElements.append(self.modelLabel)
        self.uiGridParams.append([1, 2, 1, 1, "E"])
        # Create frame for the model selector
        self.modelFrame = Frame(master=self.filterFrame)
        self.uiElements.append(self.modelFrame)
        self.uiGridParams.append([1, 2, 1, 1, "NESW"])
        # Create model selector buttons
        self.modelDisButton = Radiobutton(self.modelFrame, text="Disabled", variable = self.modelStateV, value="Disabled")
        self.uiElements.append(self.modelDisButton)
        self.uiGridParams.append([0, 0, 1, 1, "E"])
        self.modelDisButton.bind("<Button-1>", self.handle_modelDis)
        self.modelHzButton = Radiobutton(self.modelFrame, text="H(z)", variable = self.modelStateV, value="H(z)")
        self.uiElements.append(self.modelHzButton)
        self.uiGridParams.append([0, 1, 1, 1, "W"])
        self.modelHzButton.bind("<Button-1>", self.handle_modelHz)
        self.modelHsButton = Radiobutton(self.modelFrame, text="H(s)", variable = self.modelStateV, value="H(s)")
        self.uiElements.append(self.modelHsButton)
        self.uiGridParams.append([0, 2, 1, 1, "W"])
        self.modelHsButton.bind("<Button-1>", self.handle_modelHs)
        # Array to store wether there is a H(z) to display for the respective filter
        self.hzEnabled = [True, True, True, True, True, True, True, True, True, True, False]
        # Array to store wether there is a H(s) to display for the respective filter
        self.hsEnabled = [True, True, True, True, False, False, False, False, True, True, False]
        # create frame for the run control
        self.runFrame = Frame(master=self.controlFrame, relief=RIDGE, borderwidth=2)
        self.uiElements.append(self.runFrame)
        self.uiGridParams.append([0, 2, 1, 1, "NESW"])
        self.runFrame.rowconfigure(1, weight=1)
        # Create Label for run control
        self.runLabel = Label(master=self.runFrame, text="Run control")
        self.uiElements.append(self.runLabel)
        self.uiGridParams.append([0, 0, 1, 1, ""])
        # Create frame for the actual widgets
        self.runSFrame = Frame(master=self.runFrame, relief=RIDGE, borderwidth=2)
        self.uiElements.append(self.runSFrame)
        self.uiGridParams.append([1, 0, 1, 1, "NESW"])
        self.runSFrame.rowconfigure(1, weight=1)
        # Create label for the reading status
        self.readLabel = Label(master=self.runSFrame, text="Paused")
        self.uiElements.append(self.readLabel)
        self.uiGridParams.append([0, 0, 1, 1, ""])
        # Create read switch
        self.readSwitch = Button(master=self.runSFrame, text="Run                ")
        self.uiElements.append(self.readSwitch)
        self.uiGridParams.append([0, 1, 1, 1, ""])
        self.readSwitch.bind("<Button-1>", self.handle_switchRead)
        # Status variable controlling the reading of data
        self.reading = False
        # Status variable for handling restarting the reading of data
        self.reactivate = True
        # Create stop button
        self.stopButton = Button(master=self.runSFrame, text="Quit Program", fg="black", bg="red")
        self.uiElements.append(self.stopButton)
        self.uiGridParams.append([1, 0, 1, 2, "NESW"])
        self.stopButton.bind("<Button-1>", self.stop)
        # Create canvas for the time series
        self.fig1 = Figure(figsize=(5, 2), layout='constrained')
        # Maximum time value
        tMax = (self.dataSize-1)*self.oversamples/self.samplerate
        # Create values for time axis
        self.x = np.linspace(0, tMax, self.dataSize)
        # Create array to hold current impulse response (pre averaging)
        self.voltagePre = self.data
        self.ax1 = self.fig1.add_subplot(111)
        self.ax1.set_xlabel("Time (s)")
        self.ax1.set_ylabel("Voltage AD4020 (V)")
        # Set time axis limits to match data
        self.ax1.set_xlim([0, tMax])
        self.voltage, = self.ax1.plot(self.x, self.voltagePre, 'b.-', label="Impulse response", linewidth=0.5)
        # Legend for time series
        self.legendImpulse = self.ax1.legend(loc="upper right", title="Averaged impulse responses: 1")
        self.legendImpulse.set_visible(False)
        # Create the canvas
        canvas1 = FigureCanvasTkAgg(self.fig1)
        canvas1.draw()
        self.uiElements.append(canvas1.get_tk_widget())
        self.uiGridParams.append([1, 0, 1, 2, "NESW"])
        # Create data tip for the voltage
        self.dataTipVoltage = L.dataTip(canvas1, self.ax1, 0.01, self.voltage, "b")
        # Create frame for saving the plot
        self.saveFrame1 = Frame()
        self.uiElements.append(self.saveFrame1)
        self.uiGridParams.append([1, 2, 1, 1, "NS"])
        # Create save button
        self.saveButton1 = Button(master=self.saveFrame1, text=u"\U0001F4BE", font=("TkDefaultFont", 60))
        self.uiElements.append(self.saveButton1)
        self.uiGridParams.append([0, 0, 1, 1, ""])
        # Create label to display saved message
        self.saveLabel1 = Label(master=self.saveFrame1)
        self.uiElements.append(self.saveLabel1)
        self.uiGridParams.append([1, 0, 1, 1, ""])
        def updateSaveLabel1(event):
            path = L.savePath("Time Series", self.dir)
            # save the image
            self.fig1.savefig(path + ".svg")
            # save the data as csv file
            L.saveFigCSV(self.fig1, path)
            # display the saved message
            self.saveLabel1.configure(text="Saved as " + path + "!")
            # schedule message removal
            self.window.after(2000, lambda: self.saveLabel1.configure(text=""))
        self.saveButton1.bind("<Button-1>", updateSaveLabel1)
        toolbar1 = L.VerticalPlotToolbar(canvas1, self.saveFrame1)
        toolbar1.update()
        toolbar1.pack_forget()
        self.uiElements.append(toolbar1)
        self.uiGridParams.append([2, 0, 1, 1, "NW"])
        # Create canvas for the spectra
        self.fig2 = Figure(figsize=(5, 2), layout='constrained')
        # Maximum frequency value
        fMax = self.samplerate/(2 * self.oversamples)
        # Number of frequencies
        self.freqs1 = int(np.ceil((self.dataSize+1)/2))
        self.freqs2 = int(np.ceil((self.dataSize+1)/2))
        # Default indices of the amplitude response to norm on
        self.normIndexDefault = [0, 0, 0, self.freqs1-2, -1, 0, 0, self.freqs1-2, 0, 0, None]
        # Index of the amplitude response to norm on
        self.normIndex = self.normIndexDefault
        # Create values for frequency axis
        self.f1 = np.linspace(0, fMax, self.freqs1)
        self.f2 = np.linspace(0, fMax, self.freqs2)
        # Possibly omit zero frequency
        if not self.spectral:
            self.f1 = self.f1[1:len(self.f1)]
            self.f2 = self.f2[1:len(self.f2)]
        self.ax2 = self.fig2.add_subplot(111)
        self.ax2.set_xlabel("Frequency (Hz)")
        self.ax2.set_ylabel(self.psdLabel)
        # Set frequency axis limits to match data
        self.ax2.set_xlim([0, fMax])
        # Create arrays to hold current spectra (pre scaling and averaging)
        self.S1Pre = [0] * self.freqs1
        self.S2Pre = [0] * self.freqs2
        # Possibly omit zero frequency
        if not self.spectral:
            self.S1Pre = self.S1Pre[1:len(self.S1Pre)]
            self.S2Pre = self.S2Pre[1:len(self.S2Pre)]
        # ENBWs of the current spectra
        self.enbw1 = 0
        self.enbw2 = 0
        # Create spectra
        self.spectrum1, = self.ax2.plot(self.f1, self.S1Pre, 'b.-', label=self.windows[0] + " window, ENBW: 0Hz", linewidth=0.5)
        self.spectrum2, = self.ax2.plot(self.f2, self.S2Pre, 'r.-', label=self.windows[0] + " window, ENBW: 0Hz", linewidth=0.5)
        # Create data tips for the spectra's respective maximum
        self.maxAnnotation1 = self.ax2.annotate("Peak\nf: " + L.fstr(0, 5) + "\ny: " + L.fstr(0, 5), 
		    xy=(0, 0), xytext=(-50, 15),
		    textcoords='offset points',
		    bbox=dict(alpha=0.5, fc="b"),
		    arrowprops=dict(arrowstyle='->')
		)
        self.maxAnnotation1.set_visible(False)
        self.maxAnnotation2 = self.ax2.annotate("Peak\nf: " + L.fstr(0, 5) + "\ny: " + L.fstr(0, 5), 
		    xy=(0, 0), xytext=(10, 15),
		    textcoords='offset points',
		    bbox=dict(alpha=0.5, fc="b"),
		    arrowprops=dict(arrowstyle='->')
		)
        self.maxAnnotation2.set_visible(False)
        # Create modelled transfer function
        self.transferModel, = self.ax2.plot(self.f1, self.S1Pre, "g.-", label="Modelled transfer function", linewidth=0.5)
        # Create arrays to hold current phases (pre averaging)
        self.phase1Pre = [0] * self.freqs1
        self.phase2Pre = [0] * self.freqs2
        # Possibly omit zero frequency
        if not self.spectral:
            self.phase1Pre = self.phase1Pre[1:len(self.phase1Pre)]
            self.phase2Pre = self.phase2Pre[1:len(self.phase2Pre)]
        # Create axis for phase
        self.ax3 = self.ax2.twinx()
        self.ax3.set_ylabel('Phase')
        # Create phases
        self.phase1, = self.ax3.plot(self.f1, self.phase1Pre, "b.", label=self.windows[0] + " window phase", markersize=1)
        self.phase2, = self.ax3.plot(self.f2, self.phase2Pre, "r.", label=self.windows[0] + " window phase", markersize=1)
        # Create modelled phase
        self.phaseModel, = self.ax3.plot(self.f1, self.phase1Pre, "g.", label="Modelled phase", markersize=1)
        # Start and end frequencies for the signal power integrator
        self.startF = 0
        self.endF = fMax
        # Indices of these frequencies
        self.startFindex = int(self.startF * (self.freqs1 - 1) / self.f1[-1])
        self.endFindex = int(self.endF * (self.freqs1 - 1) / self.f1[-1])
        # Markers for start and end frequency
        self.dots, = self.ax2.plot([self.startF, self.endF], [0, 0], "b^", ms = 10, label = "Total power in selected band: 0V$^2$")
        # Default sacling is logarithmic
        self.ax2.set_yscale("log")
        # Legend for spectral display
        # List of all plots for the legend
        self.plots = []
        # List of all plot titles
        self.plotTitles = []
        # Check for phase setting
        if self.phaseState == "Enabled":
            # Legend for frequency-phase diagram
            self.legendSpectra = self.ax3.legend(self.plots, self.plotTitles, loc="upper right", title="Averaged spectra: 1")
        else:
            # Legend for frequency diagram
            self.legendSpectra = self.ax2.legend(self.plots, self.plotTitles, loc="upper right", title="Averaged spectra: 1")
        # Draw the canvas
        canvas2 = FigureCanvasTkAgg(self.fig2)
        canvas2.draw()
        self.uiElements.append(canvas2.get_tk_widget())
        self.uiGridParams.append([2, 0, 1, 2, "NESW"])
        # Create data tip for spectra
        self.dataTipSpectra = L.dataTip(canvas2, self.ax2, 0.01)
        # Create frame for saving the plot
        self.saveFrame2 = Frame()
        self.uiElements.append(self.saveFrame2)
        self.uiGridParams.append([2, 2, 1, 1, "NS"])
        # Create save button
        self.saveButton2 = Button(master=self.saveFrame2, text=u"\U0001F4BE", font=("TkDefaultFont", 60))
        self.uiElements.append(self.saveButton2)
        self.uiGridParams.append([0, 0, 1, 1, ""])
        # Create label to display saved message
        self.saveLabel2 = Label(master=self.saveFrame2)
        self.uiElements.append(self.saveLabel2)
        self.uiGridParams.append([1, 0, 1, 1, ""])
        def updateSaveLabel2(event):
            path = L.savePath("Spectrum", self.dir)
            # save the image
            self.fig2.savefig(path + ".svg")
            # save the data of spectra as csv file
            L.saveFigCSV(self.fig2, path)
            # display the saved message
            self.saveLabel2.configure(text="Saved as " + path + "!")
            # schedule message removal
            self.window.after(2000, lambda: self.saveLabel2.configure(text=""))
        self.saveButton2.bind("<Button-1>", updateSaveLabel2)
        toolbar2 = L.VerticalPlotToolbar(canvas2, self.saveFrame2)
        toolbar2.update()
        toolbar2.pack_forget()
        self.uiElements.append(toolbar2)
        self.uiGridParams.append([2, 0, 1, 1, "NW"])
        # Create frame for the signal power integrator
        self.powerFrame = Frame(relief=RIDGE, borderwidth=2)
        self.uiElements.append(self.powerFrame)
        self.uiGridParams.append([3, 0, 1, 3, "WE"])
        self.powerFrame.columnconfigure(0, weight=1)
        # Create Label for the signal power integrator
        self.powerLabel = Label(master=self.powerFrame, text="Total Signal Power Integrator (First Spectrum)")
        self.uiElements.append(self.powerLabel)
        self.uiGridParams.append([0, 0, 1, 1, ""])
        # Create frame for the individual widgets
        self.powerSFrame = Frame(master=self.powerFrame, relief=RIDGE, borderwidth=2)
        self.uiElements.append(self.powerSFrame)
        self.uiGridParams.append([1, 0, 1, 1, "WE"])
        self.powerSFrame.columnconfigure((3, 5), weight=1)
        # Initialize power integrator state
        self.powerState = StringVar()
        self.powerState.set("Disabled")
        # Create power integrator state selector buttons
        self.powerDisable = Radiobutton(self.powerSFrame, text="Disabled", variable = self.powerState, value = "Disabled")
        self.uiElements.append(self.powerDisable)
        self.uiGridParams.append([0, 0, 1, 1, "E"])
        self.powerDisable.bind("<Button-1>", self.handle_disablePower)
        self.powerEnable = Radiobutton(self.powerSFrame, text="Enabled", variable = self.powerState, value = "Enabled")
        self.uiElements.append(self.powerEnable)
        self.uiGridParams.append([0, 1, 1, 1, "W"])
        self.powerEnable.bind("<Button-1>", self.handle_enablePower)
        # Create label for the start frequency entry box
        self.startFLabel = Label(master=self.powerSFrame, text="Start Frequency")
        self.uiElements.append(self.startFLabel)
        self.uiGridParams.append([0, 2, 1, 1, ""])
        # Variable to control content of the start frequency entry box
        self.startFV = DoubleVar()
        self.startFV.set(self.startF)
        # Create start frequency entry box
        self.startFEntry = Entry(master=self.powerSFrame, textvariable=self.startFV, justify=RIGHT)
        self.uiElements.append(self.startFEntry)
        self.uiGridParams.append([0, 3, 1, 1, "WE"])
        self.startFEntry.bind("<Return>", self.handle_updateStartF)
        self.startFEntry.bind("<KP_Enter>", self.handle_updateStartF)
        self.startFEntry.bind("<FocusOut>", self.handle_updateStartF)
        # Create label for the end frequency entry box
        self.endFLabel = Label(master=self.powerSFrame, text="End Frequency")
        self.uiElements.append(self.endFLabel)
        self.uiGridParams.append([0, 4, 1, 1, ""])
        # Variable to control content of the end frequency entry box
        self.endFV = DoubleVar()
        self.endFV.set(self.endF)
        # Create end frequency entry box
        self.endFEntry = Entry(master=self.powerSFrame, textvariable=self.endFV, justify=RIGHT)
        self.uiElements.append(self.endFEntry)
        self.uiGridParams.append([0, 5, 1, 1, "WE"])
        self.endFEntry.bind("<Return>", self.handle_updateEndF)
        self.endFEntry.bind("<KP_Enter>", self.handle_updateEndF)
        self.endFEntry.bind("<FocusOut>", self.handle_updateEndF)
        self.waitLabel = Label(text="Initializing... ",
                               font=("", 100))
        # status variable to prevent struggle for power between function calls
        self.busy = False
        self.handle_disablePower()
        self.updateAll(True)
        self.handle_updateWindow2()
        # Initially hide phases
        self.handle_phaseDis()
        # Initially hide model
        self.handle_modelDis()
        # Display the widgets
        L.buildUI(self.uiElements, self.uiGridParams)
        # Display correct filter parameters
        self.handle_updateFilter()
        # Maximize the window
        self.window.attributes("-zoomed", True)
        # Start the reading thread
        self.port.start(maxSize=self.dataSizeMax*4*100)
        # Start the serial connection monitor
        self.window.after(0, self.checkConnection)
        # Execute the function to read with the mainloop of the window (this is probably not the best solution)
        self.window.mainloop()
    
    # Update all board values since the program might still be running with different values from a previous session
    def updateAll(self, init):
        pre = "Initializing... "
        if not init:
            pre = "Restoring Settings... "
        self.waitLabel.grid(row=0, column=0, sticky="WE")
        self.waitLabel.configure(text=pre + "\\")
        self.window.update_idletasks()
        self.handle_updateFreq(force=True)
        self.waitLabel.configure(text=pre + "|")
        self.window.update_idletasks()
        self.handle_updateSize(force=True)
        self.waitLabel.configure(text=pre + "/")
        self.window.update_idletasks()
        self.handle_updateOvers(force=True)
        self.waitLabel.configure(text=pre + "-")
        self.window.update_idletasks()
        self.handle_updateMode()
        self.waitLabel.configure(text=pre + "\\")
        self.window.update_idletasks()
        self.handle_updateProc(force=True)
        self.waitLabel.configure(text=pre + "|")
        self.window.update_idletasks()
        self.handle_updateFilter()
        self.waitLabel.grid_forget()
    
    # Event handler for operation mode selector
    def handle_updateMode(self, event=None, recursive=False, recReact=False, val=None):
        newMode = self.modeSelect.get()
        if val != None:
            newMode = val
        # Stop reading during update
        react = self.reading
        if recursive:
            react = recReact
        self.reading = False
        if self.busy:
            self.window.after(1, lambda: self.handle_updateMode(recursive=True, recReact=react, val=newMode))
        else:
            # Seize Power
            self.busy = True
            # Update the mode
            self.mode = newMode
            time.sleep(0.005)
            self.port.writeL('deactivate AD4020')
            time.sleep(0.005)
            self.port.writeL('deactivate LTC2500')
            time.sleep(0.005)
            self.port.writeL('deactivate Internal ADC')
            if self.mode == "AD4020 spectral analysis":
                self.ax1.set_ylabel("Voltage AD4020 (V)")
                self.spectral = True
            elif self.mode == "LTC2500 spectral analysis":
                self.ax1.set_ylabel("Voltage LTC2500 (V)")
                self.spectral = True
            elif self.mode == "Internal ADC spectral analysis":
                self.ax1.set_ylabel("Voltage Internal ADC (V)")
                self.spectral = True
            elif (self.mode == "Pulse response & signal processing" or
                self.mode == "Step up response & signal processing" or
                self.mode == "Step down response & signal processing"):
                self.ax1.set_ylabel("Voltage AD4020 (V)")
                self.samplerateV.set(self.procV.get())
                self.handle_updateFreq()
                self.freqEntry["state"] = DISABLED
                self.windowSelect1.set("Rectangle")
                self.windowSelect2.set("Disabled")
                self.handle_updateWindow1()
                self.handle_updateWindow2()
                self.windowSelect1["state"] = DISABLED
                self.windowSelect2["state"] = DISABLED
                self.spectral = False
                # Enable model buttons as appropriate
                self.updateModelFilter()
                self.modelDisButton["state"] = NORMAL
                self.unitSelect.set("Normalized Spectrum")
                self.handle_updateUnit()
                # Update frequency indices in power integrator
                self.handle_updateStartF()
                self.handle_updateEndF()
                # show impulse response legend
                self.legendImpulse.set_visible(True)
            # Possibly hide impulse response legend
            if self.spectral:
                self.freqEntry["state"] = NORMAL
                self.windowSelect1["state"] = NORMAL
                self.windowSelect2["state"] = NORMAL
                self.modelDisButton["state"] = DISABLED
                self.modelHzButton["state"] = DISABLED
                self.modelHsButton["state"] = DISABLED
                self.legendImpulse.set_visible(False)
                self.handle_modelDis()
            time.sleep(0.005)
            self.port.writeL('set mode ' + str(self.mode))
            self.port.clearBuffer()
            self.readNext = True
            self.updateAxes()
            # Reactivate reading if paused by this function
            self.reading = react
            if react:
                self.window.after(0, self.readDisp)
            # resign from power
            self.busy = False

    # Event handler for samplerate entry box
    def handle_updateFreq(self, event=None, force=False, recursive=False, recReact=False, val=None):
        # Make sure the input is a number
        try:
            newSamplerate = float(self.freqEntry.get())
            if val != None:
                newSamplerate = val
            # Make sure the input is in the input range
            if newSamplerate < self.samplerateMin:
                newSamplerate = self.samplerateMin
            if newSamplerate > self.samplerateMax:
                newSamplerate = self.samplerateMax
            # Only update if the value has actually changed
            if newSamplerate != self.samplerate or force:
                # Stop reading during update
                react = self.reading
                if recursive:
                    react = recReact
                self.reading = False
                if self.busy:
                    self.window.after(1, lambda: self.handle_updateFreq(force=force, recursive=True, recReact=react, val=newSamplerate))
                else:
                    # Seize Power
                    self.busy = True
                    # Update variable for samplerate
                    self.samplerate = newSamplerate
                    # Write command to serial port
                    time.sleep(0.005)
                    self.port.writeL('set samplerate ' + str(self.samplerate))
                    # Update the axes
                    self.updateAxes()
                    # Clear serial buffer
                    self.port.clearBuffer()
                    self.readNext = True
                    # Reactivate reading if paused by this function
                    self.reading = react
                    if react:
                        self.window.after(0, self.readDisp)
                    # resign from power
                    self.busy = False
            else:
                pass
        except ValueError:
            pass
        if not self.busy:
            self.samplerateV.set(str(self.samplerate))
        self.window.update_idletasks()
    
    # Event handler for data size entry box
    def handle_updateSize(self, event=None, force=False, recursive=False, recReact=False, val=None):
        # Make sure the input is an integer
        if self.sizeEntry.get().isdigit():
            newSize = int(self.sizeEntry.get())
            if val != None:
                newSize = val
            # Make sure the input is in the input range
            if newSize < self.dataSizeMin:
                newSize = self.dataSizeMin
            if newSize > self.dataSizeMax:
                newSize = self.dataSizeMax
            # Only update if the value has actually changed
            if newSize != self.dataSize or force:
                # Stop reading during update
                react = self.reading
                if recursive:
                    react = recReact
                self.reading = False
                if self.busy:
                    self.window.after(1, lambda: self.handle_updateSize(force=force, recursive=True, recReact=react, val=newSize))
                else:
                    # Seize Power
                    self.busy = True
                    if newSize < self.dataSize:
                        self.data = self.data[self.dataSize-newSize:self.dataSize]
                    else:
                        self.data = np.pad(self.data, (newSize - self.dataSize, 0))
                    # Update variable for data size
                    self.dataSize = newSize
                    # Write command to serial port
                    time.sleep(0.005)
                    self.port.writeL('set dataSize ' + str(self.dataSize))
                    # If transform size entry box is disabled, overwrite the value
                    if self.transformSizeStatus.get() == "N_FT-1=N/2":
                        self.transformSize1 = math.floor(self.dataSize / 2)
                        self.transformSize2 = math.floor(self.dataSize / 2)
                        self.transformSize1V.set(str(self.transformSize1))
                        self.transformSize2V.set(str(self.transformSize2))
                    # Update the axes
                    self.updateAxes()
                    # Clear serial buffer
                    self.port.clearBuffer()
                    self.readNext = True
                    # Reactivate reading if paused by this function
                    self.reading = react
                    if react:
                        self.window.after(0, self.readDisp)
                    # resign from power
                    self.busy = False
        self.dataSizeV.set(str(self.dataSize))
        self.window.update_idletasks()
    
    # Event handler for oversamples entry box
    def handle_updateOvers(self, event=None, force=False, recursive=False, recReact=False, val=None):
        # Make sure the input is an integer
        if self.oversEntry.get().isdigit():
            newOvers = int(self.oversEntry.get())
            if val != None:
                newOvers = val
            # Make sure the input is in the input range
            if newOvers < self.oversMin:
                newOvers = self.oversMin
            if newOvers > self.oversMax:
                newOvers = self.oversMax
            # Only update if the value has actually changed
            if newOvers != self.oversamples or force:
                # Stop reading during update
                react = self.reading
                if recursive:
                    react = recReact
                self.reading = False
                if self.busy:
                    self.window.after(1, lambda: self.handle_updateOvers(force=force, recursive=True, recReact=react, val=newOvers))
                else:
                    # Seize Power
                    self.busy = True
                    # Update variable for oversamples
                    self.oversamples = newOvers
                    # Write command to serial port
                    time.sleep(0.005)
                    self.port.writeL('set oversamples ' + str(self.oversamples))
                    # Update the axes
                    self.updateAxes()
                    # Clear serial buffer
                    self.port.clearBuffer()
                    self.readNext = True
                    # Reactivate reading if paused by this function
                    self.reading = react
                    if react:
                        self.window.after(0, self.readDisp)
                    # resign from power
                    self.busy = False
        self.oversamplesV.set(str(self.oversamples))
        self.window.update_idletasks()
    
    # Event handler for processing rate input box
    def handle_updateProc(self, event=None, force=False, recursive=False, recReact=False, val=None):
        # Make sure the input is a number
        try:
            newProc = float(self.procEntry.get())
            if val != None:
                newProc = val
            # Make sure the input is in the input range
            if newProc < self.procMin:
                newProc = self.procMin
            if newProc > self.procMax:
                newProc = self.procMax
            # Only update if the value has actually changed
            if newProc != self.proc or force:
                # Stop reading during update
                react = self.reading
                if recursive:
                    react = recReact
                self.reading = False
                if self.busy:
                    self.window.after(1, lambda: self.handle_updateProc(force=force, recursive=True, recReact=react, val=newProc))
                else:
                    # Seize Power
                    self.busy = True
                    # Update variable for samplerate
                    self.proc = newProc
                    # Write command to serial port
                    time.sleep(0.005)
                    self.port.writeL('set processing rate ' + str(self.proc))
                    # Update the axes
                    self.updateAxes()
                    # Clear serial buffer
                    self.port.clearBuffer()
                    self.readNext = True
                    # Reactivate reading if paused by this function
                    self.reading = react
                    if react:
                        self.window.after(0, self.readDisp)
                    # resign from power
                    self.busy = False
                    if not self.spectral:
                        self.handle_updateFreq(force=force, val=self.proc)
        except ValueError:
            pass
        self.procV.set(str(self.proc))
        self.window.update_idletasks()
    
    # Reset the y-data and averaging of the spectra
    def resetYSpectra(self):
        self.averaged = 0
        rezero1 = [0] * self.freqs1
        rezero2 = [0] * self.freqs2
        # Possibly omit zero frequency and reset averaging of impulse response
        if not self.spectral:
            rezero1 = rezero1[1:len(rezero1)]
            rezero2 = rezero2[1:len(rezero2)]
            self.voltagePre = [0] * self.dataSize
        self.S1Pre = rezero1
        self.S2Pre = rezero2
        self.spectrum1.set_ydata(self.S1Pre)
        self.spectrum2.set_ydata(self.S2Pre)
        self.phase1Pre = rezero1
        self.phase2Pre = rezero2
        self.phase1.set_ydata(self.phase1Pre)
        self.phase2.set_ydata(self.phase2Pre)
    
    # Updates the x axes for plots
    def updateAxes(self):
        # Maximum time value
        tMax = (self.dataSize-1)*self.oversamples/self.samplerate
        # Update values for time axis
        self.x = np.linspace(0, tMax, self.dataSize)
        # Maximum frequency value
        fMax = self.samplerate/(2 * self.oversamples)
        # Number of frequencies
        #self.freqs1 = int(np.ceil((self.dataSize+1)/2))
        self.freqs1 = self.transformSize1+1
        self.freqs2 = self.transformSize2+1
        # Update values for frequency axis
        self.f1 = np.linspace(0, fMax, self.freqs1)
        self.f2 = np.linspace(0, fMax, self.freqs2)
        # Possibly omit zero frequency
        if not self.spectral:
            self.f1 = self.f1[1:len(self.f1)]
            self.f2 = self.f2[1:len(self.f2)]
        # Update the axes data
        self.voltage.set_xdata(self.x)
        #self.spectrum1.set_xdata(self.f1[1:len(self.f1)])
        self.spectrum1.set_xdata(self.f1)
        self.spectrum2.set_xdata(self.f2)
        self.phase1.set_xdata(self.f1)
        self.phase2.set_xdata(self.f2)
        middle = int(self.freqs1 * (self.prop1Value[4] + self.prop2Value[4]) / self.samplerate) - 1
        self.normIndex = [0, 0, 0, self.freqs1-2, middle, 0, 0, self.freqs1-2, 0, 0, None]
        if self.spectral:
            self.transferModel.set_xdata(self.f1[1:len(self.f1)])
            self.phaseModel.set_xdata(self.f1[1:len(self.f1)])
        else:
            self.transferModel.set_xdata(self.f1)
            self.phaseModel.set_xdata(self.f1)
        self.voltage.set_ydata(self.data)
        self.resetYSpectra()
        # Update power integrator indices
        self.handle_updateStartF()
        self.handle_updateEndF()
        # Set time axes scale
        self.ax1.set_xlim([0, tMax])
        # Set frequency axis limits to match data
        self.ax2.set_xlim([0, fMax])
        if self.phaseState == "Enabled":
            self.ax3.set_xlim([0, fMax])
        # Redraw the model
        self.drawModelCurve()
        # Update the canvases
        L.updateCanvas(self.fig1.canvas, self.ax1, False, True)
        L.updateCanvas(self.fig2.canvas, self.ax2, False, True)
        if self.phaseState == "Enabled":
            L.updateCanvas(self.fig2.canvas, self.ax3, False, True)
    
    # Callback function for changing the y-scale to "Logarithmic"
    def handle_logScale(self, event):
        # Don't change state if button is disabled
        if self.logButton["state"] == DISABLED:
            return
        self.ax2.set_yscale("log")
        # Update the canvas for the spectra
        L.updateCanvas(self.fig2.canvas, self.ax2, False, True)

    # Callback function for changing the y-scale to "Linear"
    def handle_linScale(self, event):
        # Don't change state if button is disabled
        if self.linButton["state"] == DISABLED:
            return
        self.ax2.set_yscale("linear")
        # Update the canvas for the spectra
        L.updateCanvas(self.fig2.canvas, self.ax2, False, True)
    
    # Event handler for window selector 1
    def handle_updateWindow1(self, event=None):
        if self.window1.get() == "Disabled":
            self.spectrum1.set_visible(False)
            if self.phaseState == "Enabled":
                self.phase1.set_visible(False)
            self.maxAnnotation1.set_visible(False)
            #self.dataTipSpectrum1.setState(DISABLED)
        else:
            self.spectrum1.set_visible(True)
            if self.phaseState == "Enabled":
                self.phase1.set_visible(True)
            self.maxAnnotation1.set_visible(True)
            #self.dataTipSpectrum1.setState(NORMAL)
            self.winFunc1 = "Window" + self.window1.get() + "." + "Window" + self.window1.get()
            self.resetYSpectra()
    
    # Event handler for window selector 2
    def handle_updateWindow2(self, event=None):
        if self.window2.get() == "Disabled":
            self.spectrum2.set_visible(False)
            if self.phaseState == "Enabled":
                self.phase2.set_visible(False)
            self.maxAnnotation2.set_visible(False)
            #self.dataTipSpectrum2.setState(DISABLED)
        else:
            self.spectrum2.set_visible(True)
            if self.phaseState == "Enabled":
                self.phase2.set_visible(True)
            self.maxAnnotation2.set_visible(True)
            #self.dataTipSpectrum2.setState(NORMAL)
            self.winFunc2 = "Window" + self.window2.get() + "." + "Window" + self.window2.get()
            self.resetYSpectra()
    
    # Event handler for spectrum unit selector (also used by readDisp)
    def handle_updateUnit(self, event=None):
        self.ax2.set_ylabel(self.unitLabels[self.unitList.index(self.unitSelect.get())])
        if self.unitSelect.get() == "Power Spectral Density":
            S1 = np.divide(np.power(np.divide(self.S1Pre, self.averaged), 2), self.enbw1)
            S2 = np.divide(np.power(np.divide(self.S2Pre, self.averaged), 2), self.enbw2)
        elif self.unitSelect.get() == "Power Spectrum":
            S1 = np.power(np.divide(self.S1Pre, self.averaged), 2)
            S2 = np.power(np.divide(self.S2Pre, self.averaged), 2)
        elif self.unitSelect.get() == "Amplitude Spectral Density":
            S1 = np.divide(self.S1Pre, (self.averaged * np.sqrt(self.enbw1)))
            S2 = np.divide(self.S2Pre, (self.averaged * np.sqrt(self.enbw2)))
        elif self.unitSelect.get() == "Amplitude Spectrum":
            S1 = np.divide(self.S1Pre, self.averaged)
            S2 = np.divide(self.S2Pre, self.averaged)
        elif self.unitSelect.get() == "Normalized Spectrum":
            if self.normIndex[self.filterIndex] == None:
                S1 = np.divide(self.S1Pre, max(self.S1Pre))
                S2 = np.divide(self.S2Pre, max(self.S2Pre))
            else:
                S1 = np.divide(self.S1Pre, self.S1Pre[self.normIndex[self.filterIndex]])
                S2 = np.divide(self.S2Pre, self.S2Pre[self.normIndex[self.filterIndex]])
        self.spectrum1.set_ydata(S1)
        self.spectrum2.set_ydata(S2)
        self.dots.set_ydata([S1[self.startFindex], S1[self.endFindex]])
        # Update the canvas for the spectra
        L.updateCanvas(self.fig2.canvas, self.ax2, False, True)
    
    # Callback function for changing the subtraction to "Disabled"
    def handle_subDis(self, event):
        # Don't change state if button is disabled
        if self.subDisButton["state"] == DISABLED:
            return
        self.subtract.set("Disabled")
        # Update the axes
        self.updateAxes()
        # Clear serial buffer
        self.port.clearBuffer()
        self.readNext = True
    
    # Callback function for changing the subtraction to "Enabled"
    def handle_subEn(self, event):
        # Don't change state if button is disabled
        if self.subEnButton["state"] == DISABLED:
            return
        self.subtract.set("Enabled")
        # Update the axes
        self.updateAxes()
        # Clear serial buffer
        self.port.clearBuffer()
        self.readNext = True
    
    # Callback function for changing the phase to "Disabled"
    def handle_phaseDis(self, event=None):
        # Don't change state if button is disabled
        if self.phaseDisButton["state"] == DISABLED:
            return
        self.phaseState = "Disabled"
        self.phaseStateV.set(self.phaseState)
        # Hide phases
        self.phase1.set_visible(False)
        self.phase2.set_visible(False)
        self.phaseModel.set_visible(False)
        self.ax3.set_visible(False)
    
    # Callback function for changing the phase to "Enabled"
    def handle_phaseEn(self, event):
        # Don't change state if button is disabled
        if self.phaseEnButton["state"] == DISABLED:
            return
        self.phaseState  = "Enabled"
        self.phaseStateV.set(self.phaseState)
        # Display phases
        if self.window1.get() != "Disabled":
            self.phase1.set_visible(True)
        if self.window2.get() != "Disabled":
            self.phase2.set_visible(True)
        self.ax3.set_visible(True)
        self.drawModelCurve()
    
    # Event handler for transform size entry box
    def handle_updateTransformSize1(self, event=None):
        # Stop reading during update
        reactivate = False
        if self.reading:
            reactivate = True
            self.reading = False
        # Make sure the input is an integer
        if self.transformSize1Entry.get().isdigit():
            newTransformSize1 = int(self.transformSize1Entry.get())
            # Make sure the input is in the input range
            if newTransformSize1 < self.transformSizeMin:
                newTransformSize1 = self.transformSizeMin
            if newTransformSize1 > self.transformSizeMax:
                newTransformSize1 = self.transformSizeMax
            # Update variable for transform size
            self.transformSize1 = newTransformSize1
            # Update the axes
            self.updateAxes()
            # Clear serial buffer
            self.port.clearBuffer()
            self.readNext = True
        self.transformSize1V.set(str(self.transformSize1))
        self.window.update_idletasks()
        # Reactivate reading if paused by this function
        if reactivate:
            self.reading = True
            self.window.after(0, self.readDisp)
    
    # Event handler for transform size entry box
    def handle_updateTransformSize2(self, event=None):
        # Stop reading during update
        reactivate = False
        if self.reading:
            reactivate = True
            self.reading = False
        # Make sure the input is an integer
        if self.transformSize2Entry.get().isdigit():
            newTransformSize2 = int(self.transformSize2Entry.get())
            # Make sure the input is in the input range
            if newTransformSize2 < self.transformSizeMin:
                newTransformSize2 = self.transformSizeMin
            if newTransformSize2 > self.transformSizeMax:
                newTransformSize2 = self.transformSizeMax
            # Update variable for transform size
            self.transformSize2 = newTransformSize2
            # Update the axes
            self.updateAxes()
            # Clear serial buffer
            self.port.clearBuffer()
            self.readNext = True
        self.transformSize2V.set(str(self.transformSize2))
        self.window.update_idletasks()
        # Reactivate reading if paused by this function
        if reactivate:
            self.reading = True
            self.window.after(0, self.readDisp)
    
    # Callback function for changing the y-scale to "Logarithmic"
    def handle_customTransform(self, event):
        # Don't change state if button is disabled
        if self.N_FTButton["state"] == DISABLED:
            return
        self.transformSize1Entry["state"] = NORMAL
        self.transformSize2Entry["state"] = NORMAL
        self.transformSizeStatus.set("N_FT-1")

    # Callback function for changing the y-scale to "Linear"
    def handle_lockedTransform(self, event):
        # Don't change state if button is disabled
        if self.NButton["state"] == DISABLED:
            return
        self.transformSize1Entry["state"] = DISABLED
        self.transformSize2Entry["state"] = DISABLED
        self.transformSizeStatus.set("N_FT-1=N/2")
        self.handle_updateSize(force=True)
    
    # Updates the model state buttons according to the filter
    def updateModelFilter(self):
        if not self.spectral:
            if self.hzEnabled[self.filterIndex]:
                self.modelHzButton["state"] = NORMAL
            else:
                self.modelHzButton["state"] = DISABLED
                if self.modelState == "H(z)":
                    if self.hsEnabled[self.filterIndex]:
                        self.handle_modelHs()
                    else:
                        self.handle_modelDis()
            if self.hsEnabled[self.filterIndex]:
                self.modelHsButton["state"] = NORMAL
            else:
                self.modelHsButton["state"] = DISABLED
                if self.modelState == "H(s)":
                    if self.hzEnabled[self.filterIndex]:
                        self.handle_modelHz()
                    else:
                        self.handle_modelDis()
    
    # Event handler for signal filter selector
    def handle_updateFilter(self, event=None, recursive=False, recReact=False, val=None):
        newFilter = self.filterSelect.get()
        if val != None:
            newFilter = val
        # Stop reading during update
        react = self.reading
        if recursive:
            react = recReact
        self.reading = False
        if self.busy:
            self.window.after(1, lambda: self.handle_updateFilter(recursive=True, recReact=react, val=newFilter))
        else:
            # Seize Power
            self.busy = True
            self.prop1Label.grid_forget()
            self.prop1Entry.grid_forget()
            self.prop2Label.grid_forget()
            self.prop2Entry.grid_forget()
            self.prop3Label.grid_forget()
            self.prop3Entry.grid_forget()
            self.prop4Label.grid_forget()
            self.windowSelect.grid_forget()
            self.prop5Label.grid_forget()
            self.arithmeticSelect.grid_forget()
            for k in range(len(self.filters)):
                if newFilter == self.filters[k]:
                    self.filterIndex = k
                    self.prop1Label.configure(text=self.prop1Names[k])
                    self.prop2Label.configure(text=self.prop2Names[k])
                    self.prop3Label.configure(text=self.prop3Names[k])
                    self.prop4Label.configure(text=self.prop4Names[k])
                    self.prop5Label.configure(text=self.prop5Names[k])
                    if self.prop1Visible[k]:
                        self.prop1Label.grid(row=1, column=0, sticky="E")
                        self.prop1Entry.grid(row=1, column=1, columnspan=1, sticky="WE")
                    else:
                        pass
                    if self.prop2Visible[k]:
                        self.prop2Label.grid(row=2, column=0, sticky="E")
                        self.prop2Entry.grid(row=2, column=1, columnspan=1, sticky="WE")
                    else:
                        pass
                    if self.prop3Visible[k]:
                        self.prop3Label.grid(row=3, column=0, sticky="E")
                        self.prop3Entry.grid(row=3, column=1, columnspan=1, sticky="WE")
                    else:
                        pass
                    if self.prop4Visible[k]:
                        self.prop4Label.grid(row=4, column=0, sticky="E")
                        self.windowSelect.grid(row=4, column=1, columnspan=1, sticky="WE")
                    if self.prop5Visible[k]:
                        self.prop5Label.grid(row=5, column=0, sticky="E")
                        self.arithmeticSelect.grid(row=5, column=1, columnspan=1, sticky="WE")
                    self.prop1V.set(self.prop1Value[k])
                    self.prop2V.set(self.prop2Value[k])
                    self.prop3V.set(self.prop3Value[k])
                    self.prop4V.set(self.prop4Value[k])
                    self.prop5V.set(self.prop5Value[k])
                    self.windowSelect.set(str(self.prop4Value[k]))
                    self.arithmeticSelect.set(str(self.prop5Value[k]))
                    self.updateModelFilter()
            time.sleep(0.005)
            self.port.writeL("set filter " + newFilter)
            self.resetYSpectra()
            # Clear the buffer
            self.port.clearBuffer()
            self.readNext = True
            # Reactivate reading if paused by this function
            self.reading = react
            if react:
                self.window.after(0, self.readDisp)
            # resign from power
            self.busy = False
            # Update all filter properties
            self.handle_updateProp1(force=True)
            self.handle_updateProp2(force=True)
            self.handle_updateProp3(force=True)
            self.handle_updateWindow(force=True)
            self.handle_updateArithmetic(force=True)
    
    # Event handler for filter property 1 entry box
    def handle_updateProp1(self, event=None, force=False, recursive=False, recReact=False, val=None):
        # Make sure the input has the correct type
        newProp = self.prop1Value[self.filterIndex]
        if self.prop1Type[self.filterIndex] == "Integer":
            try:
                newProp = int(self.prop1V.get())
            except ValueError:
                pass
        elif self.prop1Type[self.filterIndex] == "Float":
            try:
                newProp = float(self.prop1V.get())
            except ValueError:
                pass
        elif self.prop1Type[self.filterIndex] == "String":
            newProp = self.prop1V.get()
        else:
            return
        if val != None:
            newProp = val
        if self.prop1Type[self.filterIndex] != "String":
            # Make sure the input is in the input range
            if newProp < self.prop1Min[self.filterIndex]:
                newProp = self.prop1Min[self.filterIndex]
            if newProp > self.prop1Max[self.filterIndex]:
                newProp = self.prop1Max[self.filterIndex]
        # Only update if the value has actually changed
        if newProp != self.prop1Value[self.filterIndex] or force:
            # Stop reading during update
            react = self.reading
            if recursive:
                react = recReact
            self.reading = False
            if self.busy:
                self.window.after(1, lambda: self.handle_updateProp1(force=force, recursive=True, recReact=react, val=newProp))
            else:
                # Seize Power
                self.busy = True
                # Update variable for filter property 1
                self.prop1Value[self.filterIndex] = newProp
                # Write command to serial port
                time.sleep(0.005)
                self.port.writeL("set filterProperty1 " + str(self.prop1Value[self.filterIndex]))
                self.drawModelCurve()
                # Update the axes
                self.updateAxes()
                # Clear the buffer
                self.port.clearBuffer()
                self.readNext = True
                # Reactivate reading if paused by this function
                self.reading = react
                if react:
                    self.window.after(0, self.readDisp)
                # resign from power
                self.busy = False
        self.prop1V.set(str(self.prop1Value[self.filterIndex]))
        self.window.update_idletasks()
    
    # Event handler for filter property 2 entry box
    def handle_updateProp2(self, event=None, force=False, recursive=False, recReact=False, val=None):
        # Make sure the input has the correct type
        newProp = self.prop2Value[self.filterIndex]
        if self.prop2Type[self.filterIndex] == "Integer":
            try:
                newProp = int(self.prop2V.get())
            except ValueError:
                pass
        elif self.prop2Type[self.filterIndex] == "Float":
            try:
                newProp = float(self.prop2V.get())
            except ValueError:
                pass
        elif self.prop2Type[self.filterIndex] == "String":
            newProp = self.prop2V.get()
        else:
            return
        if val != None:
            newProp = val
        if self.prop2Type[self.filterIndex] != "String":
            # Make sure the input is in the input range
            if newProp < self.prop2Min[self.filterIndex]:
                newProp = self.prop2Min[self.filterIndex]
            if newProp > self.prop2Max[self.filterIndex]:
                newProp = self.prop2Max[self.filterIndex]
        # Only update if the value has actually changed
        if newProp != self.prop2Value[self.filterIndex] or force:
            # Stop reading during update
            react = self.reading
            if recursive:
                react = recReact
            self.reading = False
            if self.busy:
                self.window.after(1, lambda: self.handle_updateProp2(force=force, recursive=True, recReact=react, val=newProp))
            else:
                # Seize Power
                self.busy = True
                # Update variable for filter property 2
                self.prop2Value[self.filterIndex] = newProp
                # Write command to serial port
                time.sleep(0.005)
                self.port.writeL("set filterProperty2 " + str(self.prop2Value[self.filterIndex]))
                self.drawModelCurve()
                # Update the axes
                self.updateAxes()
                # Clear the buffer
                self.port.clearBuffer()
                self.readNext = True
                # Reactivate reading if paused by this function
                self.reading = react
                if react:
                    self.window.after(0, self.readDisp)
                # resign from power
                self.busy = False
        self.prop2V.set(str(self.prop2Value[self.filterIndex]))
        self.window.update_idletasks()
    
    # Event handler for filter property 3 entry box
    def handle_updateProp3(self, event=None, force=False, recursive=False, recReact=False, val=None):
        # Make sure the input has the correct type
        newProp = self.prop3Value[self.filterIndex]
        if self.prop3Type[self.filterIndex] == "Integer":
            try:
                newProp = int(self.prop3V.get())
                # Special case for this property: The filter order must be a multitude of 2
                newProp = 2*int(newProp/2)
            except ValueError:
                pass
        elif self.prop3Type[self.filterIndex] == "Float":
            try:
                newProp = float(self.prop3V.get())
            except ValueError:
                pass
        elif self.prop3Type[self.filterIndex] == "String":
            newProp = self.prop3V.get()
        else:
            return
        if val != None:
            newProp = val
        if self.prop3Type[self.filterIndex] != "String":
            # Make sure the input is in the input range
            if newProp < self.prop3Min[self.filterIndex]:
                newProp = self.prop3Min[self.filterIndex]
            if newProp > self.prop3Max[self.filterIndex]:
                newProp = self.prop3Max[self.filterIndex]
        # Only update if the value has actually changed
        if newProp != self.prop3Value[self.filterIndex] or force:
            # Stop reading during update
            react = self.reading
            if recursive:
                react = recReact
            self.reading = False
            if self.busy:
                self.window.after(1, lambda: self.handle_updateProp3(force=force, recursive=True, recReact=react, val=newProp))
            else:
                # Seize Power
                self.busy = True
                # Update variable for filter property 3
                self.prop3Value[self.filterIndex] = newProp
                # Write command to serial port
                time.sleep(0.005)
                self.port.writeL("set filterProperty3 " + str(self.prop3Value[self.filterIndex]))
                self.drawModelCurve()
                # Update the axes
                self.updateAxes()
                # Clear the buffer
                self.port.clearBuffer()
                self.readNext = True
                # Reactivate reading if paused by this function
                self.reading = react
                if react:
                    self.window.after(0, self.readDisp)
                # resign from power
                self.busy = False
        self.prop3V.set(str(self.prop3Value[self.filterIndex]))
        self.window.update_idletasks()
    
    # Event handler for filter property 4 selector
    def handle_updateWindow(self, event=None, force=False):
        self.prop4V.set(self.windowSelect.get())
        self.handle_updateProp4(force)
    
    # Update function for filter property 4
    def handle_updateProp4(self, force=False, recursive=False, recReact=False, val=None):
        # Make sure the input has the correct type
        newProp = self.prop4Value[self.filterIndex]
        if self.prop4Type[self.filterIndex] == "Integer":
            try:
                newProp = int(self.prop4V.get())
            except ValueError:
                pass
        elif self.prop4Type[self.filterIndex] == "Float":
            try:
                newProp = float(self.prop4V.get())
            except ValueError:
                pass
        elif self.prop4Type[self.filterIndex] == "String":
            newProp = self.prop4V.get()
        else:
            return
        if val != None:
            newProp = val
        if self.prop4Type[self.filterIndex] != "String":
            # Make sure the input is in the input range
            if newProp < self.prop4Min[self.filterIndex]:
                newProp = self.prop4Min[self.filterIndex]
            if newProp > self.prop4Max[self.filterIndex]:
                newProp = self.prop4Max[self.filterIndex]
        # Only update if the value has actually changed
        if newProp != self.prop4Value[self.filterIndex] or force:
            # Stop reading during update
            react = self.reading
            if recursive:
                react = recReact
            self.reading = False
            if self.busy:
                self.window.after(1, lambda: self.handle_updateProp4(force=force, recursive=True, recReact=react, val=newProp))
            else:
                # Seize Power
                self.busy = True
                # Update variable for filter property 4
                self.prop4Value[self.filterIndex] = newProp
                # Write command to serial port
                time.sleep(0.005)
                self.port.writeL("set filterProperty4 " + str(self.prop4Value[self.filterIndex]))
                self.drawModelCurve()
                # Update the axes
                self.updateAxes()
                # Clear the buffer
                self.port.clearBuffer()
                self.readNext = True
                # Reactivate reading if paused by this function
                self.reading = react
                if react:
                    self.window.after(0, self.readDisp)
                # resign from power
                self.busy = False
        self.prop4V.set(str(self.prop4Value[self.filterIndex]))
        self.window.update_idletasks()
    
    # Event handler for arithmetic selector
    def handle_updateArithmetic(self, event=None, force=False):
        self.prop5V.set(self.arithmeticSelect.get())
        self.handle_updateProp5(force)
    
    # Update function for filter property 5
    def handle_updateProp5(self, force=False, recursive=False, recReact=False, val=None):
        # Make sure the input has the correct type
        newProp = self.prop5Value[self.filterIndex]
        if self.prop5Type[self.filterIndex] == "Integer":
            try:
                newProp = int(self.prop5V.get())
            except ValueError:
                pass
        elif self.prop5Type[self.filterIndex] == "Float":
            try:
                newProp = float(self.prop5V.get())
            except ValueError:
                pass
        elif self.prop5Type[self.filterIndex] == "String":
            newProp = self.prop5V.get()
        else:
            return
        if val != None:
            newProp = val
        if self.prop5Type[self.filterIndex] != "String":
            # Make sure the input is in the input range
            if newProp < self.prop5Min[self.filterIndex]:
                newProp = self.prop5Min[self.filterIndex]
            if newProp > self.prop5Max[self.filterIndex]:
                newProp = self.prop5Max[self.filterIndex]
        # Only update if the value has actually changed
        if newProp != self.prop5Value[self.filterIndex] or force:
            # Stop reading during update
            react = self.reading
            if recursive:
                react = recReact
            self.reading = False
            if self.busy:
                self.window.after(1, lambda: self.handle_updateProp5(force=force, recursive=True, recReact=react, val=newProp))
            else:
                # Seize Power
                self.busy = True
                # Update variable for filter property 5
                self.prop5Value[self.filterIndex] = newProp
                # Write command to serial port
                time.sleep(0.005)
                self.port.writeL("set filterProperty5 " + str(self.prop5Value[self.filterIndex]))
                self.drawModelCurve()
                # Update the axes
                self.updateAxes()
                # Clear the buffer
                self.port.clearBuffer()
                self.readNext = True
                # Reactivate reading if paused by this function
                self.reading = react
                if react:
                    self.window.after(0, self.readDisp)
                # resign from power
                self.busy = False
        self.prop5V.set(str(self.prop5Value[self.filterIndex]))
        self.window.update_idletasks()
    
    # Function to update the model state and its radiobuttons
    def updateModelState(self):
        # Set string variable
        self.modelStateV.set(self.modelState)
        # Hide/show models
        if self.modelState == "Disabled":
            self.transferModel.set_visible(False)
            self.phaseModel.set_visible(False)
        else:
            self.transferModel.set_visible(True)
            if self.phaseState != "Disabled":
                self.phaseModel.set_visible(True)
        self.drawModelCurve()
        L.updateCanvas(self.fig2.canvas, self.ax2, False, True)
    
    # Callback function for changing the model to "Disabled"
    def handle_modelDis(self, event=None):
        # Don't change state if button is disabled
        if self.modelDisButton["state"] == DISABLED:
            return
        self.modelState = "Disabled"
        self.updateModelState()
    
    # Callback function for changing the model to "H(z)"
    def handle_modelHz(self, event=None):
        # Don't change state if button is disabled
        if self.modelHzButton["state"] == DISABLED:
            return
        self.modelState = "H(z)"
        self.updateModelState()
    
    # Callback function for changing the model to "H(s)"
    def handle_modelHs(self, event=None):
        # Don't change state if button is disabled
        if self.modelHsButton["state"] == DISABLED:
            return
        self.modelState = "H(s)"
        self.updateModelState()
    
    # Function to draw the modelled transfer function and phase
    def drawModelCurve(self):
        if self.modelState == "Disabled":
            self.transferModel.set_visible(False)
            self.phaseModel.set_visible(False)
            return
        curFilter = self.filters[self.filterIndex]
        import WindowHamming
        import WindowRectangle
        if curFilter == "Scaling":
            self.transferModel.set_ydata([1] * (self.freqs1 - 1))
            phases = np.linspace(0, -2*np.pi, self.freqs1)
            phases = phases[1:len(phases)]
            self.phaseModel.set_ydata(phases)
        elif curFilter == "Moving average":
            hma = None
            if self.modelState == "H(z)":
                hma = np.divide(np.subtract(np.exp(np.multiply(np.multiply(1j, 2*np.pi*self.prop1Value[self.filterIndex]/self.proc), self.f1)), 1), 
                            np.subtract(np.exp(np.multiply(np.multiply(1j, 2*np.pi/self.proc), self.f1)), 1))
            elif self.modelState == "H(s)":
                hma = np.divide(np.subtract(np.exp(np.multiply(np.multiply(1j, 2*np.pi*self.prop1Value[self.filterIndex]/self.proc), self.f1)), 1), 
                            np.subtract(np.exp(np.multiply(np.multiply(1j, 2*np.pi/self.proc), self.f1)), 1))
            hma = np.divide(hma, np.abs(hma[self.normIndex[self.filterIndex]]))
            self.transferModel.set_ydata(np.abs(hma))
            self.phaseModel.set_ydata(-np.angle(hma))
            # Hier ist die Phase falsch
        elif curFilter == "Low pass filter 1st order":
            # Catch case of f_c=0
            if self.prop1Value[self.filterIndex] == 0:
                self.transferModel.set_visible(False)
                self.phaseModel.set_visible(False)
                return
            hlpf = None
            if self.modelState == "H(z)":
                hlpf = np.divide(1, np.add(1, np.multiply(self.proc/(2*np.pi*self.prop1Value[self.filterIndex]), np.subtract(1, np.exp(np.multiply(-2*np.pi*1j/self.proc, self.f1))))))
                #hlpf = np.divide(1, np.add(1, np.divide(np.exp(np.multiply(1j*2*np.pi/self.proc, self.f1)), 2*np.pi*self.prop1Value[self.filterIndex])))
            elif self.modelState == "H(s)":
                hlpf = np.divide(1, np.add(1, np.multiply(1j/self.prop1Value[self.filterIndex], self.f1)))
            #hlpf = np.divide(1, np.add(1, np.divide(np.exp(np.multiply(1j*2*np.pi/self.proc, self.f1)), 2*np.pi*self.prop1Value[self.filterIndex])))
            hlpf = np.divide(hlpf, np.abs(hlpf[self.normIndex[self.filterIndex]]))
            self.transferModel.set_ydata(abs(hlpf))
            self.phaseModel.set_ydata(np.angle(hlpf))
        elif curFilter == "High pass filter 1st order":
            hhpf = None
            if self.modelState == "H(z)":
                hhpf = np.divide(1, np.add(1, np.divide(2*np.pi*self.prop1Value[self.filterIndex]/self.proc, np.subtract(1, np.exp(np.multiply(-2*np.pi*1j/self.proc, self.f1))))))
                np.divide(1, np.subtract(1, np.divide(1j*self.prop1Value[self.filterIndex], self.f1)))
            elif self.modelState == "H(s)":
                hhpf = np.divide(1, np.subtract(1, np.divide(1j*self.prop1Value[self.filterIndex], self.f1)))
            hhpf = np.divide(hhpf, np.abs(hhpf[self.normIndex[self.filterIndex]]))
            self.transferModel.set_ydata(abs(hhpf))
            self.phaseModel.set_ydata(np.angle(hhpf))
        elif curFilter == "FIR bandpass filter":
            nFilter = self.prop3Value[self.filterIndex]
            k = np.linspace(-nFilter/2, nFilter/2, nFilter+1)
            phi1 = 2*np.pi*self.prop1Value[self.filterIndex] / self.proc
            phi2 = 2*np.pi*self.prop2Value[self.filterIndex] / self.proc
            hres = None
            if self.modelState == "H(z)":
                hres = np.divide((np.sin(np.multiply(phi2, k)) - np.sin(np.multiply(phi1, k))), np.multiply(np.pi, k))
                hres[int((len(hres)-1) / 2)] = (phi2-phi1) / np.pi
                win, dummyVal = eval("Window" + self.prop4Value[self.filterIndex] + ".Window" + self.prop4Value[self.filterIndex] + "(" + str(nFilter+1) + ")")
                hres = np.multiply(hres, np.pad(win, (len(hres)-len(win)), constant_values=(1, 1)))
            #elif self.modelState == "H(s)":
            #    hres = np.divide((np.sin(np.multiply(phi2, k)) - np.sin(np.multiply(phi1, k))), np.multiply(np.pi, k))
            #    hres[int((len(hres)-1) / 2)] = (phi2-phi1) / np.pi
            self.prop1Value[self.filterIndex]
            self.normIndex[self.filterIndex] = int((self.prop1Value[self.filterIndex] + self.prop2Value[self.filterIndex]) * 
                                                    len(self.transferModel.get_xdata()) / self.proc)
            Hzf = np.fft.fft(hres, n=2*len(self.transferModel.get_xdata()))
            Hzf = Hzf[1:int(len(Hzf)/2)+1]
            self.transferModel.set_ydata(np.divide(abs(Hzf), abs(Hzf)[self.normIndex[self.filterIndex]]))
            self.phaseModel.set_ydata(np.angle(Hzf))
        elif curFilter == "FIR bandstop filter":
            nFilter = self.prop3Value[self.filterIndex]
            k = np.linspace(-nFilter/2, nFilter/2, nFilter+1)
            phi1 = 2*np.pi*self.prop1Value[self.filterIndex] / self.proc
            phi2 = 2*np.pi*self.prop2Value[self.filterIndex] / self.proc
            hres = None
            if self.modelState == "H(z)":
                hres = -np.divide((np.sin(np.multiply(phi2, k)) - np.sin(np.multiply(phi1, k))), np.multiply(np.pi, k))
                hres[int((len(hres)-1) / 2)] = 1 - (phi2-phi1) / np.pi
                win, dummyVal = eval("Window" + self.prop4Value[self.filterIndex] + ".Window" + self.prop4Value[self.filterIndex] + "(" + str(nFilter+1) + ")")
                hres = np.multiply(hres, np.pad(win, (len(hres)-len(win)), constant_values=(1, 1)))
            #elif self.modelState == "H(s)":
            #    hres = -np.divide((np.sin(np.multiply(phi2, k)) - np.sin(np.multiply(phi1, k))), np.multiply(np.pi, k))
            #    hres[int((len(hres)-1) / 2)] = 1 - (phi2-phi1) / np.pi
            Hzf = np.fft.fft(hres, n=2*len(self.transferModel.get_xdata()))
            Hzf = Hzf[1:int(len(Hzf)/2)+1]
            self.transferModel.set_ydata(np.divide(abs(Hzf), abs(Hzf)[self.normIndex[self.filterIndex]]))
            self.phaseModel.set_ydata(np.angle(Hzf))
        elif curFilter == "FIR low pass filter":
            nFilter = self.prop3Value[self.filterIndex]
            k = np.linspace(-nFilter/2, nFilter/2, nFilter+1)
            phic = 2*np.pi*self.prop1Value[self.filterIndex] / self.proc
            hres = None
            if self.modelState == "H(z)":
                hres = np.divide(np.sin(np.multiply(phic, k)), np.multiply(np.pi, k))
                hres[int((len(hres)-1) / 2)] = phic / np.pi
                win, dummyVal = eval("Window" + self.prop4Value[self.filterIndex] + ".Window" + self.prop4Value[self.filterIndex] + "(" + str(nFilter+1) + ")")
                hres = np.multiply(hres, np.pad(win, (len(hres)-len(win)), constant_values=(1, 1)))
            #elif self.modelState == "H(s)":
            #    hres = np.divide(np.sin(np.multiply(phic, k)), np.multiply(np.pi, k))
            #    hres[int((len(hres)-1) / 2)] = phic / np.pi
            Hzf = np.fft.fft(hres, n=2*len(self.transferModel.get_xdata()))
            Hzf = Hzf[1:int(len(Hzf)/2)+1]
            self.transferModel.set_ydata(np.divide(abs(Hzf), abs(Hzf)[self.normIndex[self.filterIndex]]))
            self.phaseModel.set_ydata(np.angle(Hzf))
        elif curFilter == "FIR high pass filter":
            nFilter = self.prop3Value[self.filterIndex]
            k = np.linspace(-nFilter/2, nFilter/2, nFilter+1)
            phic = 2*np.pi*self.prop1Value[self.filterIndex] / self.proc
            hres = None
            if self.modelState == "H(z)":
                hres = np.subtract(np.divide(np.sin(np.multiply(np.pi, k)), np.multiply(np.pi, k)), np.divide(np.sin(np.multiply(phic, k)), np.multiply(np.pi, k)))
                hres[int((len(hres)-1) / 2)] = 1 - phic / np.pi
                win, dummyVal = eval("Window" + self.prop4Value[self.filterIndex] + ".Window" + self.prop4Value[self.filterIndex] + "(" + str(nFilter+1) + ")")
                hres = np.multiply(hres, np.pad(win, (len(hres)-len(win)), constant_values=(1, 1)))
            #elif self.modelState == "H(s)":
            #    hres = np.subtract(np.divide(np.sin(np.multiply(np.pi, k)), np.multiply(np.pi, k)), np.divide(np.sin(np.multiply(phic, k)), np.multiply(np.pi, k)))
            #    hres[int((len(hres)-1) / 2)] = 1 - phic / np.pi
            Hzf = np.fft.fft(hres, n=2*len(self.transferModel.get_xdata()))
            Hzf = Hzf[1:int(len(Hzf)/2)+1]
            self.transferModel.set_ydata(np.divide(abs(Hzf), abs(Hzf)[self.normIndex[self.filterIndex]]))
            self.phaseModel.set_ydata(np.angle(Hzf))
        elif curFilter == "Low pass filter 2nd order":
            # Catch case of f_c=0
            if self.prop1Value[self.filterIndex] == 0:
                self.transferModel.set_visible(False)
                self.phaseModel.set_visible(False)
                return
            hlpf = None
            if self.modelState == "H(z)":
                hlpf = np.divide(1, np.power(np.add(1, np.multiply(self.proc/(2*np.pi*self.prop1Value[self.filterIndex]), np.subtract(1, np.exp(np.multiply(-2*np.pi*1j/self.proc, self.f1))))), 2))
            elif self.modelState == "H(s)":
                hlpf = np.divide(1, np.power(np.add(1, np.multiply(1j/self.prop1Value[self.filterIndex], self.f1)), 2))
            hlpf = np.divide(hlpf, np.abs(hlpf[self.normIndex[self.filterIndex]]))
            self.transferModel.set_ydata(abs(hlpf))
            self.phaseModel.set_ydata(np.angle(hlpf))
        elif curFilter == "Low pass filter 3rd order":
            # Catch case of f_c=0
            if self.prop1Value[self.filterIndex] == 0:
                self.transferModel.set_visible(False)
                self.phaseModel.set_visible(False)
                return
            hlpf = None
            if self.modelState == "H(z)":
                hlpf = np.divide(1, np.power(np.add(1, np.multiply(self.proc/(2*np.pi*self.prop1Value[self.filterIndex]), np.subtract(1, np.exp(np.multiply(-2*np.pi*1j/self.proc, self.f1))))), 3))
            elif self.modelState == "H(s)":
                hlpf = np.divide(1, np.power(np.add(1, np.multiply(1j/self.prop1Value[self.filterIndex], self.f1)), 3))
            hlpf = np.divide(hlpf, np.abs(hlpf[self.normIndex[self.filterIndex]]))
            self.transferModel.set_ydata(abs(hlpf))
            self.phaseModel.set_ydata(np.angle(hlpf))
        elif curFilter == "Programmable IIR filter":
            self.transferModel.set_visible(False)
            self.phaseModel.set_visible(False)
        if curFilter != "Programmable IIR filter":
            if self.modelState != "Disabled":
                self.transferModel.set_visible(True)
                if self.phaseState == "Enabled":
                    self.phaseModel.set_visible(True)
    
    # Function to check and possibly restore serial connection
    def checkConnection(self):
        # Prepare for restoring settings on reconnect
        if self.port.disconnected() and not self.disconnected:
            self.disconnected = True
            self.reactivate = self.reading
            self.reading = False
            self.controlFrame.grid_forget()
            self.waitLabel.configure(text="Connection Lost")
            self.waitLabel.grid(row=0, column=0, columnspan=2, sticky="WE")
            self.window.update_idletasks()
        elif self.disconnected and self.port.disconnected():
            self.window.update_idletasks()
        # Restore settings on reconnect
        if self.disconnected and not self.port.disconnected():
            self.updateAll(False)
            self.waitLabel.grid_forget()
            L.buildUI(self.uiElements, self.uiGridParams)
            # Display correct filter parameters
            self.handle_updateFilter()
            self.window.update_idletasks()
            self.disconnected = False
            if self.reactivate:
                self.handle_switchRead()
        if not self.reading:
            self.window.after(10, self.checkConnection)
    
    # Function that handles reading and displaying data from the serial port
    def readDisp(self):
        self.busy = True
        self.checkConnection()
        # Do nothing if the button to start the program hasn"t been pressed yet or the port is being initialized
        if not self.reading:
            self.busy = False
            return
        # Read data from the serial port (if enough is available)
        # Issue command to board to send data
        if self.readNext:
            time.sleep(0.005)
            self.port.writeL("send data")
            self.readNext = False
        #L.pln("trying to read")
        # Read raw values
        rawValues = self.port.readB(self.dataSize*4)
        # Only process data, if there was any read
        if rawValues != None and rawValues != "not enough data":
            #lastTime = time.time()
            # Discard any extra data on the port
            self.port.clearBuffer()
            # Prepare for next read
            self.readNext = True
            values = list(struct.unpack("%df" %self.dataSize, rawValues))
            # Possibly subtract average
            if self.subtract.get() == "Enabled":
                values = np.subtract(values, np.average(values))
            # Store the values to the data buffer
            self.data = values
            # Shift the first value to the end - this is not necessary
            #self.data = self.data[1:len(self.data)] + [self.data[0]]
            #self.data = self.data[1:len(self.data)]
            #self.data = np.pad(self.data, (0, 1))
            # Debug test for values that are clearly out of range
            if max(np.abs(self.data)) > 100:
                L.p("There was a misread: ")
                L.pln(max(np.abs(self.data)))
                L.pln(values)
                L.pln(rawValues)
                self.handle_switchRead()
            # Multiply with window functions
            for f in self.windowFiles:
                exec("import " + f[0:len(f)-3])
            win1, m1m2s1 = eval(self.winFunc1 + "(" + str(self.dataSize) + ")")
            win2, m1m2s2 = eval(self.winFunc2 + "(" + str(self.dataSize) + ")")
            self.enbw1 = m1m2s1 * self.samplerate / self.oversamples
            self.enbw2 = m1m2s2 * self.samplerate / self.oversamples
            # Mulitply data with respective window function
            x1 = np.multiply(self.data, win1)
            x2 = np.multiply(self.data, win2)
            # Compute fourier transforms
            #X1 = np.multiply(np.fft.fft(x1)[0:self.freqs1], 2/self.dataSize)
            #X2 = np.multiply(np.fft.fft(x2)[0:self.freqs1], 2/self.dataSize)
            X1 = np.multiply(np.fft.fft(x1, n=(self.transformSize1) * 2)[0:self.freqs1], 2/self.dataSize)
            X2 = np.multiply(np.fft.fft(x2, n=(self.transformSize2) * 2)[0:self.freqs2], 2/self.dataSize)
            #L.pln(abs(np.fft.fft(x1)))
            #L.pln(abs(np.fft.fft(x1, n=(self.transformSize1 - 1) * 2)))
            #L.pln()
            # Possibly omit zero frequency
            if not self.spectral:
                X1 = X1[1:len(X1)]
                X2 = X2[1:len(X2)]
            # Possibly average spectra and possibly calculate phases
            if self.averaging.get():
                if not self.spectral:
                    self.voltagePre = np.add(self.voltagePre, self.data)
                else:
                    self.voltagePre = self.data
                self.S1Pre += abs(X1)
                self.S2Pre += abs(X2)
                self.phase1Pre += np.angle(X1)
                self.phase2Pre += np.angle(X2)
                self.averaged += 1
            else:
                self.voltagePre = self.data
                self.S1Pre = abs(X1)
                self.S2Pre = abs(X2)
                self.phase1Pre = np.angle(X1)
                self.phase2Pre = np.angle(X2)
                self.averaged = 1
            # Display the values
            if not self.spectral:
                self.voltage.set_ydata(np.divide(self.voltagePre, self.averaged))
            else:
                self.voltage.set_ydata(self.voltagePre)
            # Multiply based on the selected unit
            self.handle_updateUnit()
            # Update the canvas for the time series
            L.updateCanvas(self.fig1.canvas, self.ax1, False, True)
            #lastTime = time.time()
            #L.pln(time.time()-lastTime)
            # Update the legends
            # extract range to integrate over and average
            powSpec = np.divide(self.S1Pre[self.startFindex:self.endFindex+1], self.averaged)
            power = sum(np.multiply(np.power(powSpec, 2), self.samplerate/(self.enbw1 * self.dataSize)))
            # List of all plots for the legend
            self.plots = []
            # List of all plot titles
            self.plotTitles = []
            if self.window1.get() != "Disabled":
                # Calculate and display main peak
                S1 = self.spectrum1.get_ydata()
                peakIndex = np.argmax(S1)
                peakF = self.f1[peakIndex]
                peak = S1[peakIndex]
                self.maxAnnotation1.remove()
                self.maxAnnotation1 = self.ax2.annotate("Peak\nf: " + L.fstr(peakF, 2) +"\ny: " + L.fstr(peak, 3), 
                    xy=(peakF, peak), xytext=(-50, 15),
                    textcoords='offset points',
                    bbox=dict(alpha=0.5, fc="b"),
                    arrowprops=dict(arrowstyle='->')
                )
                # Add first spectrum to the legend
                self.plots += [self.spectrum1]
                self.plotTitles += [self.window1.get() + " window, ENBW: " + L.fstr(self.enbw1, 3) + "Hz"]
                # Possibly update phase 1 and add it to the legend
                if self.phaseState == "Enabled":
                    self.phase1.set_ydata(np.divide(self.phase1Pre, self.averaged))
                    self.plots += [self.phase1]
                    self.plotTitles += [self.window1.get() + " window phase"]
            if self.window2.get() != "Disabled":
                # Calculate and display main peak
                S2 = self.spectrum2.get_ydata()
                peakIndex = np.argmax(S2)
                peakF = self.f2[peakIndex]
                peak = S2[peakIndex]
                self.maxAnnotation2.remove()
                self.maxAnnotation2 = self.ax2.annotate("Peak\nf: " + L.fstr(peakF, 2) + "\ny: " + L.fstr(peak, 3), 
                    xy=(peakF, peak), xytext=(10, 15),
                    textcoords='offset points',
                    bbox=dict(alpha=0.5, fc="r"),
                    arrowprops=dict(arrowstyle='->')
                )
                # Add second spectrum to the legend
                self.plots += [self.spectrum2]
                self.plotTitles += [self.window2.get() + " window, ENBW: " + L.fstr(self.enbw2, 3) + "Hz"]
                # Possibly update phase 2 and add it to the legend
                if self.phaseState == "Enabled":
                    self.phase2.set_ydata(np.divide(self.phase2Pre, self.averaged))
                    self.plots += [self.phase2]
                    self.plotTitles += [self.window2.get() + " window phase"]
            if self.powerState.get() != "Disabled":
                # Add power integrator to the legend
                self.plots += [self.dots]
                self.plotTitles += ["Total power in selected band: " + L.fstr(power, 5) + "V$^2$"]
            if self.modelState != "Disabled":
                self.plots += [self.transferModel]
                self.plotTitles += ["Modeled transfer function (" + self.modelState + ")"]
                if self.phaseState != "Disabled":
                    self.plots += [self.phaseModel]
                    self.plotTitles += ["Modeled phase"]
            # Draw the legends
            if self.phaseState == "Enabled":
                self.legendSpectra = self.ax3.legend(self.plots, self.plotTitles, loc='upper right', title="Averaged spectra: " + L.fstr(self.averaged))
                # Update the canvas for the phases
                L.updateCanvas(self.fig2.canvas, self.ax3, False, True)
            else:
                self.legendSpectra = self.ax2.legend(self.plots, self.plotTitles, loc='upper right', title="Averaged spectra: " + L.fstr(self.averaged))
            # Legend for time series
            if not self.spectral:
                self.legendImpulse = self.ax1.legend(loc="upper right", title="Averaged impulse responses: " + L.fstr(self.averaged))
        self.window.update_idletasks()
        # Reschedule function (this is probably not the best solution)
        self.window.after(0, self.readDisp)
        self.busy = False

    # Callback for read switch
    def handle_switchRead(self, event=None):
        if self.reading:
            self.reading = False
            self.readSwitch['text'] = "Run                "
            self.readLabel['text'] = "Paused"
            self.window.update_idletasks()
        else:
            self.window.after(0, self.readDisp)
            self.readSwitch['text'] = "           Pause"
            self.readLabel['text'] = "Running"
            self.window.update_idletasks()
            self.reading = True
            self.readNext = True
    
    # Callback for the stop button
    def stop(self, event):
        self.window.destroy()
    
    # Callback function for changing the power integrator state to "Disabled"
    def handle_disablePower(self, event=None):
        self.startFEntry["state"] = DISABLED
        self.endFEntry["state"] = DISABLED
        self.dots.set_visible(False)

    # Callback function for changing the power integrator state to "Enabled"
    def handle_enablePower(self, event=None):
        self.startFEntry["state"] = NORMAL
        self.endFEntry["state"] = NORMAL
        self.dots.set_visible(True)
    
    # Event handler for start frequency entry box
    def handle_updateStartF(self, event=None):
        # Check if value is a float
        try:
            newStart = float(self.startFEntry.get())
            # Make sure the input is in the input range
            if newStart < 0:
                newStart = 0
            if newStart > self.endF:
                newStart = self.endF
            # Update variable for the start frequency
            self.startF = newStart
        except ValueError:
            pass
        self.startFV.set(self.startF)
        # Update index
        self.startFindex = int(self.startF * (self.freqs1 - 1) / self.f1[-1])
        # Possibly omit zero frequency
        if not self.spectral:
            self.startFindex -= 1
        # Update values in the plot
        self.dots.set_xdata([self.startF, self.endF])
    
    # Event handler for start frequency entry box
    def handle_updateEndF(self, event=None):
        # Check if value is a float
        try:
            newEnd = float(self.endFEntry.get())
            # Make sure the input is in the input range
            if newEnd < self.startF:
                newEnd = self.startF
            if newEnd > self.f1[-1]:
                newEnd = self.f1[-1]
            # Update variable for the start frequency
            self.endF = newEnd
        except ValueError:
            pass
        self.endFV.set(self.endF)
        # Update index
        self.endFindex = int(self.endF * (self.freqs1 - 1) / self.f1[-1])
        # Possibly omit zero frequency
        if not self.spectral:
            self.endFindex -= 1
        # Update values in the plot
        self.dots.set_xdata([self.startF, self.endF])
