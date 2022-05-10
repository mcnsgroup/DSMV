# SpectralGUI includes a GUI for the spectral analysis of the oscilloscope functionality of the DSMV board
#
# Requires the Arduino sketch DisplayDSMV.ino loaded on the Teensy 4.0.
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
# 03.05.2022, ver1.5
# 
# Changelog
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
from PIL import Image, ImageTk
import struct
import time
import glob
import os
# Import custom modules
from DSMVLib import DSMVLib as L

class SpectralGUI:
    # Constructor method
    def __init__(self):
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
        self.oversamplesDefault = 1
        self.oversamples = self.oversamplesDefault
        self.samplerateDefault = 1000.0
        self.samplerate = self.samplerateDefault
        self.dataSizeDefault = 100
        self.dataSize = self.dataSizeDefault
        self.port.clearBuffer()
        # Initialize data buffer
        self.data = [0] * self.dataSize
        # List with all UI elements
        self.uiElements = []
        # List with the grid parameters of all UI elements
        self.uiGridParams = []
        # create label for version number
        self.vLabel = Label(master=self.window, text="DSMV\nEx. 05\nv1.5")
        self.uiElements.append(self.vLabel)
        self.uiGridParams.append([0, 0, 1, 1, "NS"])
        # create frame for controls
        self.controlFrame = Frame()
        self.uiElements.append(self.controlFrame)
        self.uiGridParams.append([0, 1, 1, 2, "WE"])
        self.controlFrame.columnconfigure((0, 1), weight=1)
        # create frame for the data settings
        self.dataFrame = Frame(master=self.controlFrame, relief=RIDGE, borderwidth=2)
        self.uiElements.append(self.dataFrame)
        self.uiGridParams.append([0, 0, 1, 1, "WE"])
        self.dataFrame.rowconfigure(1, weight=1)
        self.dataFrame.columnconfigure(0, weight=1)
        # Create Label for data settings
        self.dataLabel = Label(master=self.dataFrame, text="Data settings")
        self.uiElements.append(self.dataLabel)
        self.uiGridParams.append([0, 0, 1, 1, ""])
        # Create frame for the individual labels and entry boxes
        self.dataSFrame = Frame(master=self.dataFrame, relief=RIDGE, borderwidth=2)
        self.uiElements.append(self.dataSFrame)
        self.uiGridParams.append([1, 0, 1, 1, "NESW"])
        self.dataSFrame.columnconfigure(1, weight=1)
        # Initialize input source
        self.source = "AD4020"
        # Create label for the source selector
        self.sourceLabel = Label(master=self.dataSFrame, text="Input source")
        self.uiElements.append(self.sourceLabel)
        self.uiGridParams.append([0, 0, 1, 1, "E"])
        # List of different Input sources
        sourceList = ["AD4020", "LTC2500", "Internal ADC"]
        # Create combo box for input source selector
        self.sourceSelect = ttk.Combobox(master=self.dataSFrame, values = sourceList, state="readonly")
        self.uiElements.append(self.sourceSelect)
        self.uiGridParams.append([0, 1, 1, 1, "WE"])
        self.sourceSelect.bind('<<ComboboxSelected>>', self.handle_updateSource)
        self.sourceSelect.set(sourceList[0])
        # Create label for the oversamples entry box
        self.oversLabel = Label(master=self.dataSFrame, text="Number of oversamples")
        self.uiElements.append(self.oversLabel)
        self.uiGridParams.append([1, 0, 1, 1, "E"])
        # Variable to control content of the oversamples entry box
        self.oversamplesV = StringVar()
        self.oversamplesV.set(str(self.oversamples))
        # Create oversamples entry box
        self.oversEntry = Entry(master=self.dataSFrame, textvariable=self.oversamplesV, justify=RIGHT)
        self.uiElements.append(self.oversEntry)
        self.uiGridParams.append([1, 1, 1, 1, "WE"])
        self.oversEntry.bind("<Return>", self.handle_updateOvers)
        # Minimum oversamples
        self.oversMin = 1
        # Maximum oversamples
        self.oversMax = 256
        # Create label for the data size entry box
        self.sizeLabel = Label(master=self.dataSFrame, text="Number of data points")
        self.uiElements.append(self.sizeLabel)
        self.uiGridParams.append([2, 0, 1, 1, "E"])
        # Variable to control content of the data size entry box
        self.dataSizeV = StringVar()
        self.dataSizeV.set(str(self.dataSize))
        # Create data size entry box
        self.sizeEntry = Entry(master=self.dataSFrame, textvariable=self.dataSizeV, justify=RIGHT)
        self.uiElements.append(self.sizeEntry)
        self.uiGridParams.append([2, 1, 1, 1, "WE"])
        self.sizeEntry.bind("<Return>", self.handle_updateSize)
        # Minimum data size
        self.dataSizeMin = 1
        # Maximum data size
        self.dataSizeMax = 32768
        # Create label for the samplerate entry box
        self.freqLabel = Label(master=self.dataSFrame, text="Samplerate (Hz)")
        self.uiElements.append(self.freqLabel)
        self.uiGridParams.append([3, 0, 1, 1, "E"])
        # Variable to control content of the samplerate entry box
        self.samplerateV = StringVar()
        self.samplerateV.set(str(self.samplerate))
        # Create samplerate entry box
        self.freqEntry = Entry(master=self.dataSFrame, textvariable=self.samplerateV, justify=RIGHT)
        self.uiElements.append(self.freqEntry)
        self.uiGridParams.append([3, 1, 1, 1, "WE"])
        self.freqEntry.bind("<Return>", self.handle_updateFreq)
        # Minimum data size
        self.samplerateMin = 1
        # Maximum data size
        self.samplerateMax = 90000
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
        self.displaySFrame.columnconfigure((1, 2), weight=1)
        # Number of averaged spectra
        self.averaged = 1
        # Initialize averaging state
        self.averaging = BooleanVar()
        self.averaging.set(False)
        # Create label for the averaging selector
        self.averagingLabel = Label(master=self.displaySFrame, text="Spectrum")
        self.uiElements.append(self.averagingLabel)
        self.uiGridParams.append([0, 0, 1, 1, "E"])
        # Create averaging selector buttons
        self.singleButton = Radiobutton(self.displaySFrame, text="Single", variable = self.averaging, value = False)
        self.uiElements.append(self.singleButton)
        self.uiGridParams.append([0, 1, 1, 1, "E"])
        self.averagedButton = Radiobutton(self.displaySFrame, text="Averaged", variable = self.averaging, value = True)
        self.uiElements.append(self.averagedButton)
        self.uiGridParams.append([0, 2, 1, 1, "W"])
        # Initialize y-scale state
        self.yscale = StringVar()
        self.yscale.set("Logarithmic")
        # Create label for the y-scale selector
        self.yscaleLabel = Label(master=self.displaySFrame, text="Y-scale (Spectrum)")
        self.uiElements.append(self.yscaleLabel)
        self.uiGridParams.append([1, 0, 1, 1, "E"])
        # Create y-scale selector buttons
        self.logButton = Radiobutton(self.displaySFrame, text="Logarithmic", variable = self.yscale, value = "Logarithmic")
        self.uiElements.append(self.logButton)
        self.uiGridParams.append([1, 1, 1, 1, "E"])
        self.logButton.bind("<Button-1>", self.handle_logScale)
        self.linButton = Radiobutton(self.displaySFrame, text="Linear", variable = self.yscale, value = "Linear")
        self.uiElements.append(self.linButton)
        self.uiGridParams.append([1, 2, 1, 1, "W"])
        self.linButton.bind("<Button-1>", self.handle_linScale)
        # Create label for the window selectors
        self.windowLabel = Label(master=self.displaySFrame, text="Windows")
        self.uiElements.append(self.windowLabel)
        self.uiGridParams.append([2, 0, 1, 1, "E"])
        # Create list of available window functions
        pathFiles=sorted(glob.glob(self.dir + "Window*.py"))
        self.windowFiles = [os.path.basename(f) for f in pathFiles]
        for f in self.windowFiles:
            exec("import " + f[0:len(f)-3])
        self.windows = [wf[6:len(wf)-3] for wf in self.windowFiles]
        func = self.windowFiles[0]
        self.winFunc1 = func[0:len(func)-3] + "." + func[0:len(func)-3]
        self.winFunc2 = func[0:len(func)-3] + "." + func[0:len(func)-3]
        # Variables for the current windows
        self.window1 = StringVar()
        self.window2 = StringVar()
        self.window1.set(self.windows[0])
        self.window2.set(self.windows[0])
        # Create combo box for window selector 1
        self.windowSelect1 = ttk.Combobox(master=self.displaySFrame, values = self.windows, textvariable=self.window1, state="readonly")
        self.uiElements.append(self.windowSelect1)
        self.uiGridParams.append([2, 1, 1, 1, "WE"])
        self.windowSelect1.bind('<<ComboboxSelected>>', self.handle_updateWindow1)
        # Create combo box for window selector 2
        self.windowSelect2 = ttk.Combobox(master=self.displaySFrame, values = self.windows, textvariable=self.window2, state="readonly")
        self.uiElements.append(self.windowSelect2)
        self.uiGridParams.append([2, 2, 1, 1, "WE"])
        self.windowSelect2.bind('<<ComboboxSelected>>', self.handle_updateWindow2)
        # Create label for the spectrum unit selector
        self.unitLabel = Label(master=self.displaySFrame, text="Spectrum unit")
        self.uiElements.append(self.unitLabel)
        self.uiGridParams.append([3, 0, 1, 1, "E"])
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
        self.unitSelect = ttk.Combobox(master=self.displaySFrame, values = self.unitList, state="readonly")
        self.uiElements.append(self.unitSelect)
        self.uiGridParams.append([3, 1, 1, 2, "WE"])
        self.unitSelect.bind('<<ComboboxSelected>>', self.handle_updateUnit)
        self.unitSelect.set(self.unitList[0])
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
        # Create label for the read switch
        self.readLabel = Label(master=self.runSFrame, text="Reading")
        self.uiElements.append(self.readLabel)
        self.uiGridParams.append([0, 0, 1, 1, ""])
        # Create read switch
        self.readSwitch = Button(master=self.runSFrame, text="Pause              ")
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
        self.ax1 = self.fig1.add_subplot(111)
        self.ax1.set_xlabel("Time (s)")
        self.ax1.set_ylabel("Voltage AD4020 (V)")
        # Set time axis limits to match data
        self.ax1.set_xlim([0, tMax])
        self.voltage, = self.ax1.plot(self.x, self.data, 'b-')
        canvas1 = FigureCanvasTkAgg(self.fig1)
        canvas1.draw()
        self.uiElements.append(canvas1.get_tk_widget())
        self.uiGridParams.append([1, 0, 1, 2, "NESW"])
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
            # save the data as text
            f = open(path + ".txt", mode = "w")
            f.write(str(self.data[0]))
            f.close
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
        self.freqs = int(np.ceil((self.dataSize+1)/2))
        # Create values for frequency axis
        self.f = np.linspace(0, fMax, self.freqs)
        self.ax2 = self.fig2.add_subplot(111)
        self.ax2.set_xlabel("Frequency (Hz)")
        self.ax2.set_ylabel(self.psdLabel)
        # Set frequency axis limits to match data
        self.ax2.set_xlim([0, fMax])
        # Create arrays to hold current spectra (pre scaling)
        self.S1Pre = [0] * self.freqs
        self.S2Pre = [0] * self.freqs
        # ENBWs of the current spectra
        self.enbw1 = 0
        self.enbw2 = 0
        # Create spectra
        self.spectrum1, = self.ax2.plot(self.f, self.S1Pre, 'b-', label=self.windows[0] + " window, ENBW: 0Hz")
        self.spectrum2, = self.ax2.plot(self.f, self.S2Pre, 'r-', label=self.windows[0] + " window, ENBW: 0Hz")
        self.ax2.set_yscale("log")
        self.legend = self.ax2.legend(loc='upper right', title="Averaged spectra: 1")
        canvas2 = FigureCanvasTkAgg(self.fig2)
        canvas2.draw()
        self.uiElements.append(canvas2.get_tk_widget())
        self.uiGridParams.append([2, 0, 1, 2, "NESW"])
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
            self.fig1.savefig(path + ".svg")
            # save the data as text
            f = open(path + ".txt", mode = "w")
            f.write(str(self.data[0]))
            f.close
            # display the saved message
            self.saveLabel1.configure(text="Saved as " + path + "!")
            # schedule message removal
            self.window.after(2000, lambda: self.saveLabel1.configure(text=""))
        self.saveButton2.bind("<Button-1>", updateSaveLabel2)
        toolbar2 = L.VerticalPlotToolbar(canvas2, self.saveFrame2)
        toolbar2.update()
        toolbar2.pack_forget()
        self.uiElements.append(toolbar2)
        self.uiGridParams.append([2, 0, 1, 1, "NW"])
        self.waitLabel = Label(text="Initializing... ",
                               font=("", 100))
        self.updateAll(True)
        # Display the widgets
        L.buildUI(self.uiElements, self.uiGridParams)
        # Maximize the window
        self.window.attributes("-zoomed", True)
        # Start the reading thread
        self.port.start(maxSize=self.dataSizeMax*4)
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
        self.handle_updateOvers()
        time.sleep(0.005)
        self.waitLabel.configure(text=pre + "|")
        self.window.update_idletasks()
        self.handle_updateSize()
        time.sleep(0.005)
        self.waitLabel.configure(text=pre + "/")
        self.window.update_idletasks()
        self.handle_updateFreq()
        time.sleep(0.005)
        self.waitLabel.configure(text=pre + "-")
        self.window.update_idletasks()
        self.handle_updateSource()
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
        self.port.writeL('activate ' + str(self.sourceSelect.get()))
        self.port.clearBuffer()
        self.resetYSpectra()

    # Event handler for oversamples entry box
    def handle_updateOvers(self, event=0):
        # Stop reading during update
        reactivate = False
        if self.reading:
            reactivate = True
            self.reading = False
        # Make sure the input is an integer
        if self.oversEntry.get().isdigit():
            newOvers = int(self.oversEntry.get())
            # Make sure the input is in the input range
            if newOvers < self.oversMin:
                newOvers = self.oversMin
            if newOvers > self.oversMax:
                newOvers = self.oversMax
            # Update variable for oversamples
            self.oversamples = newOvers
            # Write command to serial port
            self.port.writeL('set oversamples ' + str(self.oversamples))
            # Update the time axes
            self.updateAxes()
            # Clear serial buffer
            self.port.clearBuffer()
        self.oversamplesV.set(str(self.oversamples))
        self.window.update_idletasks()
        # Reactivate reading if paused by this function
        if reactivate:
            self.reading = True
            self.window.after(0, self.readDisp)

    # Event handler for data size entry box
    def handle_updateSize(self, event=0):
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
            if newSize < self.dataSize:
                self.data = self.data[self.dataSize-newSize:self.dataSize]
                #self.data[1] = self.data[1][self.dataSize-newSize:self.dataSize]
            else:
                self.data = [0]*(newSize - self.dataSize) + self.data
                #self.data[1] = [0]*(newSize - self.dataSize) + self.data[1]
            # Update variable for data size
            self.dataSize = newSize
            # Write command to serial port
            self.port.writeL('set dataSize ' + str(self.dataSize))
            self.updateAxes()
            # Clear serial buffer
            self.port.clearBuffer()
        self.dataSizeV.set(str(self.dataSize))
        self.window.update_idletasks()
        # Reactivate reading if paused by this function
        if reactivate:
            self.reading = True
            self.window.after(0, self.readDisp)
    
    # Event handler for samplerate entry box
    def handle_updateFreq(self, event=0):
        # Stop reading during update
        reactivate = False
        if self.reading:
            reactivate = True
            self.reading = False
        # Make sure the input is a number
        try:
            newSamplerate = float(self.freqEntry.get())
            # Make sure the input is in the input range
            if newSamplerate < self.samplerateMin:
                newSamplerate = self.samplerateMin
            if newSamplerate > self.samplerateMax:
                newSamplerate = self.samplerateMax
            # Update variable for samplerate
            self.samplerate = newSamplerate
            # Write command to serial port
            self.port.writeL('set samplerate ' + str(self.samplerate))
            # Update the time axes
            self.updateAxes()
            # Clear serial buffer
            self.port.clearBuffer()
        except ValueError:
            pass
        self.samplerateV.set(str(self.samplerate))#
        self.window.update_idletasks()
        # Reactivate reading if paused by this function
        if reactivate:
            self.reading = True
            self.window.after(0, self.readDisp)
    
    # Reset the y-data and averaging of the spectra
    def resetYSpectra(self):
        self.S1Pre = [0] * self.freqs
        self.S2Pre = [0] * self.freqs
        self.averaged = 0
        self.spectrum1.set_ydata(self.S1Pre)
        self.spectrum2.set_ydata(self.S2Pre)
    
    # Updates the x axes for plots
    def updateAxes(self):
        # Maximum time value
        tMax = (self.dataSize-1)*self.oversamples/self.samplerate
        # Update values for time axis
        self.x = np.linspace(0, tMax, self.dataSize)
        # Maximum frequency value
        fMax = self.samplerate/(2 * self.oversamples)
        # Number of frequencies
        self.freqs = int(np.ceil((self.dataSize+1)/2))
        # Update values for frequency axis
        self.f = np.linspace(0, fMax, self.freqs)
        # Update the axes data
        self.voltage.set_xdata(self.x)
        self.spectrum1.set_xdata(self.f)
        self.spectrum2.set_xdata(self.f)
        self.voltage.set_ydata(self.data)
        self.resetYSpectra()
        # Set time axes scale
        self.ax1.set_xlim([0, tMax])
        # Set frequency axis limits to match data
        self.ax2.set_xlim([0, fMax])
        # Update the canvases
        L.updateCanvas(self.fig1.canvas, self.ax1, False, True)
        L.updateCanvas(self.fig2.canvas, self.ax2, False, True)
    
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
        self.winFunc1 = "Window" + self.window1.get() + "." + "Window" + self.window1.get()
        self.resetYSpectra()
    
    # Event handler for window selector 1
    def handle_updateWindow2(self, event=0):
        self.winFunc2 = "Window" + self.window2.get() + "." + "Window" + self.window2.get()
        self.resetYSpectra()
    
    # Event handler for spectrum unit selector (also used by readDisp)
    def handle_updateUnit(self, event=0):
        self.ax2.set_ylabel(self.unitLabels[self.unitList.index(self.unitSelect.get())])
        if self.unitSelect.get() == "Power Spectral Density":
            S1 = np.divide(np.power(self.S1Pre, 2), (self.averaged * self.enbw1))
            S2 = np.divide(np.power(self.S2Pre, 2), (self.averaged * self.enbw2))
        elif self.unitSelect.get() == "Power Spectrum":
            S1 = np.divide(np.power(self.S1Pre, 2), self.averaged)
            S2 = np.divide(np.power(self.S2Pre, 2), self.averaged)
        elif self.unitSelect.get() == "Amplitude Spectral Density":
            S1 = np.divide(self.S1Pre, (self.averaged * np.sqrt(self.enbw1)))
            S2 = np.divide(self.S2Pre, (self.averaged * np.sqrt(self.enbw2)))
        elif self.unitSelect.get() == "Amplitude Spectrum":
            S1 = np.divide(self.S1Pre, self.averaged)
            S2 = np.divide(self.S2Pre, self.averaged)
        self.spectrum1.set_ydata(S1)
        self.spectrum2.set_ydata(S2)
        # Update the canvas for the spectra
        L.updateCanvas(self.fig2.canvas, self.ax2, False, True)
    
    # Function that handles reading and displaying data from the serial port
    def readDisp(self):
        # Prepare for restoring settings on reconnect
        if self.port.disconnected() and not self.disconnected:
            self.disconnected = True
            self.reactivate = self.reading
            self.reading = False
            self.controlFrame.grid_forget()
            self.waitLabel.configure(text="Connection Lost")
            self.waitLabel.grid(row=0, column=0, columnspan=2, sticky="WE")
            self.window.update_idletasks()
            self.window.after(0, self.readDisp)
        elif self.disconnected and self.port.disconnected():
            self.window.update_idletasks()
            self.window.after(0, self.readDisp)
        # Restore settings on reconnect
        if self.disconnected and not self.port.disconnected():
            time.sleep(0.01)
            self.updateAll(False)
            L.buildUI(self.uiElements, self.uiGridParams)
            self.window.update_idletasks()
            self.disconnected = False
            self.reading = self.reactivate
        # Do nothing if the button to start the program hasn't been pressed yet or the port is bein initialized
        if not self.reading:
            return
        # Read data from the serial port (if enough is available)
        # Read raw values
        rawValues = self.port.readB(self.dataSize*4)
        # Only process data, if there was any read
        if rawValues != None and rawValues != "not enough data":
            values = list(struct.unpack("%df" %self.dataSize, rawValues))
            # Store the different parts to the different sub arrays of the data buffer
            self.data = values#[0:self.dataSize]
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
            X1 = np.multiply(np.fft.fft(x1)[0:self.freqs], 2/self.dataSize)
            X2 = np.multiply(np.fft.fft(x2)[0:self.freqs], 2/self.dataSize)
            # Possibly average spectra
            if self.averaging.get():
                self.S1Pre += abs(X1)
                self.S2Pre += abs(X2)
                self.averaged += 1
            else:
                self.S1Pre = abs(X1)
                self.S2Pre = abs(X2)
                self.averaged = 1
            # Display the values
            self.voltage.set_ydata(self.data)
            # Multiply based on the selected unit
            self.handle_updateUnit()
            # Update the canvas for the time series
            L.updateCanvas(self.fig1.canvas, self.ax1, False, True)
            # Update the legends
            self.legend = self.ax2.legend([self.window1.get() + " window, ENBW: %.3fHz" %self.enbw1, 
                                            self.window2.get() + " window, ENBW: %.3fHz" %self.enbw2],
                                            loc='upper right', title="Averaged spectra: %d" %self.averaged)
            #L.pln(time.time()-lastTime)
        self.window.update_idletasks()
        # Reschedule function (this is probably not the best solution)
        self.window.after(0, self.readDisp)

    # Callback for read switch
    def handle_switchRead(self, event):
        if self.reading:
            self.reading = False
            self.readSwitch['text']="Pause              "
            self.window.update_idletasks()
        else:
            self.port.clearBuffer()
            self.readSwitch['text']="                Run"
            self.window.update_idletasks()
            self.reading = True
            self.window.after(0, self.readDisp)
    
    # Callback for the stop button
    def stop(self, event):
        self.window.destroy()
