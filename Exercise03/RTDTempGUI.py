# DisplayRTDTemp includes a GUI for displaying the values read from the Board as a temperature time series.
#
# Requires the Arduino sketch RTD_experiment.ino loaded on the RTD-Board.
# 
# Lukas Freudenberg (lfreudenberg@uni-osnabrueck.de)
# Philipp Rahe (prahe@uni-osnabrueck.de)
# 08.05.2023, ver1.9
# 
# Changelog
#   - 08.05.2023: Enable direct execution; N=5000 as max value; save as csv; file rename; 
#                 corrected bug with legends
#   - 21.06.2022: Update to maintain compatibility with newer version of DSMVLib module
#   - 10.05.2022: Added functionality to display the values of a point clicked on the plots
#   - 03.05.2022: Moved entry box processing to DSMVLib module,
#                 greatly improved performance of histograms
#   - 27.04.2022: Shortened entry boxes to fit on smaller screens
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

# Import official modules
import numpy as np
from matplotlib import *
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import *
import os
# Import custom module
from DSMVLib import DSMVLib as L

class RTDTempGUI:
    # Constructor method
    def __init__(self):
        # Constants for temperature calculation
        self.ALPHA = 3.85e-3
        self.RREF = 430
        # Initialize all components
        # Initialize data buffer
        self.dataSize = 100
        self.data = [[0] * self.dataSize for _ in range(2)]
        # Reference Voltage for AD7819
        self.uref = 5
        # RTD Current for AD7819
        self.IRTD = 0.001
        # Offset for AD7819
        self.offset = 0
        # R0 of the connected Pt element
        self.R0 = 100
        # R2 of the AD7819 precircutry
        self.R2 = 10000
        # R3 of the AD7819 precircutry
        self.R3 = 10000
        # Gain resistor of the AD7819 precircutry
        self.RGain = 10000
        # Constant to specify how often histograms are updated as a fraction of the data size (i. e. every 10-th value read)
        # This is done because updating the histogram is rather resource intensive
        self.histCycle = 10
        # Functions for converting the raw value according to the selected unit
        self.convertAD7819 = self.convertIdent
        self.convertMAX31865 = self.convertIdent
        # Create control window
        self.window = Tk()
        L.window = self.window
        self.window.title("RTD Temperature GUI")
        self.window.columnconfigure(1, weight=1)
        self.window.rowconfigure((1, 2), weight=1)
        # Get file path
        self.dir = os.path.relpath(__file__)
        self.dir = self.dir[0:len(self.dir)-13]
        # Initialize the port for the Board
        self.port = 0
        try:
            self.port = L.sPort()
        except L.SerialDisconnect:
            quit()
        self.disconnected = False
        # List with all UI elements
        self.uiElements = []
        # List with the grid parameters of all UI elements
        self.uiGridParams = []
        # create label for version number
        self.vLabel = Label(master=self.window, text="DSMV\nEx. 03\nv1.9")
        self.uiElements.append(self.vLabel)
        self.uiGridParams.append([0, 0, 1, 1, "NS"])
        # create frame for controls
        self.controlFrame = Frame()
        self.uiElements.append(self.controlFrame)
        self.uiGridParams.append([0, 1, 1, 2, "WE"])
        self.controlFrame.columnconfigure(1, weight=1)
        # create frame for the display settings
        self.displayFrame = Frame(master=self.controlFrame, relief=RIDGE, borderwidth=2)
        self.uiElements.append(self.displayFrame)
        self.uiGridParams.append([0, 1, 1, 1, "NESW"])
        self.displayFrame.columnconfigure(0, weight=1)
        # Create Label for display settings
        self.displayLabel = Label(master=self.displayFrame, text="Display settings")
        self.uiElements.append(self.displayLabel)
        self.uiGridParams.append([0, 0, 1, 1, ""])
        # Create frame for individual widgets
        self.displaySFrame = Frame(master=self.displayFrame, relief=RIDGE, borderwidth=2)
        self.uiElements.append(self.displaySFrame)
        self.uiGridParams.append([1, 0, 1, 1, "NESW"])
        self.displaySFrame.columnconfigure(4, weight=1)
        # Create Label for the view type selector
        self.viewLabel = Label(master=self.displaySFrame, text="View type")
        self.uiElements.append(self.viewLabel)
        self.uiGridParams.append([0, 0, 1, 1, "E"])
        # Variable to hold the current view type
        self.viewType = StringVar()
        self.viewType.set("Time series")
        # Variable that holds the previous view type
        self.viewTypePrev = "Time series"
        # Create view type selector buttons
        self.timeButton = Radiobutton(self.displaySFrame, text="Time series", variable = self.viewType, value = "Time series")
        self.uiElements.append(self.timeButton)
        self.uiGridParams.append([0, 1, 1, 1, "W"])
        self.timeButton.bind("<Button-1>", self.handle_viewTimeSeries)
        self.histAutoButton = Radiobutton(self.displaySFrame, text="Hist. (auto)", variable = self.viewType, value = "Hist. (auto)")
        self.uiElements.append(self.histAutoButton)
        self.uiGridParams.append([0, 2, 1, 1, "W"])
        self.histAutoButton.bind("<Button-1>", self.handle_viewHistogramAuto)
        self.histOneButton = Radiobutton(self.displaySFrame, text="Hist. (bin=1)", variable = self.viewType, value = "Hist. (bin=1)")
        self.uiElements.append(self.histOneButton)
        self.uiGridParams.append([0, 3, 1, 1, "W"])
        self.histOneButton.bind("<Button-1>", self.handle_viewHistogramOne)
        # Create Label for the unit selector
        self.unitLabel = Label(master=self.displaySFrame, text="Signal")
        self.uiElements.append(self.unitLabel)
        self.uiGridParams.append([1, 0, 1, 1, "E"])
        # Variable to hold the current unit
        self.unit = StringVar()
        self.unit.set("Raw value")
        # Variable that holds the previous unit
        self.unitPrev = "Raw value"
        # Create unit selector buttons
        self.rawButton = Radiobutton(self.displaySFrame, text="Raw value", variable = self.unit, value = "Raw value")
        self.uiElements.append(self.rawButton)
        self.uiGridParams.append([1, 1, 1, 1, "W"])
        self.rawButton.bind("<Button-1>", self.handle_unitRaw)
        self.voltageButton = Radiobutton(self.displaySFrame, text="U_ADCIN", variable = self.unit, value = "U_ADCIN")
        self.uiElements.append(self.voltageButton)
        self.uiGridParams.append([1, 2, 1, 1, "W"])
        self.voltageButton.bind("<Button-1>", self.handle_unitVoltage)
        self.resistanceButton = Radiobutton(self.displaySFrame, text="R_RTD", variable = self.unit, value = "R_RTD")
        self.uiElements.append(self.resistanceButton)
        self.uiGridParams.append([1, 3, 1, 1, "W"])
        self.resistanceButton.bind("<Button-1>", self.handle_unitResistance)
        self.temperatureButton = Radiobutton(self.displaySFrame, text="T_RTD", variable = self.unit, value = "T_RTD")
        self.uiElements.append(self.temperatureButton)
        self.uiGridParams.append([1, 4, 1, 1, "W"])
        self.temperatureButton.bind("<Button-1>", self.handle_unitTemperature)
        # Create Label for the array size scale
        self.sizeLabel = Label(master=self.displaySFrame, text="Data points")
        self.uiElements.append(self.sizeLabel)
        self.uiGridParams.append([2, 0, 1, 1, ""])
        # Create array size scale
        self.sizeScale = Scale(master=self.displaySFrame, from_=1, to=5000, orient=HORIZONTAL)
        self.uiElements.append(self.sizeScale)
        self.uiGridParams.append([2, 1, 1, 4, "WE"])
        self.sizeScale.set(self.dataSize)
        self.sizeScale.bind("<ButtonRelease-1>", self.changeSize)
        # Create frame for the board variables
        self.boardFrame = Frame(master=self.controlFrame, relief=RIDGE, borderwidth=2)
        self.uiElements.append(self.boardFrame)
        self.uiGridParams.append([0, 2, 1, 1, "NESW"])
        self.boardFrame.columnconfigure(0, weight=1)
        self.boardFrame.rowconfigure((1, 3), weight=1)
        # Create Label for board variables
        self.boardLabel = Label(master=self.boardFrame, text="Board variables")
        self.uiElements.append(self.boardLabel)
        self.uiGridParams.append([0, 0, 1, 1, ""])
        # Create frame for individual widgets
        self.boardSFrame = Frame(master=self.boardFrame, relief=RIDGE, borderwidth=2)
        self.uiElements.append(self.boardSFrame)
        self.uiGridParams.append([1, 0, 1, 1, "NESW"])
        # Create label for the reference voltage entry box
        self.urefLabel = Label(master=self.boardSFrame, text="U_REF (V)")
        self.uiElements.append(self.urefLabel)
        self.uiGridParams.append([0, 0, 1, 1, "E"])
        # Variable to control content of the reference voltage entry box
        self.urefV = StringVar()
        self.urefV.set(str(self.uref))
        # Create reference voltage entry box
        self.urefEntry = Entry(master=self.boardSFrame, textvariable=self.urefV, justify=RIGHT, width=10)
        self.uiElements.append(self.urefEntry)
        self.uiGridParams.append([0, 1, 1, 1, "WE"])
        self.urefEntry.bind("<Return>", self.handle_updateUref)
        self.urefEntry.bind("<KP_Enter>", self.handle_updateUref)
        self.urefEntry.bind("<FocusOut>", self.handle_updateUref)
        # Minimum refrence voltage
        self.urefMin = 1
        # Maximum refrence voltage
        self.urefMax = 10
        # Create label for the RTD current entry box
        self.IRTDLabel = Label(master=self.boardSFrame, text="I_RTD (A)")
        self.uiElements.append(self.IRTDLabel)
        self.uiGridParams.append([1, 0, 1, 1, "E"])
        # Variable to control content of the RTD current entry box
        self.IRTDV = StringVar()
        self.IRTDV.set(str(self.IRTD))
        # Create RTD current entry box
        self.IRTDEntry = Entry(master=self.boardSFrame, textvariable=self.IRTDV, justify=RIGHT, width=10)
        self.uiElements.append(self.IRTDEntry)
        self.uiGridParams.append([1, 1, 1, 1, "WE"])
        self.IRTDEntry.bind("<Return>", self.handle_updateIRTD)
        self.IRTDEntry.bind("<KP_Enter>", self.handle_updateIRTD)
        self.IRTDEntry.bind("<FocusOut>", self.handle_updateIRTD)
        # Minimum RTD current
        self.IRTDMin = 0
        # Maximum RTD current
        self.IRTDMax = 1
        # Create label for the offset entry box
        self.offsetLabel = Label(master=self.boardSFrame, text="U_offset (V)")
        self.uiElements.append(self.offsetLabel)
        self.uiGridParams.append([2, 0, 1, 1, "E"])
        # Variable to control content of the offset entry box
        self.offsetV = StringVar()
        self.offsetV.set(str(self.offset))
        # Create offset entry box
        self.offsetEntry = Entry(master=self.boardSFrame, textvariable=self.offsetV, justify=RIGHT, width=10)
        self.uiElements.append(self.offsetEntry)
        self.uiGridParams.append([2, 1, 1, 1, "WE"])
        self.offsetEntry.bind("<Return>", self.handle_updateOffset)
        self.offsetEntry.bind("<KP_Enter>", self.handle_updateOffset)
        self.offsetEntry.bind("<FocusOut>", self.handle_updateOffset)
        # Minimum offset
        self.offsetMin = -10
        # Maximum offset
        self.offsetMax = 10
        # Create label for the R0 entry box
        self.R0Label = Label(master=self.boardSFrame, text="R_0 (" + u"\U000003A9" + ")")
        self.uiElements.append(self.R0Label)
        self.uiGridParams.append([3, 0, 1, 1, "E"])
        # Variable to control content of the R0 entry box
        self.R0V = StringVar()
        self.R0V.set(str(self.R0))
        # Create R0 entry box
        self.R0Entry = Entry(master=self.boardSFrame, textvariable=self.R0V, justify=RIGHT, width=10)
        self.uiElements.append(self.R0Entry)
        self.uiGridParams.append([3, 1, 1, 1, "WE"])
        self.R0Entry.bind("<Return>", self.handle_updateR0)
        self.R0Entry.bind("<KP_Enter>", self.handle_updateR0)
        self.R0Entry.bind("<FocusOut>", self.handle_updateR0)
        # Minimum R0
        self.R0Min = 1
        # Maximum R0
        self.R0Max = 100000
        # Create label for the R2 entry box
        self.R2Label = Label(master=self.boardSFrame, text="R_2 (" + u"\U000003A9" + ")")
        self.uiElements.append(self.R2Label)
        self.uiGridParams.append([0, 2, 1, 1, "E"])
        # Variable to control content of the R2 entry box
        self.R2V = StringVar()
        self.R2V.set(str(self.R2))
        # Create R2 entry box
        self.R2Entry = Entry(master=self.boardSFrame, textvariable=self.R2V, justify=RIGHT, width=10)
        self.uiElements.append(self.R2Entry)
        self.uiGridParams.append([0, 3, 1, 1, "WE"])
        self.R2Entry.bind("<Return>", self.handle_updateR2)
        self.R2Entry.bind("<KP_Enter>", self.handle_updateR2)
        self.R2Entry.bind("<FocusOut>", self.handle_updateR2)
        # Minimum R2
        self.R2Min = 1
        # Maximum R2
        self.R2Max = 1000000
        # Create label for the R3 entry box
        self.R3Label = Label(master=self.boardSFrame, text="R_3 (" + u"\U000003A9" + ")")
        self.uiElements.append(self.R3Label)
        self.uiGridParams.append([1, 2, 1, 1, "E"])
        # Variable to control content of the R3 entry box
        self.R3V = StringVar()
        self.R3V.set(str(self.R3))
        # Create R3 entry box
        self.R3Entry = Entry(master=self.boardSFrame, textvariable=self.R3V, justify=RIGHT, width=10)
        self.uiElements.append(self.R3Entry)
        self.uiGridParams.append([1, 3, 1, 1, "WE"])
        self.R3Entry.bind("<Return>", self.handle_updateR3)
        self.R3Entry.bind("<KP_Enter>", self.handle_updateR3)
        self.R3Entry.bind("<FocusOut>", self.handle_updateR3)
        # Minimum R3
        self.R3Min = 1
        # Maximum R3
        self.R3Max = 1000000
        # Create label for the gain resistor entry box
        self.RGainLabel = Label(master=self.boardSFrame, text="R_gain (" + u"\U000003A9" + ")")
        self.uiElements.append(self.RGainLabel)
        self.uiGridParams.append([2, 2, 1, 1, "E"])
        # Variable to control content of the RGain entry box
        self.RGainV = StringVar()
        self.RGainV.set(str(self.RGain))
        # Create gain resitor entry box
        self.RGainEntry = Entry(master=self.boardSFrame, textvariable=self.RGainV, justify=RIGHT, width=10)
        self.uiElements.append(self.RGainEntry)
        self.uiGridParams.append([2, 3, 1, 1, "WE"])
        self.RGainEntry.bind("<Return>", self.handle_updateRGain)
        self.RGainEntry.bind("<KP_Enter>", self.handle_updateRGain)
        self.RGainEntry.bind("<FocusOut>", self.handle_updateRGain)
        # Minimum gain resitor
        self.RGainMin = 1
        # Maximum gain resistor
        self.RGainMax = 10000000
        # create frame for the run control
        self.runFrame = Frame(master=self.controlFrame, relief=RIDGE, borderwidth=2)
        self.uiElements.append(self.runFrame)
        self.uiGridParams.append([0, 4, 1, 1, "NESW"])
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
        # Create stop button
        self.stopButton = Button(master=self.runSFrame, text="Quit Program", fg="black", bg="red")
        self.uiElements.append(self.stopButton)
        self.uiGridParams.append([1, 0, 1, 2, "NESW"])
        self.stopButton.bind("<Button-1>", self.stop)
        # Create canvas for the time series of the AD7819
        self.fig1 = Figure(figsize=(5, 3), layout='constrained')
        # Create a list of evenly-spaced numbers over the range
        self.x = np.linspace(1, self.dataSize, self.dataSize)
        self.ax1 = self.fig1.add_subplot(111)
        self.ax1.set_xlabel("Index")
        self.ax1.set_ylabel("Raw value AD7819")
        self.line1, = self.ax1.plot(self.x, self.data[0], 'r.-', linewidth=0.5)
        # Legend for AD7819
        self.legend1 = self.ax1.legend([], loc="upper left", title="Last value: 0")
        canvas1 = FigureCanvasTkAgg(self.fig1)
        canvas1.draw()
        self.uiElements.append(canvas1.get_tk_widget())
        self.uiGridParams.append([1, 0, 1, 2, "NESW"])
        # Create data tip for canvas 1
        self.dataTip1 = L.dataTip(canvas1, self.ax1, 0.01, self.line1)
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
            path = L.savePath("RTD_data", self.dir)
            # save the images
            self.fig1.savefig(path + " AD7819.svg")
            self.fig1.savefig(path + " AD7819.png")
            self.fig2.savefig(path + " MAX31865.svg")
            self.fig2.savefig(path + " MAX31865.png")
            # save the data as csv file
            outarr = np.asarray([self.x, self.data[0], self.data[1]])
            outarr = outarr.transpose()
            np.savetxt(path + ".csv", outarr, delimiter=",")
            # display the saved message
            self.saveLabel1.configure(text="Last file:\n " + path)
            # schedule message removal
            #self.window.after(2000, lambda: self.saveLabel1.configure(text=""))
        self.saveButton1.bind("<Button-1>", updateSaveLabel1)
        toolbar1 = L.VerticalPlotToolbar(canvas1, self.saveFrame1)
        toolbar1.update()
        toolbar1.pack_forget()
        self.uiElements.append(toolbar1)
        self.uiGridParams.append([2, 0, 1, 1, "NW"])
        # Create canvas for the time series of the MAX31865
        self.fig2 = Figure(figsize=(5, 3), layout='constrained')
        # Create a list of evenly-spaced numbers over the range
        #x2 = np.linspace(1, self.dataSize, self.dataSize)
        self.ax2 = self.fig2.add_subplot(111)
        self.ax2.set_xlabel("Index")
        self.ax2.set_ylabel("Raw value MAX31865")
        self.line2, = self.ax2.plot(self.x, self.data[1], 'r.-', linewidth=0.5)
        # Legend for MAX31865
        self.legend2 = self.ax2.legend([], loc="upper left", title="Last value: 0")
        canvas2 = FigureCanvasTkAgg(self.fig2)
        canvas2.draw()
        self.uiElements.append(canvas2.get_tk_widget())
        self.uiGridParams.append([2, 0, 1, 2, "NESW"])
        # Create data tip for canvas 2
        self.dataTip2 = L.dataTip(canvas2, self.ax2, 0.01, self.line2)
        # Create frame for saving the plot
        self.saveFrame2 = Frame()
        self.uiElements.append(self.saveFrame2)
        self.uiGridParams.append([2, 2, 1, 1, "NW"])
        # Create save button
        #self.saveButton2 = Button(master=self.saveFrame2, text=u"\U0001f4be", font=("TkDefaultFont", 60))
        #self.uiElements.append(self.saveButton2)
        #self.uiGridParams.append([0, 0, 1, 1, ""])
        # Create label to display saved message
        #self.saveLabel2 = Label(master=self.saveFrame2)
        #self.uiElements.append(self.saveLabel2)
        #self.uiGridParams.append([1, 0, 1, 1, ""])
        #def updateSaveLabel2(event):
        #    path = L.savePath("MAX31865", self.dir)
        #    # save the image
        #    self.fig2.savefig(path + ".svg")
        #    # save the data as text
        #    f = open(path + ".txt", mode = "w")
        #    f.write(str(self.data[1]))
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
        self.waitLabel = Label(text="Initializing... ",
                               font=("", 100))
        # Maximize the window
        self.window.attributes("-zoomed", True)
        # Display the widgets
        L.buildUI(self.uiElements, self.uiGridParams)
        # Start the reading thread
        self.port.start(maxSize=65536)
        # Execute the function to read with the mainloop of the window (this is probably not the best solution)
        self.window.mainloop()
    
    # Function for "converting" a raw input value into a raw input value
    def convertIdent(self, value):
        return value
    
    # Function for converting a raw input value into a voltage (AD7819)
    def convertVoltageAD7819(self, value):
        val = value * self.uref / 256
        return val
    
    # Function for converting a raw input value into a Resistance (AD7819)
    def convertResistanceAD7819(self, value):
        u = self.convertVoltageAD7819(value)
        val = self.R2 * (u - self.offset * self.RGain / self.R3) / (self.IRTD * self.RGain - u + self.offset * self.RGain / self.R3)
        return val
    
    # Function to convert the value into a temperature
    def convertTempAD7819(self, value):
        # Calculate the value of the resistor
        R = self.convertResistanceAD7819(value)
        # Calculate the temperature
        val = (R-self.R0)/(self.ALPHA*self.R0)
        return val
    
    # Function for converting a raw input value into a Resistance (MAX31865)
    def convertResistanceMAX31865(self, value):
        val = self.RREF * value / pow(2, 15)
        return val
    
    # Function to convert the value into a temperature (this is your task)
    def convertTempMAX31865(self, value):
        # Calculate the value of the resistor first
        R = self.convertResistanceMAX31865(value)
        # Now calculate the temperature
        val = (R-100)/(self.ALPHA*100)
        return val
    
    # Function for displaying correct labelling of the axes
    def labelAxes(self):
        dataAD7819 = ""
        dataMAX31865 = ""
        if self.unit.get() == "Raw value":
            dataAD7819 = "Raw value AD7819"
            dataMAX31865 = "Raw value MAX31865"
        elif self.unit.get() == "Voltage":
            dataAD7819 = "Voltage AD7819 (V)"
            dataMAX31865 = "Raw value MAX31865"
        elif self.unit.get() == "Resistance":
            dataAD7819 = "Resistance AD7819 (" + u"\U000003A9" + ")"
            dataMAX31865 = "Resistance MAX31865 (" + u"\U000003A9" + ")"
        elif self.unit.get() == "Temperature":
            dataAD7819 = "Temperature AD7819 (°C)"
            dataMAX31865 = "Temperature MAX31865 (°C)"
        if self.viewType.get() == "Time series":
            self.ax1.set_xlabel("Index")
            self.ax1.set_ylabel(dataAD7819)
            self.ax2.set_xlabel("Index")
            self.ax2.set_ylabel(dataMAX31865)
        else:
            self.ax1.set_xlabel(dataAD7819)
            self.ax1.set_ylabel("Data frequency")
            self.ax2.set_xlabel(dataMAX31865)
            self.ax2.set_ylabel("Data frequency")
    
    # Callback function for changing the view type to Hist. (auto)
    def handle_viewHistogramAuto(self, event):
        self.viewType.set("Hist. (auto)")
        if self.viewTypePrev == self.viewType.get():
            return
        self.viewTypePrev = self.viewType.get()
        self.labelAxes()
    
    # Callback function for changing the view type to Hist. (bin=1)
    def handle_viewHistogramOne(self, event):
        self.viewType.set("Hist. (bin=1)")
        if self.viewTypePrev == self.viewType.get():
            return
        self.viewTypePrev = self.viewType.get()
        self.labelAxes()
    
    # Callback function for changing the view type to time series
    def handle_viewTimeSeries(self, event):
        self.viewType.set("Time series")
        if self.viewTypePrev == self.viewType.get():
            return
        self.viewTypePrev = self.viewType.get()
        self.ax1.cla()
        self.ax2.cla()
        self.line1, = self.ax1.plot(self.x, self.data[0], 'r.-', linewidth=0.5)
        self.line2, = self.ax2.plot(self.x, self.data[1], 'r.-', linewidth=0.5)
        self.labelAxes()
    
    # Callback function for changing the unit to raw value
    def handle_unitRaw(self, event):
        self.unit.set("Raw value")
        if self.unitPrev == self.unit.get():
            return
        self.unitPrev = self.unit.get()
        self.convertAD7819 = self.convertIdent
        self.convertMAX31865 = self.convertIdent
    
    # Callback function for changing the unit to Volts
    def handle_unitVoltage(self, event):
        self.unit.set("U_ADCIN")
        if self.unitPrev == self.unit.get():
            return
        self.unitPrev = self.unit.get()
        self.convertAD7819 = self.convertVoltageAD7819
        self.convertMAX31865 = self.convertIdent
    
    # Callback function for changing the unit to raw Ohms
    def handle_unitResistance(self, event):
        self.unit.set("R_RTD")
        if self.unitPrev == self.unit.get():
            return
        self.unitPrev = self.unit.get()
        self.convertAD7819 = self.convertResistanceAD7819
        self.convertMAX31865 = self.convertResistanceMAX31865
    
    # Callback function for changing the unit to raw °C
    def handle_unitTemperature(self, event):
        self.unit.set("T_RTD")
        if self.unitPrev == self.unit.get():
            return
        self.unitPrev = self.unit.get()
        self.convertAD7819 = self.convertTempAD7819
        self.convertMAX31865 = self.convertTempMAX31865
    
    # Callback function for the array size scale
    def changeSize(self, event):
        newSize = self.sizeScale.get()
        if newSize < self.dataSize:
            self.data[0] = self.data[0][self.dataSize-newSize:self.dataSize]
            self.data[1] = self.data[1][self.dataSize-newSize:self.dataSize]
        else:
            self.data[0] = [0]*(newSize - self.dataSize) + self.data[0]
            self.data[1] = [0]*(newSize - self.dataSize) + self.data[1]
        self.dataSize = newSize
        self.x = np.linspace(1, self.dataSize, self.dataSize)
    
    # Event handler for reference voltage input box
    def handle_updateUref(self, event=0):
        newUref = L.toFloat(self.urefEntry.get())
        if newUref != None:
            # Make sure the input is in the input range
            if newUref < self.urefMin:
                newUref = self.urefMin
            if newUref > self.urefMax:
                newUref = self.urefMax
            # Update variable for reference voltage
            self.uref = newUref
        self.urefV.set(str(self.uref))
        self.window.update_idletasks()
    
    # Event handler for RTD current input box
    def handle_updateIRTD(self, event=0):
        newIRTD = L.toFloat(self.IRTDEntry.get())
        if newIRTD != None:
            # Make sure the input is in the input range
            if newIRTD < self.IRTDMin:
                newIRTD = self.IRTDMin
            if newIRTD > self.IRTDMax:
                newIRTD = self.IRTDMax
            # Update variable for reference voltage
            self.IRTD = newIRTD
        self.IRTDV.set(str(self.IRTD))
        self.window.update_idletasks()
    
    # Event handler for offset input box
    def handle_updateOffset(self, event=0):
        newOffset = L.toFloat(self.offsetEntry.get())
        if newOffset != None:
            # Make sure the input is in the input range
            if newOffset < self.offsetMin:
                newOffset = self.offsetMin
            if newOffset > self.offsetMax:
                newOffset = self.offsetMax
            # Update variable for reference voltage
            self.offset = newOffset
        self.offsetV.set(str(self.offset))
        self.window.update_idletasks()
    
    # Event handler for R0 input box
    def handle_updateR0(self, event=0):
        newR0 = L.toFloat(self.R0Entry.get())
        if newR0 != None:
            # Make sure the input is in the input range
            if newR0 < self.R0Min:
                newR0 = self.R0Min
            if newR0 > self.R0Max:
                newR0 = self.R0Max
            # Update variable for reference voltage
            self.R0 = newR0
        self.R0V.set(str(self.R0))
        self.window.update_idletasks()
    
    # Event handler for R2 input box
    def handle_updateR2(self, event=0):
        newR2 = L.toFloat(self.R2Entry.get())
        if newR2 != None:
            # Make sure the input is in the input range
            if newR2 < self.R2Min:
                newR2 = self.R2Min
            if newR2 > self.R2Max:
                newR2 = self.R2Max
            # Update variable for reference voltage
            self.R2 = newR2
        self.R2V.set(str(self.R2))
        self.window.update_idletasks()
    
    # Event handler for R3 input box
    def handle_updateR3(self, event=0):
        newR3 = L.toFloat(self.R3Entry.get())
        if newR3 != None:
            # Make sure the input is in the input range
            if newR3 < self.R3Min:
                newR3 = self.R3Min
            if newR3 > self.R3Max:
                newR3 = self.R3Max
            # Update variable for reference voltage
            self.R3 = newR3
        self.R3V.set(str(self.R3))
        self.window.update_idletasks()
    
    # Event handler for gain resitor input box
    def handle_updateRGain(self, event=0):
        newRGain = L.toFloat(self.RGainEntry.get())
        if newRGain != None:
            # Make sure the input is in the input range
            if newRGain < self.RGainMin:
                newRGain = self.RGainMin
            if newRGain > self.RGainMax:
                newRGain = self.RGainMax
            # Update variable for reference voltage
            self.RGain = newRGain
        self.RGainV.set(str(self.RGain))
        self.window.update_idletasks()
    
    # Checks whether the board is still connected and acts accordingly
    def checkConnection(self):
        # Prepare for restoring settings on reconnect
        if self.port.disconnected() and not self.disconnected:
            self.disconnected = True
            self.reactivate = self.reading
            self.reading = False
            self.controlFrame.grid_forget()
            self.waitLabel.configure(text="Connection Lost")
            self.waitLabel.grid(row=0, column=1, sticky="WE")
            self.window.update_idletasks()
        elif self.disconnected and self.port.disconnected():
            self.window.update_idletasks()
        # Restore GUI on reconnect
        if self.disconnected and not self.port.disconnected():
            L.buildUI(self.uiElements, self.uiGridParams)
            self.waitLabel.grid_forget()
            self.window.update_idletasks()
            self.disconnected = False
            if self.reactivate:
                self.handle_switchRead()
        if not self.reading:
            self.window.after(1, self.checkConnection)
    
    # Function that handles reading and displaying data from the serial port
    def readDisp(self):
        # Check the board connection
        self.checkConnection()
        # Do nothing if the button to start the program hasn"t been pressed yet or the port is being initialized
        if not self.reading:
            return
        # Read data from the serial port (if available)
        status = self.port.readL(False)
        # Only process data, if there was any read
        if status != "not enough data":
            # Clear excess data
            self.port.clearBuffer(clearLine = True)
            # Split into the two parts
            status = status.split(", ")
            # Store the values as integers
            value_ad7819 = float(status[0])
            if len(status) == 2:
                value_max31865 = float(status[1])
            # Convert the integer into a temperature
            value_ad7819 = self.convertAD7819(value_ad7819)
            if len(status) == 2:
                value_max31865 = self.convertMAX31865(value_max31865)
            # Store values in the data buffer
            # Remove oldest values
            self.data[0].pop(0)
            if len(status) == 2:
                self.data[1].pop(0)
            # Add the latest values to the end of the array
            self.data[0].append(value_ad7819)
            if len(status) == 2:
                self.data[1].append(value_max31865)
            # Display the values
            if self.viewType.get() == "Time series":
                self.line1.set_xdata(self.x)
                self.line1.set_ydata(self.data[0])
            elif self.viewType.get() == "Hist. (auto)":
                self.ax1.cla()
                self.line1 = self.ax1.hist(self.data[0], histtype='step')
            elif self.viewType.get() == "Hist. (bin=1)":
                self.ax1.cla()
                self.line1 = self.ax1.hist(self.data[0], bins=np.arange(min(self.data[0]), max(self.data[0]) + 2, 1), histtype='step')
            # Update plot legend
            self.legend1 = self.ax1.legend([], loc="upper left", title="Last value: %.2f" %self.data[0][len(self.data[0])-1])
            # Label axes correctly
            self.labelAxes()
            L.updateCanvas(self.fig1.canvas, self.ax1)
            if len(status) == 2:
                if self.viewType.get() == "Time series":
                    self.line2.set_xdata(self.x)
                    self.line2.set_ydata(self.data[1])
                elif self.viewType.get() == "Hist. (auto)":
                    self.ax2.cla()
                    self.line2 = self.ax2.hist(self.data[1], histtype='step')
                elif self.viewType.get() == "Hist. (bin=1)":
                    self.ax2.cla()
                    self.line2 = self.ax2.hist(self.data[1], bins=np.arange(min(self.data[1]), max(self.data[1]) + 2, 1), histtype='step')
                # Update plot legend
                self.legend2 = self.ax2.legend([], loc="upper left", title="Last value: %.2f" %self.data[1][len(self.data[1])-1])
                # Label axes correctly
                self.labelAxes()
                L.updateCanvas(self.fig2.canvas, self.ax2)
        
        # Reschedule function (this is probably not the best solution)
        self.window.after(0, self.readDisp)

    # Callback for read switch
    def handle_switchRead(self, event):
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
    
    # Callback for the stop button
    def stop(self, event):
        self.reading = False
        self.window.update_idletasks()
        self.window.withdraw()
        self.window.destroy()


# start the GUI when the file is directly run by the python interpreter
if __name__ == '__main__':
    gui = RTDTempGUI()