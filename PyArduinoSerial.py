from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QWidget, QGridLayout, QApplication)
from pyqtgraph import PlotWidget, plot
from pyqtgraph import QtCore, QtGui
import pyqtgraph as pg
import sys  # We need sys so that we can pass argv to QApplication
import os

from threading import Thread
import serial
import time
import collections
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import struct
import pandas as pd
import copy as copy
import numpy as np

# Now use a palette to switch to dark colors:
palette = QtGui.QPalette()
palette.setColor(QtGui.QPalette.Window, QtGui.QColor(53, 53, 53))
palette.setColor(QtGui.QPalette.WindowText, Qt.white)
palette.setColor(QtGui.QPalette.Base, QtGui.QColor(25, 25, 25))
palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(53, 53, 53))
palette.setColor(QtGui.QPalette.ToolTipBase, Qt.white)
palette.setColor(QtGui.QPalette.ToolTipText, Qt.white)
palette.setColor(QtGui.QPalette.Text, Qt.white)
palette.setColor(QtGui.QPalette.Button, QtGui.QColor(53, 53, 53))
palette.setColor(QtGui.QPalette.ButtonText, Qt.white)
palette.setColor(QtGui.QPalette.BrightText, Qt.red)
palette.setColor(QtGui.QPalette.Link, QtGui.QColor(42, 130, 218))
palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(42, 130, 218))
palette.setColor(QtGui.QPalette.HighlightedText, Qt.black)


""" SERIAL CLASS """
class SerialPlot:
    def __init__(self, bufferLength = 100, dataNumBytes = 2):
        self.plotMaxLength = bufferLength
        self.dataType = None
        
        if dataNumBytes == 2:
            self.dataType = 'h'     # 2 byte integer
        elif dataNumBytes == 4:
            self.dataType = 'f'     # 4 byte float
        elif dataNumBytes == 8:
            self.dataType = 'd'     # 4 byte float
        self.dataNumBytes = dataNumBytes
        
        self.dataNumChannels = 1 + 2 # time + 1 analog read
        self.TxBuffer = ""
        self.RxBuffer = bytearray(self.dataNumChannels * dataNumBytes)
        self.data = []
        for i in range(self.dataNumChannels):   # give an array for each type of data and store them in a list
            self.data.append(collections.deque([0] * bufferLength, maxlen=bufferLength))
        self.isRun = True
        self.isReceiving = False
        self.thread = None
        self.plotTimer = 0
        self.previousTimer = 0
        
        
    def connectSerial(self,serialPort,serialBaud):
        self.serialBaud = serialBaud
        self.serialPort = serialPort
        print('Trying to connect to: ' + str(self.serialPort) + ' at ' + str(self.serialBaud) + ' BAUD.')
        try:
            self.serialConnection = serial.Serial(self.serialPort, self.serialBaud, timeout=4)
            print('Connected to ' + str(self.serialPort) + ' at ' + str(self.serialBaud) + ' BAUD.')
        except:
            print("Failed to connect with " + str(self.serialPort) + ' at ' + str(self.serialBaud) + ' BAUD.')
        
    def writeSerial(self):
        toSend = self.TxBuffer                  # Get the Buffer
        toSend = toSend.encode()                # Encode to Bytes
        self.serialConnection.write(toSend)     # Send Over Serial
        self.serialConnection.flushInput()      # Flush Serial (HW) buffer
        self.serialConnection.flushOutput()     # Flush Serial (HW) buffer
        self.TxBuffer = ""                      # Empty Tx SW buffer

        
    def readSerialStart(self):
        print('Reading Started')
        self.serialConnection.reset_input_buffer()
        if self.thread == None:
            print("Thread Started")
            self.thread = Thread(target=self.backgroundThread)
            self.thread.start()
            self.isRun = True
            # Block till we start receiving values
            while self.isReceiving != True:
                time.sleep(0.5)
        if self.thread.is_alive() == False:
            print("Thread Started")
            self.thread = Thread(target=self.backgroundThread)
            self.thread.start()
            # Block till we start receiving values
            self.isRun = True
            while self.isReceiving != True:
                time.sleep(0.5)


    def getSerialDataRaw(self):
        privateData = copy.deepcopy(self.RxBuffer[:])    # so that the 3 values in our plots will be synchronized to the same sample time
        for i in range(self.dataNumChannels):
           data = privateData[(i*self.dataNumBytes):(self.dataNumBytes + i*self.dataNumBytes)]
           value,  = struct.unpack(self.dataType, data)
           self.data[i].append(value)    # we get the latest data point and append it to our array#self.data.append(value)    # we get the latest data point and append it to our array

    def backgroundThread(self):    # retrieve data
        time.sleep(0.1)  # give some buffer time for retrieving data
        self.serialConnection.reset_input_buffer()
        self.serialConnection.flushInput()
        print('Reseting buffer...')
        while (self.isRun):
            if (self.serialConnection.inWaiting() > 1):
                self.serialConnection.readinto(self.RxBuffer)
                self.isReceiving = True
                self.readyToConvert = True
                self.getSerialDataRaw()
       
    
    def readSerialStop(self):
        try:
            self.isRun = False
            self.thread.join()
            print("Reading stopped...")
        except:
            print("Nothing to stop")
    
    
    def close(self):
        try:
            self.readSerialStop()
            self.serialConnection.close()
            print('Disconnected...')
            print(self.thread)
        except:
            print("Nothing to Close")


""" GUI CLASS """
class PlotWindow(QWidget):                       
    def __init__(self,parent,name,data):
        super().__init__()
        self.parent = parent
        self.data = data
        self.name = name
        self.setWindowTitle(name)
        
        self.trigPoint = 250

        self.initUI()
        
        self.timerPlot = QtCore.QTimer()
        self.timerPlot.timeout.connect(self.plotUI)
        
    def initUI(self):
        self.guiplot = pg.PlotWidget()
        
        self.startPlot = QtGui.QPushButton("Start")
        self.startPlot.clicked.connect(self.startPlotTimer)
        self.stopPlot = QtGui.QPushButton("Stop")
        self.stopPlot.clicked.connect(self.stopPlotTimer)

        
        self.enaTrig = QtGui.QPushButton("Trigger ON")
        self.enaTrig.clicked.connect(self.enableTrigger)
        self.disablTrig = QtGui.QPushButton("Trigger OFF")
        self.disablTrig.clicked.connect(self.disableTrigger)
        self.triggerPointLineEdit = QtGui.QLineEdit()
        self.triggerPointLineEdit.setValidator(QtGui.QIntValidator())
        self.triggerPointLineEdit.setFixedWidth(110)
        self.triggerPointLabel = QtGui.QLabel("OFF - No Trigger")
        self.bTrigEna = False
        self.triggerPointLineEdit.setEnabled(self.bTrigEna)
        
        self.exprtOnceRadioBut = QtGui.QRadioButton("Current view")
        self.exprtOnceRadioBut.setChecked(True)
        #self.exprtOnceRadioBut.toggled.connect()
        self.exprtContinousRadioBut = QtGui.QRadioButton("For duration [ms]")
        #self.exprtContinousRadioBut.toggled.connect()
        self.exprtPltDurLineEdit = QtGui.QLineEdit()
        self.exprtPltDurLineEdit.setValidator(QtGui.QIntValidator())
        self.exprtPltDurLineEdit.setText("1000")
        self.exprt2FileLineEdit = QtGui.QLineEdit()
        self.exprt2FileLineEdit.setText("ExportFileName")
        self.exportPlot = QtGui.QPushButton("Export")
        self.exportPlot.clicked.connect(self.exportData)

        # // Layout Management \\ #
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.guiplot)
        # Vbox in right Hbox
        vbox = QtWidgets.QVBoxLayout() 
        hbox.addLayout(vbox)
        
        ## TopHbox in Vbox 
        hboxTop = QtGui.QGroupBox("Plot Control")
        hboxTop.setFixedWidth(250)
        ### Grid in TopHbox
        PlotCmdGrid = QGridLayout()
        PlotCmdGrid.addWidget(self.startPlot,0,0)
        PlotCmdGrid.addWidget(self.stopPlot,0,1)
        hboxTop.setLayout(PlotCmdGrid)
        vbox.addWidget(hboxTop)
        
        ## Midbox in Vbox 
        hboxMid = QtGui.QGroupBox("Trigger Control")
        hboxMid.setFixedWidth(250)
        ### Grid in Midbox
        TrigCmdGrid = QGridLayout()
        TrigCmdGrid.addWidget(self.enaTrig,1,0)
        TrigCmdGrid.addWidget(self.disablTrig,1,1)
        TrigCmdGrid.addWidget(self.triggerPointLabel,2,0)
        TrigCmdGrid.addWidget(self.triggerPointLineEdit,2,1)
        hboxMid.setLayout(TrigCmdGrid)
        vbox.addWidget(hboxMid)
        
        ## BotHbox in Vbox 
        hboxBot = QtGui.QGroupBox("Export Control")
        hboxBot.setFixedWidth(250)
        ### Grid in Botbox
        ExprtCmdGrid = QGridLayout()
        ExprtCmdGrid.addWidget(self.exprtOnceRadioBut,0,0)
        ExprtCmdGrid.addWidget(self.exprtContinousRadioBut,1,0)
        ExprtCmdGrid.addWidget(self.exprtPltDurLineEdit,1,1)
        ExprtCmdGrid.addWidget(self.exprt2FileLineEdit,2,0)
        ExprtCmdGrid.addWidget(self.exportPlot,2,1)
        hboxBot.setLayout(ExprtCmdGrid)
        vbox.addWidget(hboxBot)
                
        self.setLayout(hbox)
        
        
    def startPlotTimer(self):
        self.parent.s.readSerialStart()
        self.timerPlot.start(50)
        
        
    def stopPlotTimer(self):
        self.timerPlot.stop()
    
    def enableTrigger(self):
        self.bTrigEna = True
        self.triggerPointLineEdit.setEnabled(True)
        self.triggerPointLabel.setText("ON - Trigger at [ms]")
        
    def disableTrigger(self):
        self.bTrigEna = False
        self.triggerPointLineEdit.setEnabled(False)
        self.triggerPointLabel.setText("OFF - No Trigger")
        
    def plotUI(self):
        """ Plot the data , consider trigger state and plot trigger
        """
        xAxis = np.arange(self.parent.s.plotMaxLength)
        pen = pg.mkPen(color=(120, 120, 250), width=2) 
        self.guiplot.plot(xAxis, self.data[2],clear=True,pen=pen)

        if self.bTrigEna == True:
            pen = pg.mkPen(color=(250, 250, 100), width=2)
            self.guiplot.plot([self.data[0][self.trigPoint],self.data[0][self.trigPoint]], [min(self.data[1]),max(self.data[1])],pen=pen)
            if (self.data[1][self.trigPoint] >= int(self.triggerPointLineEdit.text())):
                self.stopPlotTimer()
                
        self.guiplot.plotItem.showGrid(100,100)
        
    def exportData(self):
        if self.exprtOnceRadioBut.isChecked() is True:
            data_dict = self.data
            df = pd.DataFrame(data_dict)
            df = df.T
            name = self.exprt2FileLineEdit.text()
            name = name + ".csv"
            df.to_csv(name)
        if self.exprtContinousRadioBut.isChecked() is True:
            print("Continous Exporting NOT done yet")
        
    def closeEvent(self, event):
        self.timerPlot.stop()
        self.parent.childWindowClosedEvent(self.name)
        


class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.setWindowTitle("Serial Interface")
        
        self.PlotChildWinsOpen = {}
        
        portName = '/dev/ttyUSB0'
        portName = "COM8"
        baudRate = 9600
        self.maxPlotLength = 100
        dataNumBytes = 2       # number of bytes of 1 data point
        
       
    def initUI(self):
        
        self.pushButtonSerial = QtGui.QPushButton("Serial Connect")
        self.pushButtonSerial.clicked.connect(self.serialToggle)
        self.pushButtonSerial.setCheckable(True)
        
        self.LineEditBytesNmbr = QtGui.QLineEdit()
        self.LineEditBytesNmbr.setText("2")
        self.labelBytesNmbr = QtGui.QLabel("Receiving Bytes")
        
        self.LineEditPort = QtGui.QLineEdit()
        self.LineEditPort.setText("COM8")
        self.labelPort = QtGui.QLabel("COM Port")
        
        self.LineEditBaud = QtGui.QLineEdit()
        self.LineEditBaud.setText("38400")
        self.labelBaud = QtGui.QLabel("Baudrate")
        
        self.pushButtonSend = QtGui.QPushButton("Send to Arduino")
        self.pushButtonSend.clicked.connect(self.sendtoArduino)
        
        self.LineEditPlotter = QtGui.QLineEdit()
        self.LineEditPlotter.setText("Serial Visualizer 1")
        self.pushButtonPlotter = QtGui.QPushButton("Open Plotter")
        self.pushButtonPlotter.clicked.connect(self.openWindow)
        
        self.LineEditID = QtGui.QLineEdit()
        self.LineEditID.setText("Identifier")
        
        self.LineEditValue = QtGui.QLineEdit()
        self.LineEditValue.setText("Value")
        
        # Create Logo
        logo = QtGui.QLabel() 
        pixmap = QtGui.QPixmap('logoDarkTheme.png')
        pixmap = pixmap.scaledToHeight(30,Qt.SmoothTransformation)
        logo.setPixmap(pixmap)
        logo.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        
        # Create Footer
        footerLeft = QtGui.QLabel("OpenSource") 
        
        # Define Main Layout
        mainLayout = QtWidgets.QVBoxLayout()
        
        ## Define Serial Setup
        hboxSer = QtGui.QGroupBox("Serial Setup")
        hboxSer.setFixedWidth(250)
        hboxSerGrid = QGridLayout()
        hboxSerGrid.addWidget(self.labelBytesNmbr,0,0)
        hboxSerGrid.addWidget(self.labelPort,1,0)
        hboxSerGrid.addWidget(self.labelBaud,2,0)
        hboxSerGrid.addWidget(self.LineEditBytesNmbr,0,1)
        hboxSerGrid.addWidget(self.LineEditPort,1,1)
        hboxSerGrid.addWidget(self.LineEditBaud,2,1)
        hboxSerGrid.addWidget(self.pushButtonSerial,3,0)
        hboxSer.setLayout(hboxSerGrid)
        mainLayout.addWidget(hboxSer)
        
        ## Define Tx 
        hboxTx = QtGui.QGroupBox("Tx")
        hboxTx.setFixedWidth(250)
        ReceiveGrid = QGridLayout()
        ReceiveGrid.addWidget(self.pushButtonSend,0,0)
        ReceiveGrid.addWidget(self.LineEditID,1,0)
        ReceiveGrid.addWidget(self.LineEditValue,1,1)
        hboxTx.setLayout(ReceiveGrid)
        mainLayout.addWidget(hboxTx)
        
        ## Define Rx
        hboxRx = QtGui.QGroupBox("Rx")
        hboxRx.setFixedWidth(250)
        ReceiveGrid = QGridLayout()
        ReceiveGrid.addWidget(self.LineEditPlotter,0,0)
        ReceiveGrid.addWidget(self.pushButtonPlotter,0,1)
        hboxRx.setLayout(ReceiveGrid)
        mainLayout.addWidget(hboxRx)
        
        ## Define Footer
        footer = QWidget()
        footerGrid = QGridLayout()
        footerGrid.addWidget(logo,0,2)
        footerGrid.addWidget(footerLeft,0,0)
        footer.setLayout(footerGrid)
        mainLayout.addWidget(footer)
     
        self.setLayout(mainLayout)
        
        
    def serialToggle(self):
        try:
            if self.pushButtonSerial.isChecked():
                self.s = SerialPlot(self.maxPlotLength, int(self.LineEditBytesNmbr.text()))   # initializes all required variables
                self.s.connectSerial(self.LineEditPort.text(),self.LineEditBaud.text())               
            else:
                self.s.close()
        except:
            print("Communication settings incorrect")
        
    def openWindow(self):
        try:
            name = self.LineEditPlotter.text()
            w = PlotWindow(self,name,self.s.data)
            w.show()
            self.PlotChildWinsOpen[name] = w
        except:
            print("Serial NOT open.")

    def childWindowClosedEvent(self,childWinName):
        self.PlotChildWinsOpen.pop(childWinName,None)
        
    def closeEvent(self, event):
        self.s.close()
        
    def sendtoArduino(self):
        self.s.TxBuffer = self.LineEditID.text() + ":" + self.LineEditValue.text()
        self.s.writeSerial()

        
 
############################################
if __name__ == '__main__':
    app = QtCore.QCoreApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        
    app.setStyle("Fusion")
    app.setPalette(palette)
    
    w = Window()
    w.show()

    app.exec_()

