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
# philipp Rahe (prahe@uni-osnabrueck.de)
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

# Import official modules
import numpy as np
from matplotlib.pyplot import *
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import *
from tkinter import ttk
import struct
import time
import os
import math
# Import custom modules
from DSMVLib import DSMVLib as L

class LockInGUI:
    # Constructor method
    def __init__(self):
        # Initialize variables defining which version of the GUI is being shown
        # Initialize all components
        # Create control window
        self.window = Tk()
        L.window = self.window
        self.window.title("Lock In GUI")
        self.window.columnconfigure(1, weight=1)
        self.window.rowconfigure((1, 2), weight=1)
        # Get file path
        self.dir = os.path.relpath(__file__)
        self.dir = self.dir[0:len(self.dir)-12]
        # Initialize the port for the Board
        self.port = 0
        try:
            self.port = L.sPort()
        except L.SerialDisconnect:
            quit()
        self.disconnected = False
        self.readNext = False
        self.reffreqDefault = 500.0
        self.reffreq = self.reffreqDefault
        self.dataSizeDefault = 10#100
        self.dataSize = self.dataSizeDefault
        self.zoomDefault = 1
        self.zoom = self.zoomDefault
        self.offsetDefault = 0.0
        self.transformSize1 = math.floor(self.dataSizeDefault / 2)
        self.transformSize2 = math.floor(self.dataSizeDefault / 2)
        self.offset = self.offsetDefault
        self.port.clearBuffer()
        self.readNext = True
        # Initialize data buffer
        self.data = [[0] * self.dataSize, [0] * self.dataSize]
        # List with all UI elements
        self.uiElements = []
        # List with the grid parameters of all UI elements
        self.uiGridParams = []
        # create label for version number
        self.vLabel = Label(master=self.window, text="DSMV\nEx. 12\nv1.3")
        self.uiElements.append(self.vLabel)
        self.uiGridParams.append([0, 0, 1, 1, "NS"])
        # create frame for controls
        self.controlFrame = Frame()
        self.uiElements.append(self.controlFrame)
        self.uiGridParams.append([0, 1, 1, 2, "WE"])
        self.controlFrame.columnconfigure((0, 1), weight=1)
        # Create tabsystem for bord settings
        self.boardTBS = ttk.Notebook(self.controlFrame)
        self.uiElements.append(self.boardTBS)
        self.uiGridParams.append([0, 0, 1, 1, "NESW"])
        # create frame for the board settings
        self.boardFrame = Frame(master=self.boardTBS)
        self.boardTBS.add(self.boardFrame, text='Acquisition and Processing')
        self.boardFrame.columnconfigure(1, weight=1)
        # Create label for the reference frequency entry box
        self.refLabel = Label(master=self.boardFrame, text="f_r (Hz)")
        self.uiElements.append(self.refLabel)
        self.uiGridParams.append([1, 0, 1, 1, "E"])
        # Variable to control content of the reference frequency entry box
        self.reffreqV = StringVar()
        self.reffreqV.set(str(self.reffreq))
        # Create reference frequency entry box
        self.refEntry = Entry(master=self.boardFrame, textvariable=self.reffreqV, justify=RIGHT)
        self.uiElements.append(self.refEntry)
        self.uiGridParams.append([1, 1, 1, 1, "WE"])
        self.refEntry.bind("<Return>", self.handle_updateRef)
        self.refEntry.bind("<KP_Enter>", self.handle_updateRef)
        self.refEntry.bind("<FocusOut>", self.handle_updateRef)
        # Minimum reference frequency
        self.refMin = 1
        # Maximum reference frequency
        self.refMax = 80000
        # Create label for the phase offset entry box
        self.offsetLabel = Label(master=self.boardFrame, text="Phase offset (°)")
        self.uiElements.append(self.offsetLabel)
        self.uiGridParams.append([4, 0, 1, 1, "E"])
        # Variable to control content of the phase offset entry box
        self.offsetV = StringVar()
        self.offsetV.set(str(self.offset))
        # Create phase offset entry box
        self.offsetEntry = Entry(master=self.boardFrame, textvariable=self.offsetV, justify=RIGHT)
        self.uiElements.append(self.offsetEntry)
        self.uiGridParams.append([4, 1, 1, 1, "WE"])
        self.offsetEntry.bind("<Return>", self.handle_updateOffset)
        self.offsetEntry.bind("<KP_Enter>", self.handle_updateOffset)
        self.offsetEntry.bind("<FocusOut>", self.handle_updateOffset)
        # Minimum phase offset
        self.offsetMin = -180
        # Maximum phase offset
        self.offsetMax = 180
        # Value for reference signal state
        self.reference = "Internal"
        # String variable for reference signal state
        self.refrenceV = StringVar()
        self.refrenceV.set(self.reference)
        # Create label for the reference signal selector
        self.refrenceLabel = Label(master=self.boardFrame, text="Reference signal")
        self.uiElements.append(self.refrenceLabel)
        self.uiGridParams.append([5, 0, 1, 1, "E"])
        # Create frame for the reference signal selector
        self.referenceFrame = Frame(master=self.boardFrame)
        self.uiElements.append(self.referenceFrame)
        self.uiGridParams.append([5, 1, 1, 1, "NESW"])
        # Create reference signal selector buttons
        self.internalButton = Radiobutton(self.referenceFrame, text="Internal", variable=self.refrenceV, value="Internal")
        self.uiElements.append(self.internalButton)
        self.uiGridParams.append([0, 0, 1, 1, "E"])
        self.internalButton.bind("<Button-1>", self.handle_referenceInternal)
        self.externalButton = Radiobutton(self.referenceFrame, text="External", variable=self.refrenceV, value="External")
        self.uiElements.append(self.externalButton)
        self.uiGridParams.append([0, 1, 1, 1, "W"])
        self.externalButton.bind("<Button-1>", self.handle_referenceExternal)
        # Create tabsystem for display and filter settings
        self.displayFilterTBS = ttk.Notebook(self.controlFrame)
        self.uiElements.append(self.displayFilterTBS)
        self.uiGridParams.append([0, 1, 1, 1, "NESW"])
        # Create frame for the display settings
        self.displayFrame = Frame(master=self.displayFilterTBS)
        self.displayFilterTBS.add(self.displayFrame, text='Display settings')
        self.displayFrame.columnconfigure((2, 3), weight=1)
        # Create label for the zoom entry box
        self.zoomLabel = Label(master=self.displayFrame, text="Zoom for Polar Plot")
        self.uiElements.append(self.zoomLabel)
        self.uiGridParams.append([0, 0, 1, 1, "E"])
        # Variable to control content of the zoom entry box
        self.zoomV = StringVar()
        self.zoomV.set(str(self.zoom))
        # Create zoom entry box
        self.zoomEntry = Entry(master=self.displayFrame, textvariable=self.zoomV, justify=RIGHT)
        self.uiElements.append(self.zoomEntry)
        self.uiGridParams.append([0, 1, 1, 1, "WE"])
        self.zoomEntry.bind("<Return>", self.handle_updateZoom)
        # Minimum zoom
        self.zoomMin = 1e-10
        # Maximum zoom
        self.zoomMax = 10
        # Create label for the data size entry box
        self.sizeLabel = Label(master=self.displayFrame, text="N")
        self.uiElements.append(self.sizeLabel)
        self.uiGridParams.append([1, 0, 1, 1, "E"])
        # Variable to control content of the data size entry box
        self.dataSizeV = StringVar()
        self.dataSizeV.set(str(self.dataSize))
        # Create data size entry box
        self.sizeEntry = Entry(master=self.displayFrame, textvariable=self.dataSizeV, justify=RIGHT)
        self.uiElements.append(self.sizeEntry)
        self.uiGridParams.append([1, 1, 1, 1, "WE"])
        self.sizeEntry.bind("<Return>", self.handle_updateSize)
        self.sizeEntry.bind("<KP_Enter>", self.handle_updateSize)
        self.sizeEntry.bind("<FocusOut>", self.handle_updateSize)
        # Minimum data size
        self.dataSizeMin = 1
        # Maximum data size
        self.dataSizeMax = 32768
        # Create frame for the filter settings
        self.filterFrame = Frame(master=self.displayFilterTBS)
        self.displayFilterTBS.add(self.filterFrame, text='Filter settings')
        #self.uiElements.append(self.filterFrame)
        #self.uiGridParams.append([0, 1, 1, 1, "NESW"])
        self.filterFrame.columnconfigure((1, 3), weight=1)
        # Create frame for the individual widgets
        # Create label for the signal filter selector
        self.filterSelectLabel = Label(master=self.filterFrame, text="Signal Filter")
        self.uiElements.append(self.filterSelectLabel)
        self.uiGridParams.append([0, 0, 1, 1, "E"])
        # List of different signal filters
        self.filters = ["FIR low pass filter", "IIR low pass filter"]
        # Create combo box for filter selector
        self.filterSelect = ttk.Combobox(master=self.filterFrame, values = self.filters, state="readonly")
        self.uiElements.append(self.filterSelect)
        self.uiGridParams.append([0, 1, 1, 3, "WE"])
        self.filterSelect.bind("<<ComboboxSelected>>", self.handle_updateFilter)
        self.filterDefault = "IIR low pass filter"
        filterDefIndex = self.filters.index(self.filterDefault)
        self.filterIndex = filterDefIndex
        self.filterSelect.set(self.filters[filterDefIndex])
        # Names for the filter property 1
        self.prop1Names = ["Cutoff frequency", "Cutoff frequency"]
        # Visibility of filter property 1
        self.prop1Visible = [True, True]
        # Create label for the filter property 1 entry box
        self.prop1Label = Label(master=self.filterFrame, text=self.prop1Names[filterDefIndex])
        self.uiElements.append(self.prop1Label)
        self.uiGridParams.append([1, 0, 1, 1, "E"])
        # Value type for the filter property 1
        self.prop1Type = ["Float", "Float"]
        # Default values for the filter property 1 (later current values)
        self.prop1Value = [20, 20]
        # Minimum values for the filter property 1
        self.prop1Min = [1.0, 1.0]
        # Maximum values for the filter property 1
        self.prop1Max = [np.inf, np.inf]
        # Variable to control content of the filter property 1 entry box
        self.prop1V = StringVar()
        self.prop1V.set(str(self.prop1Value[filterDefIndex]))
        # Create filter property 1 entry box
        self.prop1Entry = Entry(master=self.filterFrame, textvariable=self.prop1V, justify=RIGHT)
        self.uiElements.append(self.prop1Entry)
        self.uiGridParams.append([1, 1, 1, 3, "WE"])
        self.prop1Entry.bind("<Return>", self.handle_updateProp1)
        self.prop1Entry.bind("<KP_Enter>", self.handle_updateProp1)
        self.prop1Entry.bind("<FocusOut>", self.handle_updateProp1)
        # Names for the filter property 3
        self.prop3Names = ["Filter order", ""]
        # Visibility of filter property 3
        self.prop3Visible = [True, False]
        # Create label for the filter property 3 entry box
        self.prop3Label = Label(master=self.filterFrame, text=self.prop3Names[filterDefIndex])
        self.uiElements.append(self.prop3Label)
        self.uiGridParams.append([3, 0, 1, 1, "E"])
        # Value type for the filter property 3
        self.prop3Type = ["Integer", ""]
        # Default values for the filter property 3 (later current values)
        self.prop3Value = [2, None]
        # Minimum values for the filter property 3
        self.prop3Min = [2, None]
        # Maximum values for the filter property 3
        self.prop3Max = [200, None]
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
        self.prop4Names = ["Filter Window", ""]
        # Visibility of filter property 4
        self.prop4Visible = [True, False]
        # Create label for the filter property 4 combo box
        self.prop4Label = Label(master=self.filterFrame, text=self.prop4Names[filterDefIndex])
        self.uiElements.append(self.prop4Label)
        self.uiGridParams.append([4, 0, 1, 1, "E"])
        # Value type for the filter property 4
        self.prop4Type = ["String", ""]
        # Default values for the filter property 4 (later current values)
        self.prop4Value = ["Rectangle", None]
        # Minimum values for the filter property 4
        self.prop4Min = [None, None]
        # Maximum values for the filter property 4
        self.prop4Max = [None, None]
        # Variable to control content of the filter property 4 entry box
        self.prop4V = StringVar()
        self.prop4V.set(str(self.prop4Value[filterDefIndex]))
        # List of different window functions
        self.windows = ["Rectangle", "Hamming"]
        # Create combo box for window selector
        self.windowSelect = ttk.Combobox(master=self.filterFrame, values = self.windows, state="readonly")
        self.uiElements.append(self.windowSelect)
        self.uiGridParams.append([4, 1, 1, 3, "WE"])
        self.windowSelect.bind("<<ComboboxSelected>>", self.handle_updateWindow)
        self.windowSelect.set(str(self.prop4Value[self.filterIndex]))
        # Possibly add control for arithmetic
        
        
        # Create tabsystem for run control
        self.runTBS = ttk.Notebook(self.controlFrame)
        self.uiElements.append(self.runTBS)
        self.uiGridParams.append([0, 2, 1, 1, "NESW"])
        # create frame for the run control
        self.runFrame = Frame(master=self.runTBS)
        self.runTBS.add(self.runFrame, text="Run Control")
        self.runFrame.rowconfigure(1, weight=1)
        # Create label for the reading status
        self.readLabel = Label(master=self.runFrame, text="Paused")
        self.uiElements.append(self.readLabel)
        self.uiGridParams.append([0, 0, 1, 1, ""])
        # Create read switch
        self.readSwitch = Button(master=self.runFrame, text="Run                ")
        self.uiElements.append(self.readSwitch)
        self.uiGridParams.append([0, 1, 1, 1, ""])
        self.readSwitch.bind("<Button-1>", self.handle_switchRead)
        # Status variable controlling the reading of data
        self.reading = False
        # Status variable for handling restarting the reading of data
        self.reactivate = True
        # Create stop button
        self.stopButton = Button(master=self.runFrame, text="Quit Program", fg="black", bg="red")
        self.uiElements.append(self.stopButton)
        self.uiGridParams.append([1, 0, 1, 2, "NESW"])
        self.stopButton.bind("<Button-1>", self.stop)
        # Create frame for the polar plot
        self.polarFrame = Frame(master=self.window, relief=RIDGE, borderwidth=2)
        self.uiElements.append(self.polarFrame)
        self.polarFrame.rowconfigure(1, weight=1)
        self.polarFrame.columnconfigure(0, weight=1)
        self.uiGridParams.append([1, 0, 1, 2, "NESW"])
        self.polarFrame.rowconfigure(1, weight=1)
        # Create Label for polar plot
        self.polarLabel = Label(master=self.polarFrame, text="Polar Plot")
        self.uiElements.append(self.polarLabel)
        self.uiGridParams.append([0, 0, 1, 1, ""])
        # Create canvas for the polar plot
        self.fig0 = Figure(figsize=(5, 2), layout="constrained")
        # Text box for current values (note: this will only be displayed properly if the window is big enough)
        self.currentValues = self.fig0.text(0, 0.4, "R=0V\n$\phi$=0°\nX=0V\nY=0V", fontsize = 20)
        # Create axis for püolar plot
        self.ax0 = self.fig0.subplots(subplot_kw={'projection': 'polar'})
        thetaStep = 0.01
        self.theta = 2 * np.pi * np.arange(0, 1+thetaStep, thetaStep)
        self.circleLen = len(self.theta)
        # Create circle
        self.circle, = self.ax0.plot(self.theta, [1] * self.circleLen, color="darkorange", label="Display circle", linewidth=1)
        # Create display point
        self.dPoint, = self.ax0.plot(0, 1, color="darkorange", marker="o", label="Display circle", markersize=6)
        # Create display line
        self.dLine, = self.ax0.plot([0, 0], [0, 1], color="darkorange", label="Display line", linewidth=1)
        # Draw the canvas
        canvas0 = FigureCanvasTkAgg(self.fig0, master=self.polarFrame)
        canvas0.draw()
        self.uiElements.append(canvas0.get_tk_widget())
        self.uiGridParams.append([1, 0, 1, 2, "NESW"])
        # Create data tip for the polar plot - this is not ready yet as DSMVLib doesn't support polar plots yet
        #self.dataTip0 = L.dataTip(canvas0, self.ax0, 0.01, faceColor="b")
        # Create frame for saving the plot
        self.saveFrame0 = Frame()
        self.uiElements.append(self.saveFrame0)
        self.uiGridParams.append([1, 2, 1, 1, "NS"])
        # Create save button
        self.saveButton0 = Button(master=self.saveFrame0, text=u"\U0001F4BE", font=("TkDefaultFont", 60))
        self.uiElements.append(self.saveButton0)
        self.uiGridParams.append([0, 0, 1, 1, ""])
        # Create label to display saved message
        self.saveLabel0 = Label(master=self.saveFrame0)
        self.uiElements.append(self.saveLabel0)
        self.uiGridParams.append([1, 0, 1, 1, ""])
        def updateSaveLabel0(event):
            path = L.savePath("Polar Plot", self.dir)
            # save the image
            self.fig0.savefig(path + ".svg")
            # save the data as csv file
            L.saveFigCSV(self.fig0, path)
            # display the saved message
            self.saveLabel0.configure(text="Saved as " + path + "!")
            # schedule message removal
            self.window.after(2000, lambda: self.saveLabel0.configure(text=""))
        self.saveButton0.bind("<Button-1>", updateSaveLabel0)
        toolbar0 = L.VerticalPlotToolbar(canvas0, self.saveFrame0)
        toolbar0.update()
        toolbar0.pack_forget()
        self.uiElements.append(toolbar0)
        self.uiGridParams.append([2, 0, 1, 1, "NW"])
        # Create canvas for the R time series
        self.fig1 = Figure(figsize=(5, 2), layout='constrained')
        # Create values for time axis
        self.x = np.linspace(-self.dataSize+1, 0, self.dataSize)
        # Create axis
        self.ax1 = self.fig1.add_subplot(111)
        self.ax1.set_xlabel("#Value relative to present")
        self.ax1.set_ylabel("R (V)")
        # Set time axis limits to match data
        self.ax1.set_xlim([-self.dataSize+1, 0])
        # Create R time series
        self.R, = self.ax1.plot(self.x, self.data[0], 'b.-', label="R (V)", linewidth=0.5)
        # Legend for R time series
        self.legendR = self.ax1.legend(loc="upper right", title="Time series legend for R or something")
        self.legendR.set_visible(False)
        # Create the canvas
        canvas1 = FigureCanvasTkAgg(self.fig1)
        canvas1.draw()
        self.uiElements.append(canvas1.get_tk_widget())
        self.uiGridParams.append([2, 0, 1, 2, "NESW"])
        # Create data tip for canvas 1
        self.dataTip1 = L.dataTip(canvas1, self.ax1, 0.01, faceColor="b")
        # Create frame for saving the plot
        self.saveFrame1 = Frame()
        self.uiElements.append(self.saveFrame1)
        self.uiGridParams.append([2, 2, 1, 1, "NS"])
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
            L.savePlotCSV(self.R, path)
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
        # Create axis
        self.ax2 = self.fig2.add_subplot(111)
        self.ax2.set_xlabel("#Value relative to present")
        self.ax2.set_ylabel("$\phi$ (°)")
        # Set time axis limits to match data
        self.ax2.set_xlim([-self.dataSize, 0])
        # Create phi time series
        self.phi, = self.ax2.plot(self.x, self.data[1], 'b.-', label="$\phi$ (°)", linewidth=0.5)
        # Legend for R time series
        self.legendphi = self.ax2.legend(loc="upper right", title="Time series legend for phi or something")
        self.legendphi.set_visible(False)
        # Draw the canvas
        canvas2 = FigureCanvasTkAgg(self.fig2)
        canvas2.draw()
        self.uiElements.append(canvas2.get_tk_widget())
        self.uiGridParams.append([3, 0, 1, 2, "NESW"])
        # Create data tip for canvas2
        self.dataTip2 = L.dataTip(canvas2, self.ax2, 0.01, faceColor="b")
        # Create frame for saving the plot
        self.saveFrame2 = Frame()
        self.uiElements.append(self.saveFrame2)
        self.uiGridParams.append([3, 2, 1, 1, "NS"])
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
        # Label to indicate program initialization
        self.waitLabel = Label(text="Initializing... ",
                               font=("", 100))
        # status variable to prevent struggle for power between function calls
        self.busy = False
        self.updateAll(True)
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
        self.handle_updateRef(force=True)
        self.waitLabel.configure(text=pre + "-")
        self.window.update_idletasks()
        self.handle_updateOffset(force=True)
        self.waitLabel.configure(text=pre + "\\")
        self.window.update_idletasks()
        self.handle_updateFilter()
        self.waitLabel.grid_forget()
    
    # Event handler for reference frequency entry box
    def handle_updateRef(self, event=None, force=False, recursive=False, recReact=False, val=None):
        # Make sure the input is a number
        try:
            newRef = float(self.refEntry.get())
            if val != None:
                newRef = val
            # Make sure the input is in the input range
            if newRef < self.refMin:
                newRef = self.refMin
            if newRef > self.refMax:
                newRef = self.refMax
            # Only update if the value has actually changed
            if newRef != self.reffreq or force:
                # Stop reading during update
                react = self.reading
                if recursive:
                    react = recReact
                self.reading = False
                if self.busy:
                    self.window.after(1, lambda: self.handle_updateRef(force=force, recursive=True, recReact=react, val=newRef))
                else:
                    # Seize Power
                    self.busy = True
                    # Update variable for samplerate
                    self.reffreq = newRef
                    # Write command to serial port
                    time.sleep(0.005)
                    self.port.writeL("LockIn.set reffreq " + str(self.reffreq))
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
            self.reffreqV.set(str(self.reffreq))
        self.window.update_idletasks()
    
    # Event handler for data size entry box
    def handle_updateSize(self, event=None, force=False):
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
                    self.data[0] = self.data[0][self.dataSize-newSize:self.dataSize]
                    self.data[1] = self.data[1][self.dataSize-newSize:self.dataSize]
                else:
                    self.data[0] = np.pad(self.data[0], (newSize - self.dataSize, 0))
                    self.data[1] = np.pad(self.data[1], (newSize - self.dataSize, 0))
                # Update variable for data size
                self.dataSize = newSize
                # Update the axes
                self.updateAxes()
        self.dataSizeV.set(str(self.dataSize))
        self.window.update_idletasks()
    
    # Event handler for phase offset input box
    def handle_updateOffset(self, event=None, force=False, recursive=False, recReact=False, val=None):
        # Make sure the input is a number
        try:
            newOffset = float(self.offsetEntry.get())
            if val != None:
                newOffset = val
            # Make sure the input is in the input range
            if newOffset < self.offsetMin:
                newOffset = self.offsetMin
            if newOffset > self.offsetMax:
                newOffset = self.offsetMax
            # Only update if the value has actually changed
            if newOffset != self.offset or force:
                # Stop reading during update
                react = self.reading
                if recursive:
                    react = recReact
                self.reading = False
                if self.busy:
                    self.window.after(1, lambda: self.handle_updateOffset(force=force, recursive=True, recReact=react, val=newOffset))
                else:
                    # Seize Power
                    self.busy = True
                    # Update variable for samplerate
                    self.offset = newOffset
                    # Write command to serial port
                    time.sleep(0.005)
                    self.port.writeL('LockIn.set phaseOffset ' + str(self.offset))
                    # Clear serial buffer
                    self.port.clearBuffer()
                    self.readNext = True
                    # Reactivate reading if paused by this function
                    self.reading = react
                    if react:
                        self.window.after(0, self.readDisp)
                    # resign from power
                    self.busy = False
        except ValueError:
            pass
        self.offsetV.set(str(self.offset))
        self.window.update_idletasks()
    
    # Updates the x axes for plots
    def updateAxes(self):
        # Update values for number axis
        self.x = np.linspace(-self.dataSize+1, 0, self.dataSize)
        # Update the time series data
        self.R.set_xdata(self.x)
        self.R.set_ydata(self.data[0])
        self.phi.set_xdata(self.x)
        self.phi.set_ydata(self.data[1])
        # Set time axes scale
        self.ax1.set_xlim([-self.dataSize+1, 0])
        self.ax2.set_xlim([-self.dataSize+1, 0])
        # Update the canvases
        L.updateCanvas(self.fig1.canvas, self.ax1, False, True)
        L.updateCanvas(self.fig2.canvas, self.ax2, False, True)
    
    # Function to update the reference signal state and its radiobuttons
    def updateReference(self, recursive=False, recReact=False):
        # Stop reading during update
        react = self.reading
        if recursive:
            react = recReact
        self.reading = False
        if self.busy:
            self.window.after(1, lambda: self.updateReference(recursive=True, recReact=react))
        else:
            # Seize Power
            self.busy = True
            # Set string variable
            self.refrenceV.set(self.reference)
            # Write command to serial port
            time.sleep(0.005)
            self.port.writeL('LockIn.set source ' + str(self.reference))
            # Clear serial buffer
            self.port.clearBuffer()
            self.readNext = True
            # Reactivate reading if paused by this function
            self.reading = react
            if react:
                self.window.after(0, self.readDisp)
            # resign from power
            self.busy = False
    
    # Callback function for changing the reference signal to "Internal"
    def handle_referenceInternal(self, event=None):
        # Don't change state if button is disabled
        if self.internalButton["state"] == DISABLED:
            return
        self.reference = "Internal"
        self.refEntry["state"] = NORMAL
        self.updateReference()
    
    # Callback function for changing the reference signal to "External"
    def handle_referenceExternal(self, event=None):
        # Don't change state if button is disabled
        if self.externalButton["state"] == DISABLED:
            return
        self.reference = "External"
        self.refEntry["state"] = DISABLED
        self.updateReference()
    
    # Event handler for zoom entry box
    def handle_updateZoom(self, event=None, force=False):
        # Make sure the input is a number
        try:
            newZoom = float(self.zoomEntry.get())
            # Make sure the input is in the input range
            if newZoom < self.zoomMin:
                newZoom = self.zoomMin
            if newZoom > self.zoomMax:
                newZoom = self.zoomMax
            # Only update if the value has actually changed
            if newZoom != self.zoom or force:
                # Update variable for zoom
                self.zoom = newZoom
                # update polar plot scale
                self.ax0.set_ylim(0, self.zoom)
                # Update the canvas
                L.updateCanvas(self.fig0.canvas, self.ax0, False, False)
            else:
                pass
        except ValueError:
            pass
        self.zoomV.set(str(self.zoom))
        self.window.update_idletasks()
    
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
            self.prop3Label.grid_forget()
            self.prop3Entry.grid_forget()
            self.prop4Label.grid_forget()
            self.windowSelect.grid_forget()
            for k in range(len(self.filters)):
                if newFilter == self.filters[k]:
                    self.filterIndex = k
                    self.prop1Label.configure(text=self.prop1Names[k])
                    self.prop3Label.configure(text=self.prop3Names[k])
                    self.prop4Label.configure(text=self.prop4Names[k])
                    if self.prop1Visible[k]:
                        self.prop1Label.grid(row=1, column=0, sticky="E")
                        self.prop1Entry.grid(row=1, column=1, columnspan=3, sticky="WE")
                    if self.prop3Visible[k]:
                        self.prop3Label.grid(row=3, column=0, sticky="E")
                        self.prop3Entry.grid(row=3, column=1, columnspan=3, sticky="WE")
                    if self.prop4Visible[k]:
                        self.prop4Label.grid(row=4, column=0, sticky="E")
                        self.windowSelect.grid(row=4, column=1, columnspan=3, sticky="WE")
                    self.prop1V.set(self.prop1Value[k])
                    self.prop3V.set(self.prop3Value[k])
                    self.prop4V.set(self.prop4Value[k])
                    self.windowSelect.set(str(self.prop4Value[k]))
            time.sleep(0.005)
            self.port.writeL("LockIn.set filter " + newFilter)
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
            self.handle_updateProp3(force=True)
            self.handle_updateProp4(force=True)
    
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
                self.port.writeL("LockIn.set filterProperty1 " + str(self.prop1Value[self.filterIndex]))
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
                self.port.writeL("LockIn.set filterProperty3 " + str(self.prop3Value[self.filterIndex]))
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
    def handle_updateWindow(self, event=None):
        self.prop4V.set(self.windowSelect.get())
        self.handle_updateProp4()
    
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
                self.port.writeL("LockIn.set filterProperty4 " + str(self.prop4Value[self.filterIndex]))
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
            self.window.after(1, self.checkConnection)
    
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
        # Read raw values
        if self.reference == "Internal":
            rawValues = self.port.readB(2*4)
        else:
            rawValues = self.port.readB(3*4)
        # Only process data, if there was any read
        if rawValues != None and rawValues != "not enough data":
            #lastTime = time.time()
            # Discard any extra data on the port
            self.port.clearBuffer()
            # Prepare for next read
            self.readNext = True
            # convert binary data to float values
            if self.reference == "Internal":
                values = list(struct.unpack("%df" %2, rawValues))
            else:
                values = list(struct.unpack("%df" %3, rawValues))
                reffreq = values[2]
                self.reffreqV.set(reffreq)
                self.handle_updateRef(force=True)
            # Compute values for R and phi
            X = values[0]
            Y = values[1]
            R = np.sqrt(pow(X, 2) + pow(Y, 2))
            phi = np.arctan2(Y, X)
            # Store the values to the data buffer
            # Remove oldest values
            self.data[0] = self.data[0][1:self.dataSize]
            self.data[1] = self.data[1][1:self.dataSize]
            # Add the latest values to the end of the array
            self.data[0] = np.append(self.data[0], R)
            self.data[1] = np.append(self.data[1], phi)
            # Display the values
            self.R.set_ydata(self.data[0])
            self.phi.set_ydata(self.data[1])
            self.circle.set_ydata([R] * self.circleLen)
            self.dPoint.set_xdata(phi)
            self.dPoint.set_ydata(R)
            self.dLine.set_xdata([phi, phi])
            self.dLine.set_ydata([0, R])
            self.currentValues.set_text("R=" + L.fstr(R) + "V\n$\phi$=" + L.fstr(phi*180/np.pi) + "°\nX=" + L.fstr(X) + "V\nY=" + L.fstr(Y) + "V")
            # Update the canvases
            L.updateCanvas(self.fig0.canvas, self.ax0, False, False)
            L.updateCanvas(self.fig1.canvas, self.ax1, False, True)
            L.updateCanvas(self.fig2.canvas, self.ax2, False, True)
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
