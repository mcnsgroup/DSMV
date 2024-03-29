# SpectralGUI includes a GUI for the spectral analysis of the oscilloscope functionality of the DSMV board
#
# Requires the Arduino sketch DisplayDSMVGenerate.ino loaded on the Teensy 4.0.
# 
# There are two spectra being displayed,
# one for each of the selectable filter windows.
# The filter windows can be added externally with the following
# convention:
# File name:
#   Window[Name of the window].m, eg. WindowBlackman.m
# Inputs:
#   N: length of the window
# Returns:
#   window: the window as a vector
#   enbw: the enbw of the window (given by the sum of the squared
#   values divided by the square of the sum of all values)
# 
# Lukas Freudenberg (lfreudenberg@uni-osnabrueck.de)
# Philipp Rahe (prahe@uni-osnabrueck.de)
# 21.05.2023, ver1.15
# 
# Changelog
#   - 30.05.2023: N->N_s; power calculation corrected; 
#   - 21.05.2023: Corrected tooltips; modified axes limits so that zoom is maintained; 
#                 added direct calling option; 
#                 reduced to one save button; csv export optimised;
#   - 31.05.2022: Fixed a bug that caused the spectral data to not be saved properly as text file
#   - 30.05.2022: Compatibility update for new USB protocol,
#                 changed value displays to DSMVLib version
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
from csv import Dialect
from hashlib import new
import numpy as np
from matplotlib.pyplot import *
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk
import struct
import time
import glob
import os
import math
# Import custom modules
from DSMVLib import DSMVLib as L

class SpectralGUI:
    # Constructor method
    def __init__(self, drawPhase=False):
        # Initialize all components
        # Create control window
        self.window = Tk()
        L.window = self.window
        self.window.title("Spectral GUI")
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
        self.drawPhase = drawPhase
        # Initialize data buffer
        self.data = [0] * self.dataSize
        # List with all UI elements
        self.uiElements = []
        # List with the grid parameters of all UI elements
        self.uiGridParams = []
        # create label for version number
        self.vLabel = Label(master=self.window, text="DSMV\nEx. 05-07\nv1.15")
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
        self.uiGridParams.append([0, 0, 1, 1, "WE"])
        self.boardFrame.rowconfigure(1, weight=1)
        self.boardFrame.columnconfigure(0, weight=1)
        # Create Label for board settings
        self.boardLabel = Label(master=self.boardFrame, text="Board settings")
        self.uiElements.append(self.boardLabel)
        self.uiGridParams.append([0, 0, 1, 1, ""])
        # Create frame for the individual labels and entry boxes
        self.boardSFrame = Frame(master=self.boardFrame, relief=RIDGE, borderwidth=2)
        self.uiElements.append(self.boardSFrame)
        self.uiGridParams.append([1, 0, 1, 1, "NESW"])
        self.boardSFrame.columnconfigure(1, weight=1)
        # Initialize input source
        self.source = "AD4020"
        # Create label for the source selector
        self.sourceLabel = Label(master=self.boardSFrame, text="Input source")
        self.uiElements.append(self.sourceLabel)
        self.uiGridParams.append([0, 0, 1, 1, "E"])
        # List of different Input sources
        sourceList = ["AD4020", "LTC2500", "Internal ADC"]
        # Create combo box for input source selector
        self.sourceSelect = ttk.Combobox(master=self.boardSFrame, values = sourceList, state="readonly")
        self.uiElements.append(self.sourceSelect)
        self.uiGridParams.append([0, 1, 1, 1, "WE"])
        self.sourceSelect.bind('<<ComboboxSelected>>', self.handle_updateSource)
        self.sourceSelect.set(sourceList[0])
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
        self.sizeLabel = Label(master=self.boardSFrame, text="N_s")
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
        # Minimum data size
        self.procMin = 1
        # Maximum data size
        self.procMax = 80000
        # Create frame for the display settings
        self.displayFrame = Frame(master=self.controlFrame, relief=RIDGE, borderwidth=2)
        self.uiElements.append(self.displayFrame)
        self.uiGridParams.append([0, 1, 1, 1, "NESW"])
        self.displayFrame.rowconfigure(1, weight=1)
        self.displayFrame.columnconfigure(0, weight=1)
        # Create Label for display settings
        self.displayLabel = Label(master=self.displayFrame, text="Display settings")
        self.uiElements.append(self.displayLabel)
        self.uiGridParams.append([0, 0, 1, 1, ""])
        # Create frame for the individual widgets
        self.displaySFrame = Frame(master=self.displayFrame, relief=RIDGE, borderwidth=2)
        self.uiElements.append(self.displaySFrame)
        self.uiGridParams.append([1, 0, 1, 1, "NESW"])
        self.displaySFrame.columnconfigure((2, 3), weight=1)
        # Number of averaged spectra
        self.averaged = 1
        # Initialize averaging state
        self.averaging = BooleanVar()
        self.averaging.set(False)
        # Create label for the averaging selector
        self.averagingLabel = Label(master=self.displaySFrame, text="Spectrum")
        self.uiElements.append(self.averagingLabel)
        self.uiGridParams.append([0, 0, 1, 2, "E"])
        # Create frame for the averaging selector and spectral unit
        self.avgUnitFrame = Frame(master=self.displaySFrame)
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
        # List of different spectrum unit labels
        self.unitLabels = [self.psdLabel, self.psLabel, self.asdLabel, self.asLabel]
        # List of different spectrum units
        self.unitList = ["Power Spectral Density", "Power Spectrum", "Amplitude Spectral Density", "Amplitude Spectrum"]
        # Create combo box for spectrum unit selector
        self.unitSelect = ttk.Combobox(master=self.avgUnitFrame, values = self.unitList, state="readonly")
        self.uiElements.append(self.unitSelect)
        self.uiGridParams.append([0, 3, 1, 1, "WE"])
        self.unitSelect.bind('<<ComboboxSelected>>', self.handle_updateUnit)
        self.unitSelect.set(self.unitList[0])
        # Initialize y-scale state
        self.yscale = StringVar()
        self.yscale.set("Logarithmic")
        # Create label for the y-scale selector
        self.yscaleLabel = Label(master=self.displaySFrame, text="Y-scale (Spectrum)")
        self.uiElements.append(self.yscaleLabel)
        self.uiGridParams.append([1, 0, 1, 2, "E"])
        # Create frame for the y-scale selector
        self.scaleFrame = Frame(master=self.displaySFrame)
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
        self.windowLabel = Label(master=self.displaySFrame, text="Windows")
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
        self.windowSelect1 = ttk.Combobox(master=self.displaySFrame, values = self.windows, textvariable=self.window1, state="readonly")
        self.uiElements.append(self.windowSelect1)
        self.uiGridParams.append([2, 2, 1, 1, "WE"])
        self.windowSelect1.bind('<<ComboboxSelected>>', self.handle_updateWindow1)
        # Create combo box for window selector 2
        self.windowSelect2 = ttk.Combobox(master=self.displaySFrame, values = self.windows, textvariable=self.window2, state="readonly")
        self.uiElements.append(self.windowSelect2)
        self.uiGridParams.append([2, 3, 1, 1, "WE"])
        self.windowSelect2.bind('<<ComboboxSelected>>', self.handle_updateWindow2)
        # Initialize subtraction state
        self.subtract = StringVar()
        self.subtract.set("Disabled")
        # Create label for the subtraction selector
        self.subtractLabel = Label(master=self.displaySFrame, text="Subtract average")
        self.uiElements.append(self.subtractLabel)
        self.uiGridParams.append([3, 0, 1, 2, "E"])
        # Create frame for the subtraction selector
        self.subtractFrame = Frame(master=self.displaySFrame)
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
        self.NButton = Radiobutton(self.displaySFrame, text="N_FT-1=N_s/2", variable = self.transformSizeStatus, value = "N_FT-1=N/2")
        self.uiElements.append(self.NButton)
        self.uiGridParams.append([4, 0, 1, 1, "W"])
        self.NButton.bind("<Button-1>", self.handle_lockedTransform)
        self.N_FTButton = Radiobutton(self.displaySFrame, text="N_FT-1", variable = self.transformSizeStatus, value = "N_FT-1")
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
        self.transformSize1Entry = Entry(master=self.displaySFrame, textvariable=self.transformSize1V, justify=RIGHT)
        self.uiElements.append(self.transformSize1Entry)
        self.uiGridParams.append([4, 2, 1, 1, "WE"])
        self.transformSize1Entry.bind("<Return>", self.handle_updateTransformSize1)
        self.transformSize1Entry.bind("<KP_Enter>", self.handle_updateTransformSize1)
        self.transformSize1Entry.bind("<FocusOut>", self.handle_updateTransformSize1)
        self.transformSize1Entry["state"] = DISABLED
        # Create transform size 2 entry box
        self.transformSize2Entry = Entry(master=self.displaySFrame, textvariable=self.transformSize2V, justify=RIGHT)
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
        #### data plots
        # Create canvas for the time series
        self.fig1 = Figure(figsize=(5, 2), layout='constrained')
        # Maximum time value
        tMax = (self.dataSize-1)*self.oversamples/self.samplerate
        # Create values for time axis
        self.x = np.linspace(0, tMax, self.dataSize)
        self.ax1 = self.fig1.add_subplot(111)
        self.ax1.set_xlabel("Time (s)")
        self.ax1.set_ylabel("Voltage AD4020 (V)")
        # Set time axis limits to match data
        self.ax1.set_xlim([0, tMax])
        self.voltage, = self.ax1.plot(self.x, self.data, 'b.-', linewidth=0.5)
        canvas1 = FigureCanvasTkAgg(self.fig1)
        canvas1.draw()
        self.uiElements.append(canvas1.get_tk_widget())
        self.uiGridParams.append([1, 0, 1, 2, "NESW"])
        # Create data tip for the voltage
        self.dataTipVoltage = L.dataTip(canvas1, self.ax1, 0.01, line=self.voltage, faceColor="b")
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
            path = L.savePath("DSMV_data", self.dir)
            # save the image
            self.fig1.savefig(path + ".svg")
            self.fig1.savefig(path + ".png")
            self.fig2.savefig(path + "spectrum.svg")
            self.fig2.savefig(path + "spectrum.png")
            # save the time trace data as text
            outarr = None
            outarr = np.asarray([self.x, self.data])
            outarr = outarr.transpose()
            np.savetxt(path + ".csv", outarr, delimiter=",")
            # save the spectrum data as text
            outarr = None
            if self.window1.get() != "Disabled":
                if self.window2.get() != "Disabled":
                    outarr = np.asarray([self.f1, self.spectrum1.get_ydata(), self.f2, self.spectrum2.get_ydata()])
                else:
                    outarr = np.asarray([self.f1, self.spectrum1.get_ydata()])
            else:
                if self.window2.get() != "Disabled":
                    outarr = np.asarray([self.f2, self.spectrum2.get_ydata()])
                else:
                    outarr = np.asarray([])
            outarr = outarr.transpose()
            np.savetxt(path + "spectrum.csv", outarr, delimiter=",")
            self.saveLabel1.configure(text="Last file:\n " + path)
            #f = open(path + ".txt", mode = "w")
            #f.write(str(self.data))
            #f.close
            ## display the saved message
            #self.saveLabel1.configure(text="Saved as " + path + "!")
            ## schedule message removal
            #self.window.after(2000, lambda: self.saveLabel1.configure(text=""))
        self.saveButton1.bind("<Button-1>", updateSaveLabel1)
        toolbar1 = L.VerticalPlotToolbar(canvas1, self.saveFrame1)
        toolbar1.update()
        toolbar1.pack_forget()
        self.uiElements.append(toolbar1)
        self.uiGridParams.append([2, 0, 1, 1, "NW"])
        ##### data spectrum
        # Create canvas for the spectra
        self.fig2 = Figure(figsize=(5, 2), layout='constrained')
        # Maximum frequency value
        fMax = self.samplerate/(2 * self.oversamples)
        # Number of frequencies
        self.freqs1 = int(np.ceil((self.dataSize+1)/2))
        self.freqs2 = int(np.ceil((self.dataSize+1)/2))
        # Create values for frequency axis
        self.f1 = np.linspace(0, fMax, self.freqs1)
        self.f2 = np.linspace(0, fMax, self.freqs2)
        self.ax2 = self.fig2.add_subplot(111)
        self.ax2.set_xlabel("Frequency (Hz)")
        self.ax2.set_ylabel(self.psdLabel)
        # Set frequency axis limits to match data
        self.ax2.set_xlim([0, fMax])
        self.ax2lastxlim =[0, fMax]
        # Create arrays to hold current spectra (pre scaling and averaging)
        self.S1Pre = [0] * self.freqs1
        self.S2Pre = [0] * self.freqs2
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
        # Potentially create phases
        if self.drawPhase:
            # Create arrays to hold current phases (pre averaging)
            self.phase1Pre = [0] * self.freqs1
            self.phase2Pre = [0] * self.freqs2
            # Create axis for phase
            self.ax3 = self.ax2.twinx()
            self.ax3.set_ylabel('Phase')
            # Create phases
            self.phase1, = self.ax3.plot(self.f1, [0] * (self.freqs1), "b.", label=self.windows[0] + " window phase", markersize=1)
            self.phase2, = self.ax3.plot(self.f2, [0] * (self.freqs2), "r.", label=self.windows[0] + " window phase", markersize=1)
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
        # Check for phase setting
        if self.drawPhase:
            # List of all plots for the legend
            self.plots = [self.spectrum1, self.spectrum2, self.dots, self.phase1, self.phase2]
            # List of all plot titles
            self.plotTitles = [self.windows[0] + " window, ENBW: 0Hz",
                                self.windows[0] + " window, ENBW: 0Hz",
                                "Total power in selected band: 0V$^2$",
                                self.windows[0] + " window phase",
                                self.windows[0] + " window phase"]
            # Legend for frequency-phase diagram
            self.legend = self.ax3.legend(self.plots, self.plotTitles, loc="upper right", title="Averaged spectra: 1")
        else:
            # List of all plots for the legend
            self.plots = [self.spectrum1, self.spectrum2, self.dots]
            # List of all plot titles
            self.plotTitles = [self.windows[0] + " window, ENBW: 0Hz",
                                self.windows[0] + " window, ENBW: 0Hz",
                                "Total power in selected band: 0V$^2$"]
            # Legend for frequency diagram
            self.legend = self.ax2.legend(self.plots, self.plotTitles, loc="upper right", title="Averaged spectra: 1")
        # Draw the canvas
        canvas2 = FigureCanvasTkAgg(self.fig2)
        canvas2.draw()
        self.uiElements.append(canvas2.get_tk_widget())
        self.uiGridParams.append([2, 0, 1, 2, "NESW"])
        # Create data tip for spectrum 1
        self.dataTipSpectrum1 = L.dataTip(canvas2, self.ax2, 0.01, line=self.spectrum1, faceColor="b")
        # Create data tip for spectrum 2
        self.dataTipSpectrum2 = L.dataTip(canvas2, self.ax2, 0.01, line=self.spectrum2, faceColor="r")
        # Create frame for saving the plot
        self.saveFrame2 = Frame()
        self.uiElements.append(self.saveFrame2)
        self.uiGridParams.append([2, 2, 1, 1, "NW"])
        ## Create save button
        #self.saveButton2 = Button(master=self.saveFrame2, text=u"\U0001F4BE", font=("TkDefaultFont", 60))
        #self.uiElements.append(self.saveButton2)
        #self.uiGridParams.append([0, 0, 1, 1, ""])
        ## Create label to display saved message
        #self.saveLabel2 = Label(master=self.saveFrame2)
        #self.uiElements.append(self.saveLabel2)
        #self.uiGridParams.append([1, 0, 1, 1, ""])
        #def updateSaveLabel2(event):
        #    path = L.savePath("Spectrum", self.dir)
        #    # save the image
        #    self.fig2.savefig(path + ".svg")
        #    # save the data as text
        #    f = open(path + ".txt", mode = "w")
        #    f.write(str(self.data))
        #    f.close
        #    # display the saved message
        #    self.saveLabel2.configure(text="Saved as " + path + "!")
        #    # schedule message removal
        #    self.window.after(2000, lambda: self.saveLabel2.configure(text=""))
        #self.saveButton2.bind("<Button-1>", updateSaveLabel2)
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
        self.startFV.set(0)
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
        self.endFV.set(fMax)
        # Create end frequency entry box
        self.endFEntry = Entry(master=self.powerSFrame, textvariable=self.endFV, justify=RIGHT)
        self.uiElements.append(self.endFEntry)
        self.uiGridParams.append([0, 5, 1, 1, "WE"])
        self.endFEntry.bind("<Return>", self.handle_updateEndF)
        self.endFEntry.bind("<KP_Enter>", self.handle_updateEndF)
        self.endFEntry.bind("<FocusOut>", self.handle_updateEndF)
        self.waitLabel = Label(text="Initializing... ",
                               font=("", 100))
        self.handle_disablePower()
        self.updateAll(True)
        self.handle_updateWindow2()
        # Display the widgets
        L.buildUI(self.uiElements, self.uiGridParams)
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
        time.sleep(0.005)
        self.waitLabel.configure(text=pre + "|")
        self.window.update_idletasks()
        self.handle_updateSize(force=True)
        time.sleep(0.005)
        self.waitLabel.configure(text=pre + "/")
        self.window.update_idletasks()
        self.handle_updateOvers(force=True)
        time.sleep(0.005)
        self.waitLabel.configure(text=pre + "-")
        self.window.update_idletasks()
        self.handle_updateSource()
        time.sleep(0.005)
        self.waitLabel.configure(text=pre + "\\")
        self.window.update_idletasks()
        self.handle_updateProc(force=True)
        time.sleep(0.005)
        self.waitLabel.grid_forget()
    
    # Event handler for input source selector
    def handle_updateSource(self, event=0):
        self.ax1.set_ylabel("Voltage " + str(self.sourceSelect.get()) + "(V)")
        self.port.writeL('deactivate AD4020')
        time.sleep(0.1)
        self.port.writeL('deactivate LTC2500')
        time.sleep(0.1)
        self.port.writeL('deactivate Internal ADC')
        time.sleep(0.1)
        self.port.writeL('set mode ' + str(self.sourceSelect.get()))
        self.port.clearBuffer()
        self.readNext = True
        self.resetYSpectra()

    # Event handler for samplerate entry box
    def handle_updateFreq(self, event=0, force=False):
        # Make sure the input is a number
        try:
            newSamplerate = float(self.freqEntry.get())
            # Make sure the input is in the input range
            if newSamplerate < self.samplerateMin:
                newSamplerate = self.samplerateMin
            if newSamplerate > self.samplerateMax:
                newSamplerate = self.samplerateMax
            # Only update if the value has actually changed
            if newSamplerate != self.samplerate or force:
                # Update variable for samplerate
                self.samplerate = newSamplerate
                # Write command to serial port
                self.port.writeL('set samplerate ' + str(self.samplerate))
                # Update the axes
                self.updateAxes()
                # Clear serial buffer
                self.port.clearBuffer()
                self.readNext = True
        except ValueError:
            pass
        self.samplerateV.set(str(self.samplerate))
        self.window.update_idletasks()
    
    # Event handler for data size entry box
    def handle_updateSize(self, event=0, force=False):
        # Stop reading during update
        reactivate = False
        if self.reading:
            reactivate = True
            self.reading = False
        # Make sure the input is an integer
        if self.sizeEntry.get().isdigit():
            newSize = int(self.sizeEntry.get())
            # Make sure the input is in the input range
            if newSize < self.dataSizeMin:
                newSize = self.dataSizeMin
            if newSize > self.dataSizeMax:
                newSize = self.dataSizeMax
            # Only update if the value has actually changed
            if newSize != self.dataSize or force:
                if newSize < self.dataSize:
                    self.data = self.data[self.dataSize-newSize:self.dataSize]
                else:
                    self.data = np.pad(self.data, (newSize - self.dataSize, 0))
                # Update variable for data size
                self.dataSize = newSize
                # Write command to serial port
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
        self.dataSizeV.set(str(self.dataSize))
        self.window.update_idletasks()
        # Reactivate reading if paused by this function
        if reactivate:
            self.reading = True
            self.window.after(0, self.readDisp)
    
    # Event handler for oversamples entry box
    def handle_updateOvers(self, event=0, force=False):
        # Make sure the input is an integer
        if self.oversEntry.get().isdigit():
            newOvers = int(self.oversEntry.get())
            # Make sure the input is in the input range
            if newOvers < self.oversMin:
                newOvers = self.oversMin
            if newOvers > self.oversMax:
                newOvers = self.oversMax
            # Only update if the value has actually changed
            if newOvers != self.oversamples or force:
                # Update variable for oversamples
                self.oversamples = newOvers
                # Write command to serial port
                self.port.writeL('set oversamples ' + str(self.oversamples))
                # Update the axes
                self.updateAxes()
                # Clear serial buffer
                self.port.clearBuffer()
                self.readNext = True
        self.oversamplesV.set(str(self.oversamples))
        self.window.update_idletasks()
    
    # Event handler for processing rate input box
    def handle_updateProc(self, event=0, force=False):
        # Make sure the input is a number
        try:
            newProc = float(self.procEntry.get())
            # Make sure the input is in the input range
            if newProc < self.procMin:
                newProc = self.procMin
            if newProc > self.procMax:
                newProc = self.procMax
            # Only update if the value has actually changed
            if newProc != self.proc or force:
                # Update variable for samplerate
                self.proc = newProc
                # Write command to serial port
                self.port.writeL('set processing rate ' + str(self.proc))
                # Update the axes
                self.updateAxes()
                # Clear serial buffer
                self.port.clearBuffer()
                self.readNext = True
        except ValueError:
            pass
        self.procV.set(str(self.proc))
        self.window.update_idletasks()
    
    # Reset the y-data and averaging of the spectra
    def resetYSpectra(self):
        self.averaged = 0
        self.S1Pre = [0] * self.freqs1
        self.S2Pre = [0] * self.freqs2
        self.spectrum1.set_ydata(self.S1Pre)
        self.spectrum2.set_ydata(self.S2Pre)
        if self.drawPhase:
            self.phase1Pre = [0] * self.freqs1
            self.phase2Pre = [0] * self.freqs2
            self.phase1.set_ydata(self.phase1Pre)
            self.phase2.set_ydata(self.phase2Pre)
    
    # Updates the x axes for plots
    def updateAxes(self):
        # Maximum time value
        tMax = (self.dataSize-1)*self.oversamples/self.samplerate
        # get current axes limits for spectrum
        xlim2 = self.ax2.get_xlim()
        #print(self.ax2.margins())
        #print(xlim2)
        setxlim=False
        if self.ax2lastxlim[0] == xlim2[0] and self.ax2lastxlim[1] == xlim2[1]:
            setxlim=True
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
        # Update the axes data
        self.voltage.set_xdata(self.x)
        self.spectrum1.set_xdata(self.f1)
        self.spectrum2.set_xdata(self.f2)
        if self.drawPhase:
            self.phase1.set_xdata(self.f1)
            self.phase2.set_xdata(self.f2)
        self.voltage.set_ydata(self.data)
        self.resetYSpectra()
        # Update power integrator indices
        self.handle_updateStartF()
        self.handle_updateEndF()
        # Set time axes scale
        self.ax1.set_xlim([0, tMax])
        # Set frequency axis limits to match data
        if(setxlim):
            self.ax2.set_xlim([0, fMax])
            self.ax2lastxlim = [0, fMax]
            if self.drawPhase:
                self.ax3.set_xlim([0, fMax])
        # Update the canvases
        L.updateCanvas(self.fig1.canvas, self.ax1, False, True)
        L.updateCanvas(self.fig2.canvas, self.ax2, False, True)
        if self.drawPhase:
            L.updateCanvas(self.fig2.canvas, self.ax3, False, True)
    
    # Callback function for changing the y-scale to "Logarithmic"
    def handle_logScale(self, event):
        self.ax2.set_yscale("log")
        # Update the canvas for the spectra
        L.updateCanvas(self.fig2.canvas, self.ax2, False, True)

    # Callback function for changing the y-scale to "Linear"
    def handle_linScale(self, event):
        self.ax2.set_yscale("linear")
        # Update the canvas for the spectra
        L.updateCanvas(self.fig2.canvas, self.ax2, False, True)
    
    # Event handler for window selector 1
    def handle_updateWindow1(self, event=0):
        if self.window1.get() == "Disabled":
            self.spectrum1.set_visible(False)
            if self.drawPhase:
                self.phase1.set_visible(False)
            self.maxAnnotation1.set_visible(False)
        else:
            self.spectrum1.set_visible(True)
            if self.drawPhase:
                self.phase1.set_visible(True)
            self.maxAnnotation1.set_visible(True)
            self.winFunc1 = "Window" + self.window1.get() + "." + "Window" + self.window1.get()
            self.resetYSpectra()
    
    # Event handler for window selector 1
    def handle_updateWindow2(self, event=0):
        if self.window2.get() == "Disabled":
            self.spectrum2.set_visible(False)
            if self.drawPhase:
                self.phase2.set_visible(False)
            self.maxAnnotation2.set_visible(False)
        else:
            self.spectrum2.set_visible(True)
            if self.drawPhase:
                self.phase2.set_visible(True)
            self.maxAnnotation2.set_visible(True)
            self.winFunc2 = "Window" + self.window2.get() + "." + "Window" + self.window2.get()
            self.resetYSpectra()
    
    # Event handler for spectrum unit selector (also used by readDisp)
    def handle_updateUnit(self, event=0):
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
        self.spectrum1.set_ydata(S1)
        self.spectrum2.set_ydata(S2)
        self.dots.set_ydata([S1[self.startFindex], S1[self.endFindex]])
        # Update the canvas for the spectra
        L.updateCanvas(self.fig2.canvas, self.ax2, False, True)
    
    # Callback function for changing the subtraction to "Disabled"
    def handle_subDis(self, event):
        self.subtract.set("Disabled")
        # Update the axes
        self.updateAxes()
        # Clear serial buffer
        self.port.clearBuffer()
        self.readNext = True
    
    # Callback function for changing the subtraction to "Enabled"
    def handle_subEn(self, event):
        self.subtract.set("Enabled")
        # Update the axes
        self.updateAxes()
        # Clear serial buffer
        self.port.clearBuffer()
        self.readNext = True
    
    # Event handler for transform size entry box
    def handle_updateTransformSize1(self, event=0):
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
    def handle_updateTransformSize2(self, event=0):
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
        self.transformSize1Entry["state"] = NORMAL
        self.transformSize2Entry["state"] = NORMAL
        self.transformSizeStatus.set("N_FT-1")

    # Callback function for changing the y-scale to "Linear"
    def handle_lockedTransform(self, event):
        self.transformSize1Entry["state"] = DISABLED
        self.transformSize2Entry["state"] = DISABLED
        self.transformSizeStatus.set("N_FT-1=N/2")
        self.handle_updateSize(force=True)
    
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
            time.sleep(0.01)
            self.updateAll(False)
            self.waitLabel.grid_forget()
            L.buildUI(self.uiElements, self.uiGridParams)
            self.window.update_idletasks()
            self.disconnected = False
            if self.reactivate:
                self.handle_switchRead()
        if not self.reading:
            self.window.after(1, self.checkConnection)
    
    # Function that handles reading and displaying data from the serial port
    def readDisp(self):
        self.execRead = True
        self.checkConnection()
        # Do nothing if the button to start the program hasn"t been pressed yet or the port is being initialized
        if not self.reading:
            self.execRead = False
            return
        # Read data from the serial port (if enough is available)
        # Issue command to board to send data
        if self.readNext:
            self.port.writeL("send data")
            self.readNext = False
        # Read raw values
        rawValues = self.port.readB(self.dataSize*4)
        # Only process data, if there was any read
        #if isinstance(rawValues, bytes):
        #    print("{}".format(type(rawValues)))
        #    print("{}".format(len(rawValues)))
        if rawValues != None and rawValues != "not enough data": 
            #lastTime = time.time()
            # Discard any extra data on the port
            #self.port.clearBuffer()
            # Prepare for next read
            self.readNext = True
            values = list(struct.unpack("%df" %self.dataSize, rawValues))
            # Possibly subtract average
            if self.subtract.get() == "Enabled":
                values = np.subtract(values, np.average(values))
            # Store the values to the data buffer
            self.data = values
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
            X1 = np.multiply(np.fft.fft(x1, n=(self.transformSize1 - 1) * 2)[0:self.freqs1], 2/self.dataSize)
            X2 = np.multiply(np.fft.fft(x2, n=(self.transformSize2 - 1) * 2)[0:self.freqs2], 2/self.dataSize)
            # Possibly average spectra and possibly calculate phases
            if self.averaging.get():
                self.S1Pre += abs(X1)
                self.S2Pre += abs(X2)
                if self.drawPhase:
                    self.phase1Pre += np.angle(X1)
                    self.phase2Pre += np.angle(X2)
                self.averaged += 1
            else:
                self.S1Pre = abs(X1)
                self.S2Pre = abs(X2)
                if self.drawPhase:
                    self.phase1Pre = np.angle(X1)
                    self.phase2Pre = np.angle(X2)
                self.averaged = 1
            # Display the values
            self.voltage.set_ydata(self.data)
            # Multiply based on the selected unit
            self.handle_updateUnit()
            # Update the canvas for the time series
            L.updateCanvas(self.fig1.canvas, self.ax1, False, True)
            #lastTime = time.time()
            #L.pln(time.time()-lastTime)
            # Update the legends
            # extract range to integrate over and average
            powSpec = np.divide(self.S1Pre[self.startFindex:self.endFindex+1], self.averaged)
            power = sum(np.multiply(np.power(powSpec, 2), self.samplerate/(2 * self.enbw1 * (self.transformSize1 - 1) * 2)))
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
                if self.drawPhase:
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
                if self.drawPhase:
                    self.phase2.set_ydata(np.divide(self.phase2Pre, self.averaged))
                    self.plots += [self.phase2]
                    self.plotTitles += [self.window2.get() + " window phase"]
            if self.powerState.get() != "Disabled":
                # Add power integrator to the legend
                self.plots += [self.dots]
                self.plotTitles += ["Total power in selected band: " + L.fstr(power, 5) + "V$^2$"]
            # Draw the legend
            if self.drawPhase:
                self.legend = self.ax3.legend(self.plots, self.plotTitles, loc='upper right', title="Averaged spectra: " + L.fstr(self.averaged))
                # Update the canvas for the phases
                L.updateCanvas(self.fig2.canvas, self.ax3, False, True)
            else:
                self.legend = self.ax2.legend(self.plots, self.plotTitles, loc='upper right', title="Averaged spectra: " + L.fstr(self.averaged))
        self.window.update_idletasks()
        # Reschedule function (this is probably not the best solution)
        self.window.after(0, self.readDisp)

    # Callback for read switch
    def handle_switchRead(self, event=0):
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
    def handle_disablePower(self, event=0):
        self.startFEntry["state"] = DISABLED
        self.endFEntry["state"] = DISABLED
        self.dots.set_visible(False)

    # Callback function for changing the power integrator state to "Enabled"
    def handle_enablePower(self, event=0):
        self.startFEntry["state"] = NORMAL
        self.endFEntry["state"] = NORMAL
        self.dots.set_visible(True)
    
    # Event handler for start frequency entry box
    def handle_updateStartF(self, event=0):
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
        # Update values in the plot
        self.dots.set_xdata([self.startF, self.endF])
    
    # Event handler for start frequency entry box
    def handle_updateEndF(self, event=0):
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
        # Update values in the plot
        self.dots.set_xdata([self.startF, self.endF])

if __name__ == '__main__':
    gui = SpectralGUI()