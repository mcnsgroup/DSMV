# DSMVGUI includes a GUI for the oscilloscope functionality of the DSMV board
#
# Requires the Arduino sketch DisplayDSMV.ino loaded on the Teensy 4.0.
# 
# Lukas Freudenberg (lfreudenberg@uni-osnabrueck.de)
# Philipp Rahe (prahe@uni-osnabrueck.de)
# 12.05.2023, ver1.13
# 
# Changelog
#   - 12.05.2023: Renamed to DSMVGUI; added direct calling option; optimise label formatting
#                 reduced to one save button; csv export optimised
#   - 02.09.2022: Fixed a bug that caused the trigger threshold slider to not be disabled for Schmitt trigger
#   - 21.06.2022: Update to maintain compatibility with newer version of DSMVLib module
#   - 23.05.2022: Update to maintain compatibility with newer version of Arduino program,
#                 fixed a bug that caused the serial connection to not be monitored at the beginning,
#                 fixed a bug that falsely caused the reading to start after a serial reconnect
#   - 10.05.2022: Added functionality to display the values of a point clicked on the plots
#   - 09.05.2022: Added functionality to update entry boxes on keypad return key and focus out,
#                 fixied a bug causing the parameters to not update properly when in histogram mode
#   - 06.05.2022: Added functionality to show raw values,
#                 added functionality to show data as histograms,
#                 increased maximum oversampling to 65536,
#                 added indicator for time/series,
#                 minor design changes
#   - 03.05.2022: Moved entry box processing to DSMVLib module,
#                 changed save label to unicode symbol
#   - 27.04.2022: Changed building of the GUI to modular function from DSMVLib,
#                 added version indicator in GUI,
#                 added functionality to save plot data as plain text,
#                 update to utilize PyPI version of the DSMVLib package,
#                 added vertical tkinter menu bar from DSMVLib package
#   - 27.01.2022: Added functionality for saving plots as vector images
#   - 26.01.2022: Fixed a bug that prevented correct restoration of settings, 
#                 added indication for when the GUI isn't usable due to a disconnect or initialization
#   - 20.01.2022: Changed dropdown menus to read only, added compatibility with Spectral without the need no restart the Board, added window title
#   - 19.01.2022: Minor change to keep compatibility with DSMVLib module
#   - 17.01.2022: Added legends to plots and added trigger flank option for Schmitt trigger
#   - 12.01.2022: Ported to Python
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
import os
import struct
import time
# Import custom module
from DSMVLib import DSMVLib as L

class DSMVGUI:
    # Constructor method
    def __init__(self):
        # Initialize all components
        # Create control window
        self.window = Tk()
        L.window = self.window
        self.window.title("DSMV GUI")
        self.window.columnconfigure(1, weight=1)
        self.window.rowconfigure((1, 2, 3), weight=1)
        # Get file path
        self.dir = os.path.relpath(__file__)
        self.dir = self.dir[0:len(self.dir)-10]
        # Initialize the port for the Board
        self.port = 0
        try:
            self.port = L.sPort()
        except L.SerialDisconnect:
            quit()
        self.disconnected = False
        self.readNext = False
        self.oversamplesDefault = 1
        self.oversamples = self.oversamplesDefault
        self.samplerateDefault = 1000.0
        self.samplerate = self.samplerateDefault
        self.dataSizeDefault = 100
        self.dataSize = self.dataSizeDefault
        # Initialize data buffer
        self.dataSize = 100
        self.data = [[0] * self.dataSize for _ in range(3)]
        # List with all UI elements
        self.uiElements = []
        # List with the grid parameters of all UI elements
        self.uiGridParams = []
        # create label for version number
        self.vLabel = Label(master=self.window, text="DSMV\nEx. 04\nv1.13")
        self.uiElements.append(self.vLabel)
        self.uiGridParams.append([0, 0, 1, 1, "NS"])
        # create frame for controls
        self.controlFrame = Frame()
        self.uiElements.append(self.controlFrame)
        self.uiGridParams.append([0, 1, 1, 2, "WE"])
        self.controlFrame.columnconfigure(1, weight=1)
        # create frame for the data settings
        self.dataFrame = Frame(master=self.controlFrame, relief=RIDGE, borderwidth=2)
        self.uiElements.append(self.dataFrame)
        self.uiGridParams.append([0, 0, 1, 1, "NESW"])
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
        # Create label for the samplerate entry box
        self.freqLabel = Label(master=self.dataSFrame, text="f_s (Hz)")
        self.uiElements.append(self.freqLabel)
        self.uiGridParams.append([0, 0, 1, 1, "E"])
        # Variable to control content of the samplerate entry box
        self.samplerateV = StringVar()
        self.samplerateV.set(str(self.samplerate))
        # Create samplerate entry box
        self.freqEntry = Entry(master=self.dataSFrame, textvariable=self.samplerateV, justify=RIGHT)
        self.uiElements.append(self.freqEntry)
        self.uiGridParams.append([0, 1, 1, 1, "WE"])
        self.freqEntry.bind("<Return>", self.handle_updateFreq)
        self.freqEntry.bind("<KP_Enter>", self.handle_updateFreq)
        self.freqEntry.bind("<FocusOut>", self.handle_updateFreq)
        # Minimum samplerate
        self.samplerateMin = 1
        # Maximum samplerate
        self.samplerateMax = 80000
        # Create label for the data size entry box
        self.sizeLabel = Label(master=self.dataSFrame, text="N_s")
        self.uiElements.append(self.sizeLabel)
        self.uiGridParams.append([1, 0, 1, 1, "E"])
        # Variable to control content of the data size entry box
        self.dataSizeV = StringVar()
        self.dataSizeV.set(str(self.dataSize))
        # Create data size entry box
        self.sizeEntry = Entry(master=self.dataSFrame, textvariable=self.dataSizeV, justify=RIGHT)
        self.uiElements.append(self.sizeEntry)
        self.uiGridParams.append([1, 1, 1, 1, "WE"])
        self.sizeEntry.bind("<Return>", self.handle_updateSize)
        self.sizeEntry.bind("<KP_Enter>", self.handle_updateSize)
        self.sizeEntry.bind("<FocusOut>", self.handle_updateSize)
        # Minimum data size
        self.dataSizeMin = 1
        # Maximum data size
        self.dataSizeMax = 32768 #due to not being able to change the buffer size of pyserial to something greater that 4095, the speed is severly limited
        # Create label for the oversamples entry box
        self.oversLabel = Label(master=self.dataSFrame, text="N_o")
        self.uiElements.append(self.oversLabel)
        self.uiGridParams.append([2, 0, 1, 1, "E"])
        # Variable to control content of the oversamples entry box
        self.oversamplesV = StringVar()
        self.oversamplesV.set(str(self.oversamples))
        # Create oversamples entry box
        self.oversEntry = Entry(master=self.dataSFrame, textvariable=self.oversamplesV, justify=RIGHT)
        self.uiElements.append(self.oversEntry)
        self.uiGridParams.append([2, 1, 1, 1, "WE"])
        self.oversEntry.bind("<Return>", self.handle_updateOvers)
        self.oversEntry.bind("<KP_Enter>", self.handle_updateOvers)
        self.oversEntry.bind("<FocusOut>", self.handle_updateOvers)
        # Minimum oversamples
        self.oversMin = 1
        # Maximum oversamples
        self.oversMax = 65536
        # Create label for the signal type switch
        self.signalLabel = Label(master=self.dataSFrame, text="Signal")
        self.uiElements.append(self.signalLabel)
        self.uiGridParams.append([0, 2, 1, 1, "E"])
        # Variable to hold the current signal type setting
        self.signal = StringVar()
        self.signal.set("Voltage")
        # Variable that holds the previous signal type setting
        self.signalPrev = "Voltage"
        # Create signal type selector buttons
        self.voltageButton = Radiobutton(self.dataSFrame, text="Voltage", variable = self.signal, value = "Voltage")
        self.uiElements.append(self.voltageButton)
        self.uiGridParams.append([0, 3, 1, 1, "E"])
        self.voltageButton.bind("<Button-1>", self.handle_signalVoltage)
        self.rawButton = Radiobutton(self.dataSFrame, text="Raw Value", variable = self.signal, value = "Raw Value")
        self.uiElements.append(self.rawButton)
        self.uiGridParams.append([0, 4, 1, 1, "W"])
        self.rawButton.bind("<Button-1>", self.handle_signalRaw)
        # Create Label for the view type selector
        self.viewLabel = Label(master=self.dataSFrame, text="View type")
        self.uiElements.append(self.viewLabel)
        self.uiGridParams.append([1, 2, 1, 1, "E"])
        # Variable to hold the current view type
        self.viewType = StringVar()
        self.viewType.set("Time series")
        # Variable that holds the previous view type
        self.viewTypePrev = "Time series"
        # Create view type selector buttons
        self.timeButton = Radiobutton(self.dataSFrame, text="Time series", variable = self.viewType, value = "Time series")
        self.uiElements.append(self.timeButton)
        self.uiGridParams.append([1, 3, 1, 1, "W"])
        self.timeButton.bind("<Button-1>", self.handle_viewTimeSeries)
        self.histAutoButton = Radiobutton(self.dataSFrame, text="Hist. (auto)", variable = self.viewType, value = "Hist. (auto)")
        self.uiElements.append(self.histAutoButton)
        self.uiGridParams.append([1, 4, 1, 1, "W"])
        self.histAutoButton.bind("<Button-1>", self.handle_viewHistogramAuto)
        self.histOneButton = Radiobutton(self.dataSFrame, text="Hist. (bin=1)", variable = self.viewType, value = "Hist. (bin=1)")
        self.uiElements.append(self.histOneButton)
        self.uiGridParams.append([1, 5, 1, 1, "W"])
        self.histOneButton.bind("<Button-1>", self.handle_viewHistogramOne)
        # Label to show time required to assemble one full data set
        self.timeLabel = Label(master=self.dataSFrame, text="Time/series: 0.1s")
        self.uiElements.append(self.timeLabel)
        self.uiGridParams.append([2, 2, 1, 4, "W"])
        # Create frame for the trigger settings
        self.triggerFrame = Frame(master=self.controlFrame, relief=RIDGE, borderwidth=2)
        self.uiElements.append(self.triggerFrame)
        self.uiGridParams.append([0, 1, 1, 1, "NESW"])
        self.triggerFrame.rowconfigure(1, weight=1)
        self.triggerFrame.columnconfigure(0, weight=1)
        # Create Label for trigger settings
        self.triggerLabel = Label(master=self.triggerFrame, text="Trigger settings")
        self.uiElements.append(self.triggerLabel)
        self.uiGridParams.append([0, 0, 1, 1, ""])
        # Create frame for the individual widgets
        self.triggerSFrame = Frame(master=self.triggerFrame, relief=RIDGE, borderwidth=2)
        self.uiElements.append(self.triggerSFrame)
        self.uiGridParams.append([1, 0, 1, 1, "NESW"])
        self.triggerSFrame.columnconfigure((1, 2), weight=1)
        # Create label for the trigger source selector
        self.tSelectLabel = Label(master=self.triggerSFrame, text="Trigger source")
        self.uiElements.append(self.tSelectLabel)
        self.uiGridParams.append([0, 0, 1, 1, "E"])
        # List of different trigger sources
        tslist = ["Untriggered (roll)", "AD4020", "LTC2500", "Internal ADC", "Schmitt trigger"]
        # Create combo box for trigger source selector
        self.tSelect = ttk.Combobox(master=self.triggerSFrame, values = tslist, state="readonly")
        self.uiElements.append(self.tSelect)
        self.uiGridParams.append([0, 1, 1, 2, "WE"])
        self.tSelect.bind('<<ComboboxSelected>>', self.handle_updateTriggerSource)
        self.tSelect.set(tslist[0])
        # Create label for threshold voltage scale
        self.thresholdLabel = Label(master=self.triggerSFrame, text="Trigger threshold (V)")
        self.uiElements.append(self.thresholdLabel)
        self.uiGridParams.append([1, 0, 1, 1, "E"])
        # Create threshold voltage scale
        self.thresholdScale = Scale(master=self.triggerSFrame, from_=-10, to=10, orient=HORIZONTAL,
                                    resolution=0.001, state=DISABLED)
        self.uiElements.append(self.thresholdScale)
        self.uiGridParams.append([1, 1, 1, 2, "WE"])
        self.thresholdScale.set(0)
        self.thresholdScale.bind("<ButtonRelease-1>", self.handle_updateThreshold)
        # Create label for the flank switch
        self.flankLabel = Label(master=self.triggerSFrame, text="Trigger flank")
        self.uiElements.append(self.flankLabel)
        self.uiGridParams.append([2, 0, 1, 1, "E"])
        # Variable to hold the current flank setting
        self.flank = StringVar()
        self.flank.set("Rising")
        # Variable that holds the previous flank setting
        self.flankPrev = "Rising"
        # Create flank selector buttons
        self.fallingButton = Radiobutton(self.triggerSFrame, text="Falling", variable = self.flank, value = "Falling", state=DISABLED)
        self.uiElements.append(self.fallingButton)
        self.uiGridParams.append([2, 1, 1, 1, "E"])
        self.fallingButton.bind("<Button-1>", self.handle_flankFalling)
        self.risingButton = Radiobutton(self.triggerSFrame, text="Rising", variable = self.flank, value = "Rising", state=DISABLED)
        self.uiElements.append(self.risingButton)
        self.uiGridParams.append([2, 2, 1, 1, "W"])
        self.risingButton.bind("<Button-1>", self.handle_flankRising)
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
        self.reactivate = False
        # Create stop button
        self.stopButton = Button(master=self.runSFrame, text="Quit Program", fg="black", bg="red")
        self.uiElements.append(self.stopButton)
        self.uiGridParams.append([1, 0, 1, 2, "NESW"])
        self.stopButton.bind("<Button-1>", self.stop)
        # Axis labels for the data from the ADCs
        self.dataAD4020 = "Voltage AD4020 (V)"
        self.dataLTC2500 = "Voltage LTC2500 (V)"
        self.dataInternal = "Voltage internal ADC (V)"
        # Unit label for legend
        self.unit = "V"
        # Create canvas for the time series of the AD4020
        self.fig1 = Figure(figsize=(5, 2), layout='constrained')
        # Maximum time value
        tMax = (self.dataSize-1)*self.oversamples/self.samplerate
        # Create values for time axes
        self.x = np.linspace(0, tMax, self.dataSize)
        self.ax1 = self.fig1.add_subplot(111)
        self.ax1.set_xlabel("Time (s)")
        self.ax1.set_ylabel("Voltage AD4020 (V)")
        # Set time axis limits to match data
        self.ax1.set_xlim([0, tMax])
        self.line1, = self.ax1.plot(self.x, self.data[0], 'b-', label='AD4020 voltage')
        self.legend1 = self.ax1.legend(loc='upper right', title="Average : 0V \nStd. dev.: 0V")
        self.legend1.get_title().set_multialignment('left')
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
            path = L.savePath("DSMV_data", self.dir)
            # save the image
            self.fig1.savefig(path + "AD4020.svg")
            self.fig1.savefig(path + "AD4020.png")
            self.fig2.savefig(path + "LTC2500.svg")
            self.fig2.savefig(path + "LTC2500.png")
            self.fig3.savefig(path + "intADC.svg")
            self.fig3.savefig(path + "intADC.png")
            # save the data as csv file
            outarr = None
            if self.viewType.get() == "Time series":
                outarr = np.asarray([self.x, self.data[0], self.data[1], self.data[2]])
                outarr = outarr.transpose()
            else:
                outarr = np.vstack((self.line1[1][0:-1], self.line1[0], 
                                    self.line2[1][0:-1], self.line2[0],
                                    self.line3[1][0:-1], self.line3[0]))
                outarr = outarr.transpose()
            np.savetxt(path + ".csv", outarr, delimiter=",")
            # display the saved message
            self.saveLabel1.configure(text="Last file:\n " + path)
            # OLD: save the data as text
            #f = open(path + ".txt", mode = "w")
            #f.write(str(self.data[0]))
            #f.close
            # display the saved message
            #self.saveLabel1.configure(text="Saved as " + path + "!")
            # schedule message removal
            #self.window.after(2000, lambda: self.saveLabel1.configure(text=""))
        self.saveButton1.bind("<Button-1>", updateSaveLabel1)
        toolbar1 = L.VerticalPlotToolbar(canvas1, self.saveFrame1)
        toolbar1.update()
        toolbar1.pack_forget()
        self.uiElements.append(toolbar1)
        self.uiGridParams.append([2, 0, 1, 1, "NW"])
        # Create canvas for the time series of the LTC2500
        self.fig2 = Figure(figsize=(5, 2), layout='constrained')
        self.ax2 = self.fig2.add_subplot(111)
        self.ax2.set_xlabel("Time (s)")
        self.ax2.set_ylabel("Voltage LTC2500 (V)")
        # Set time axis limits to match data
        self.ax2.set_xlim([0, tMax])
        self.line2, = self.ax2.plot(self.x, self.data[1], 'b-', label='LTC2500 voltage')
        self.legend2 = self.ax2.legend(loc='upper right', title="Average : 0V \nStd. dev.: 0V")
        self.legend2.get_title().set_multialignment('left')
        canvas2 = FigureCanvasTkAgg(self.fig2)
        canvas2.draw()
        self.uiElements.append(canvas2.get_tk_widget())
        self.uiGridParams.append([2, 0, 1, 2, "NESW"])
        # Create data tip for canvas 1
        self.dataTip2 = L.dataTip(canvas2, self.ax2, 0.01, self.line2)
        # Create frame for saving the plot
        self.saveFrame2 = Frame()
        self.uiElements.append(self.saveFrame2)
        self.uiGridParams.append([2, 2, 1, 1, "NW"])
        # Create save button
        #self.saveButton2 = Button(master=self.saveFrame2, text=u"\U0001F4BE", font=("TkDefaultFont", 60))
        #self.uiElements.append(self.saveButton2)
        #self.uiGridParams.append([0, 0, 1, 1, ""])
        ## Create label to display saved message
        #self.saveLabel2 = Label(master=self.saveFrame2)
        #self.uiElements.append(self.saveLabel2)
        #self.uiGridParams.append([1, 0, 1, 1, ""])
        #def updateSaveLabel2(event):
        #    path = L.savePath("Time Series LTC2500", self.dir)
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
        # Create canvas for the time series of the internal ADC
        self.fig3 = Figure(figsize=(5, 2), layout='constrained')
        self.ax3 = self.fig3.add_subplot(111)
        self.ax3.set_xlabel("Time (s)")
        self.ax3.set_ylabel("Voltage Internal ADC (V)")
        # Set time axis limits to match data
        self.ax3.set_xlim([0, tMax])
        self.line3, = self.ax3.plot(self.x, self.data[2], 'b-', label='Internal ADC voltage')
        self.legend3 = self.ax3.legend(loc='upper right', title="Average : 0V \nStd. dev.: 0V")
        self.legend3.get_title().set_multialignment('left')
        canvas3 = FigureCanvasTkAgg(self.fig3)
        canvas3.draw()
        self.uiElements.append(canvas3.get_tk_widget())
        self.uiGridParams.append([3, 0, 1, 2, "NESW"])
        # Create data tip for canvas 3
        self.dataTip3 = L.dataTip(canvas3, self.ax3, 0.01, self.line3)
        # Create frame for saving the plot
        self.saveFrame3 = Frame()
        self.uiElements.append(self.saveFrame3)
        self.uiGridParams.append([3, 2, 1, 1, "NW"])
        # Create save button
        #self.saveButton3 = Button(master=self.saveFrame3, text=u"\U0001F4BE", font=("TkDefaultFont", 60))
        #self.uiElements.append(self.saveButton3)
        #self.uiGridParams.append([0, 0, 1, 1, ""])
        ## Create label to display saved message
        #self.saveLabel3 = Label(master=self.saveFrame3)
        #self.uiElements.append(self.saveLabel3)
        #self.uiGridParams.append([1, 0, 1, 1, ""])
        #def updateSaveLabel3(event):
        #    path = L.savePath("Time Series Internal ADC", self.dir)
        #    # save the image
        #    self.fig1.savefig(path + ".svg")
        #    # save the data as text
        #    f = open(path + ".txt", mode = "w")
        #    f.write(str(self.data[2]))
        #    f.close
        #    # display the saved message
        #    self.saveLabel3.configure(text="Saved as " + path + "!")
        #    # schedule message removal
        #    self.window.after(2000, lambda: self.saveLabel3.configure(text=""))
        #self.saveButton3.bind("<Button-1>", updateSaveLabel3)
        toolbar3 = L.VerticalPlotToolbar(canvas3, self.saveFrame3)
        toolbar3.update()
        toolbar3.pack_forget()
        self.uiElements.append(toolbar3)
        self.uiGridParams.append([2, 0, 1, 1, "NW"])
        self.waitLabel = Label(text="Initializing... ",
                               font=("", 100))
        self.updateAll(True)
        self.waitLabel.grid_forget()
        # Display the widgets
        L.buildUI(self.uiElements, self.uiGridParams)
        # Maximize the window
        self.window.attributes("-zoomed", True)
        # Start the reading thread
        self.port.start(maxSize=self.dataSizeMax*3*4)
        # Start the serial connection monitor
        self.window.after(0, self.checkConnection)
        # Execute the function to read with the mainloop of the window (this is probably not the best solution)
        self.window.mainloop()
    
    # Update all board values since the program might still be running with different values from a previous session
    def updateAll(self, init):
        pre = "Initializing... "
        if not init:
            pre = "Restoring Settings... "
        self.waitLabel.grid(row=0, column=0, columnspan=2, sticky="WE")
        self.waitLabel.configure(text=pre + "\\")
        self.window.update_idletasks()
        self.handle_updateFreq()
        time.sleep(0.005)
        self.waitLabel.configure(text=pre + "|")
        self.window.update_idletasks()
        self.handle_updateSize()
        time.sleep(0.005)
        self.waitLabel.configure(text=pre + "/")
        self.window.update_idletasks()
        self.handle_updateOvers()
        time.sleep(0.005)
        self.waitLabel.configure(text=pre + "-")
        self.window.update_idletasks()
        if self.signal.get() == "Voltage":
            self.handle_signalVoltage()
        else:
            self.handle_signalRaw()
        time.sleep(0.005)
        self.waitLabel.configure(text=pre + "\\")
        self.window.update_idletasks()
        self.handle_updateTriggerSource()
        time.sleep(0.005)
        self.waitLabel.configure(text=pre + "|")
        self.window.update_idletasks()
        self.handle_updateThreshold()
        time.sleep(0.005)
        self.waitLabel.configure(text=pre + "/")
        self.window.update_idletasks()
        if self.flank.get() == "Falling":
            self.handle_flankFalling()
        else:
            self.handle_flankRising()
        time.sleep(0.005)
        self.waitLabel.configure(text=pre + "-")
        self.window.update_idletasks()
        self.port.writeL('activate AD4020')
        time.sleep(0.005)
        self.waitLabel.configure(text=pre + "\\")
        self.window.update_idletasks()
        self.port.writeL('activate LTC2500')
        time.sleep(0.005)
        self.waitLabel.configure(text=pre + "|")
        self.window.update_idletasks()
        self.port.writeL('activate Internal ADC')
        time.sleep(0.005)
    
    # Event handler for samplerate entry box
    def handle_updateFreq(self, event=0):
        # Stop reading during update
        reactivate = False
        if self.reading:
            reactivate = True
            self.reading = False
        newSamplerate = L.toFloat(self.freqEntry.get())
        if newSamplerate != None:
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
            self.updateTimeAxes()
            # Clear serial buffer
            self.port.clearBuffer()
            self.readNext = True
        self.samplerateV.set(str(self.samplerate))
        self.timeLabel['text'] = "Time/series: %.4fs" %(self.dataSize * self.oversamples / self.samplerate)
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
                self.data[0] = self.data[0][self.dataSize-newSize:self.dataSize]
                self.data[1] = self.data[1][self.dataSize-newSize:self.dataSize]
                self.data[2] = self.data[2][self.dataSize-newSize:self.dataSize]
            else:
                self.data[0] = [0]*(newSize - self.dataSize) + self.data[0]
                self.data[1] = [0]*(newSize - self.dataSize) + self.data[1]
                self.data[2] = [0]*(newSize - self.dataSize) + self.data[2]
            # Update variable for data size
            self.dataSize = newSize
            # Write command to serial port
            self.port.writeL('set dataSize ' + str(self.dataSize))
            # Update the data of the plots (if applicable)
            if self.viewType.get() == "Time series":
                self.line1.set_ydata(self.data[0])
                self.line2.set_ydata(self.data[1])
                self.line3.set_ydata(self.data[2])
            self.updateTimeAxes()
            # Clear serial buffer
            self.port.clearBuffer()
            self.readNext = True
        self.dataSizeV.set(str(self.dataSize))
        self.timeLabel['text'] = "Time/series: %.4fs" %(self.dataSize * self.oversamples / self.samplerate)
        self.window.update_idletasks()
        # Reactivate reading if paused by this function
        if reactivate:
            self.reading = True
            self.window.after(0, self.readDisp)
    
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
            self.updateTimeAxes()
            # Clear serial buffer
            self.port.clearBuffer()
            self.readNext = True
        self.oversamplesV.set(str(self.oversamples))
        self.timeLabel['text'] = "Time/series: %.4fs" %(self.dataSize * self.oversamples / self.samplerate)
        self.window.update_idletasks()
        # Reactivate reading if paused by this function
        if reactivate:
            self.reading = True
            self.window.after(0, self.readDisp)
    
    # Callback function for changing the signal type to raw value
    def handle_signalVoltage(self, event=0):
        self.signal.set("Voltage")
        self.signalPrev = self.signal.get()
        self.unit = "V"
        self.labelAxes()
        # Write command to serial port
        self.port.writeL("set signalType voltage")
    
    # Callback function for changing the signal type to raw value
    def handle_signalRaw(self, event=0):
        self.signal.set("Raw value")
        self.signalPrev = self.signal.get()
        self.unit = ""
        self.labelAxes()
        # Write command to serial port
        self.port.writeL("set signalType raw")
    
    # Function for displaying correct labelling of the axes
    def labelAxes(self):
        if self.signal.get() == "Raw value":
            self.dataAD4020 = "Raw value AD4020"
            self.dataLTC2500 = "Raw value LTC2500"
            self.dataInternal = "Raw value Internal ADC"
        elif self.signal.get() == "Voltage":
            self.dataAD4020 = "Voltage AD4020 (V)"
            self.dataLTC2500 = "Voltage LTC2500 (V)"
            self.dataInternal = "Voltage internal ADC (V)"
        if self.viewType.get() == "Time series":
            self.ax1.set_xlabel("Time (s)")
            self.ax1.set_ylabel(self.dataAD4020)
            self.ax2.set_xlabel("Time (s)")
            self.ax2.set_ylabel(self.dataLTC2500)
            self.ax3.set_xlabel("Time (s)")
            self.ax3.set_ylabel(self.dataInternal)
        else:
            self.ax1.set_xlabel(self.dataAD4020)
            self.ax1.set_ylabel("Data frequency")
            self.ax2.set_xlabel(self.dataLTC2500)
            self.ax2.set_ylabel("Data frequency")
            self.ax3.set_xlabel(self.dataInternal)
            self.ax3.set_ylabel("Data frequency")
    
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
        self.ax3.cla()
        self.line1, = self.ax1.plot(self.x, self.data[0], 'b-', label='AD4020 voltage')
        self.line2, = self.ax2.plot(self.x, self.data[1], 'b-', label='LTC2500 voltage')
        self.line3, = self.ax3.plot(self.x, self.data[2], 'b-', label='Internal ADC voltage')
        self.labelAxes()
        self.updateTimeAxes()
    
    # Updates the time axes for data plots
    def updateTimeAxes(self):
        # Maximum time value
        tMax = (self.dataSize-1)*self.oversamples/self.samplerate
        # Update values for time axes
        self.x = np.linspace(0, tMax, self.dataSize)
        # Update the data of the plots (if applicable)
        if self.viewType.get() == "Time series":
            # Update the axes
            self.line1.set_xdata(self.x)
            self.line2.set_xdata(self.x)
            self.line3.set_xdata(self.x)
            # Set time axes scale
            self.ax1.set_xlim([0, tMax])
            self.ax2.set_xlim([0, tMax])
            self.ax3.set_xlim([0, tMax])
        # Update the canvases
        L.updateCanvas(self.fig1.canvas, self.ax1, False, True)
        L.updateCanvas(self.fig2.canvas, self.ax2, False, True)
        L.updateCanvas(self.fig3.canvas, self.ax3, False, True)
    
    # Event handler for trigger source selector
    def handle_updateTriggerSource(self, event=0):
        self.port.writeL('set triggerSource ' + str(self.tSelect.get()))
        if self.tSelect.get() == "Untriggered (roll)":
            self.thresholdScale["state"] = DISABLED
            self.fallingButton["state"] = DISABLED
            self.risingButton["state"] = DISABLED
        elif self.tSelect.get() == "Schmitt trigger":
            self.thresholdScale["state"] = DISABLED
        else:
            self.thresholdScale["state"] = NORMAL
            self.fallingButton["state"] = NORMAL
            self.risingButton["state"] = NORMAL
    
    # Event handler for trigger threshold scale
    def handle_updateThreshold(self, event=0):
        self.port.writeL('set threshold ' + str(self.thresholdScale.get()))
    
    # Event handler for trigger edge selector rising
    def handle_flankRising(self, event=0):
        self.flank.set("Rising")
        self.port.writeL('set flank ' + str(self.flank.get()))
    
    # Event handler for trigger edge selector falling
    def handle_flankFalling(self, event=0):
        self.flank.set("Falling")
        self.port.writeL('set flank ' + str(self.flank.get()))

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
        rawValues = self.port.readB(self.dataSize*3*4)
        # Only process data, if there was any read
        if rawValues != "not enough data":
            # Discard any extra data on the port
            self.port.clearBuffer()
            # Prepare for next read
            self.readNext = True
            values = list(struct.unpack("%df" %(self.dataSize*3), rawValues))
            # Store the different parts to the different sub arrays of the data buffer
            self.data[0] = values[0:self.dataSize]
            self.data[1] = values[self.dataSize:2*self.dataSize]
            self.data[2] = values[2*self.dataSize:3*self.dataSize]
            # Display the values
            if self.viewType.get() == "Time series":
                self.line1.set_ydata(self.data[0])
                self.line2.set_ydata(self.data[1])
                self.line3.set_ydata(self.data[2])
                self.line1.set_label(self.dataAD4020)
                self.line2.set_label(self.dataLTC2500)
                self.line3.set_label(self.dataInternal)
            elif self.viewType.get() == "Hist. (auto)":
                self.ax1.cla()
                self.ax2.cla()
                self.ax3.cla()
                self.line1 = self.ax1.hist(self.data[0], histtype='step', label=self.dataAD4020)
                self.line2 = self.ax2.hist(self.data[1], histtype='step', label=self.dataLTC2500)
                self.line3 = self.ax3.hist(self.data[2], histtype='step', label=self.dataInternal)
            elif self.viewType.get() == "Hist. (bin=1)":
                self.ax1.cla()
                self.ax2.cla()
                self.ax3.cla()
                self.line1 = self.ax1.hist(self.data[0], bins=np.arange(min(self.data[0]), max(self.data[0]) + 2, 1), histtype='step', label=self.dataAD4020)
                self.line2 = self.ax2.hist(self.data[1], bins=np.arange(min(self.data[1]), max(self.data[1]) + 2, 1), histtype='step', label=self.dataLTC2500)
                self.line3 = self.ax3.hist(self.data[2], bins=np.arange(min(self.data[2]), max(self.data[2]) + 2, 1), histtype='step', label=self.dataInternal)
            # Update the legends
            title_unit = self.unit
            title_stdfac = 1
            if self.unit == 'V':
                title_stdfac = 1000
                title_unit = 'mV'
            self.legend1 = self.ax1.legend(loc='upper right', title="Average : %.6f%s \nStd. dev.: %.6f%s" %(np.mean(self.data[0]), self.unit, np.std(self.data[0])*title_stdfac, title_unit))
            self.legend2 = self.ax2.legend(loc='upper right', title="Average : %.6f%s \nStd. dev.: %.6f%s" %(np.mean(self.data[1]), self.unit, np.std(self.data[1])*title_stdfac, title_unit))
            self.legend3 = self.ax3.legend(loc='upper right', title="Average : %.6f%s \nStd. dev.: %.6f%s" %(np.mean(self.data[2]), self.unit, np.std(self.data[2])*title_stdfac, title_unit))
            self.legend1.get_title().set_multialignment('left')
            self.legend2.get_title().set_multialignment('left')
            self.legend3.get_title().set_multialignment('left')
            # Label axes correctly
            self.labelAxes()
            # Update the canvases
            L.updateCanvas(self.fig1.canvas, self.ax1, False, True)
            L.updateCanvas(self.fig2.canvas, self.ax2, False, True)
            L.updateCanvas(self.fig3.canvas, self.ax3, False, True)
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


if __name__ == '__main__':
    gui = DSMVGUI()