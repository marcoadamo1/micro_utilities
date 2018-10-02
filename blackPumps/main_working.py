import tkinter as tk
import serial
import time
import glob
import logging
from tkinter.constants import W, LEFT, TOP, GROOVE, BOTTOM
import sys
from tkinter import ttk
import threading


FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
SW_INFO = "harvardPHD2000 v.0.1.0"
DEBUG = False

#Create every time a file (loosing the old)
#logging.basicConfig(filename = 'pumPy.log', level=logging.DEBUG, filemode='w', format=FORMAT)
#Append to the same file
logging.basicConfig(filename = 'pumPy.log', level=logging.DEBUG, filemode='a', format=FORMAT)
logging.info("%==============================================================")
logging.info("%============ Software version: " + SW_INFO)
logging.info("%==============================================================")

commands = {
    #  @@@ commands @@@
    'Start': 'RUN', #Infuse (forward direction)
    'Withdraw': 'REV', #Start (reverse direction) Not accessible on Infusion model
    'Stop': 'STP',
    'ClearVol': 'CLV', #Clear volume accumulator to zero
    'ClearTarget': 'CLT', #Clear target volume to zero
    'RateMLM':'MLM', 
    'RateULM':'ULM', 
    'RateMLH':'MLH', 
    'RateULH':'ULH', 
    'SetDia':'MMD', # Set diameter, units are mm. Rate is set to 0
    'SetVol': 'MLT', # Set target infusion volume, units are ml
    #  @@@ queries @@@
    'Diameter': 'DIA', # Get diameter value, units in mm
    'Rate':'RAT', # Get rate value in current range units
    'Volume':'VOL', # Get current accumulated infused volume, units are ml
    'Target': 'TAR', # Get target volume, units are ml.
    'Version': 'VER', # Get model and version number 
    }

class blackPump(object):
    """ A syringe pump
    """ 
    def __init__(self, address):
        """Return a Customer object whose name is *name*.""" 
        self.address = str(address).zfill(2) #Id
        self.status = 'NOT DETECTED'            #stopped, running, etc
        self.diameter = '0'           #internal diameter
        self.rate = '0'               #pumping rate
        self.units = 'UNKNOWN'             #pumping units
        self.dispensed = '0'          #dispensed volume
        self.volume = '0'          #target volume
        #self.warnings = 'N/A'          #warnings
        self.firmware = 'N/A'          #warnings
        self.infuse = -1
        self.detected = False          #ToDo fix
#     def setAddress(self, address):
#         self.address = str(address).zfill(2)
#     def setDiameter(self, diameter):
#         #Maximum of 4 digits plus 1 decimal point
#         self.diameter = str(diameter).zfill(5)
        
    def getStatus(self):
        return self.status
    def getDiameter(self):
        return self.diameter
    def getRate(self):
        return self.rate
    def getVolume(self):
        return self.volume
    def getUnits(self):
        return self.units
    def getDispensed(self):
        return self.dispensed
#     def getWarnings(self):
#         return self.warnings
    def getFirmware(self):
        return self.firmware
    def getInfuse(self):
        return self.infuse

class PumPy_GUI(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self,master)
        self.pack()
        # DATA
        self.address1 = tk.IntVar()
        self.address2 = tk.IntVar()
        self.baudrate = tk.StringVar()
        self.COMnumber = tk.StringVar()
        self.emergency = False
    
        # PUMPS
        self.pump_A = blackPump('1')
        self.pump_B = blackPump('2')
        
        # SERIAL 
        self.ser = serial.Serial()
        # GUI
        self.createFrames()
        self.createWidgets()
        self.closing = False    
        
    #===========================================================================
    #============================ USER INTERFACE ===============================
    #===========================================================================  
    def createFrames(self):
        # Connection
        self.connectionFrame = tk.Frame()
        self.connectionFrame.pack(expand = False, side = TOP)
        
        # Pump scan
        self.scanFrame = tk.Frame()
        self.scanFrame.pack(expand = False, side = TOP)
        
        # Pump status
        self.displayFrame = tk.Frame()
        self.displayFrame.pack(expand = False, side = TOP)
        
        # Commands
        self.commands = tk.Frame()
        self.commands.pack(expand = False, side = TOP, pady = 8)
        
        # Functions
        self.functions = tk.Frame()
        self.functions.pack(expand = False, side = TOP, pady = 8)
        
        # Exit program
        self.exitFrame = tk.Frame()
        self.exitFrame.pack(expand = True, side = BOTTOM)
        
    def createWidgets(self):
        # CONNECTION
        self.labelSelectCOM = tk.Label(self.connectionFrame, text="Select a COM port:")
        self.labelSelectCOM.pack( side = LEFT)
        self.choseCOM()
        self.choseBaudrate()
        self.openCOM = tk.Button(self.connectionFrame, text="open", relief = GROOVE, command = self.openPort)
        self.openCOM.configure(fg = "red")
        self.openCOM.pack(side = LEFT)
        self.openCOM.focus()
        
        self.version_button = tk.Button(self.scanFrame, text="Scan Pumps", command=self.askFWVer, width = 15, height=3, relief=GROOVE, fg='blue')
        self.version_button.pack()
        
        #=======================================================================
        #########################  PUMP MANAGER  ###############################
        #=======================================================================
        #Start/stop pumps and diameter
        self.diameterLabel = tk.Label(self.commands, text = "Diameter")
        self.diameterLabel.grid(row=0, column=1)
        self.diameterLabel = tk.Label(self.commands, text = " ")
        self.diameterLabel.grid(row=0, column=3)
        self.diameterLabel = tk.Label(self.commands, text = "Rate")
        self.diameterLabel.grid(row=0, column=4)
        self.diameterLabel = tk.Label(self.commands, text = " ")
        self.diameterLabel.grid(row=0, column=7)
        self.startStopLabel = tk.Label(self.commands, text = "Command")
        self.startStopLabel.grid(row=0, column=8)
        self.startStopLabel = tk.Label(self.commands, text = "Volume (ml)")
        self.startStopLabel.grid(row=0, column=11)
        
        #PUMP 1
        line = 1
        dia_01 = tk.StringVar() 
        dia_01.set("0.000")
        vol_01 = tk.StringVar() 
        vol_01.set("1.000")
        rat_01 = tk.StringVar() 
        rat_01.set("0.000")
        dir_01 = tk.IntVar()
        dir_01.set(0)
        units_01 = tk.StringVar()
        self.pump_02_Label = tk.Label(self.commands, text = "PUMP 1")
        self.pump_02_Label.grid(row=line, column=0)
        #Diameter
        self.dia_01_Label = tk.Entry(self.commands, text = dia_01.get(), textvariable=dia_01, width = 10)
        self.dia_01_Label.grid(row=line, column=1)
        self.dia_01_setLabel = tk.Button(self.commands, text="Set", command=lambda: self.setDiam(self.pump_A, dia_01.get()))
        self.dia_01_setLabel.grid(row=line, column=2)
        #Rate        
        self.rat_01_Label = tk.Entry(self.commands, text = rat_01.get(), textvariable=rat_01, width = 10)
        self.rat_01_Label.grid(row=line, column=4)
        self.uni_01 = ttk.Combobox(self.commands, textvariable=units_01, width = 4)
        self.uni_01['values']=('MM','MH','UM','UH')
        self.uni_01.current(0) # 6
        self.uni_01.grid(row=line, column=5)
        self.rat_01_setLabel = tk.Button(self.commands, text="Set", command=lambda: self.setRate(self.pump_A, rat_01.get(), units_01.get()))
        self.rat_01_setLabel.grid(row=line, column=6)
        #Start/stop
        self.start_01_Label = tk.Button(self.commands, text="Start", relief=GROOVE, command=lambda: self.startStopPump(self.pump_A, True))
        self.start_01_Label.grid(row=line, column=8)
        self.stop_01_Label = tk.Button(self.commands, text="Stop", relief=GROOVE, command=lambda: self.startStopPump(self.pump_A, False))
        self.stop_01_Label.grid(row=line, column=9)
        self.filler_01 = tk.Label(self.commands, text = " ")
        self.filler_01.grid(row=line, column=10)
        #Volume
        self.vol_01_Label = tk.Entry(self.commands, text = vol_01.get(), textvariable=vol_01, width = 10)
        self.vol_01_Label.grid(row=line, column=11)
        self.vol_01_setLabel = tk.Button(self.commands, text="Set", command=lambda: self.setVolume(self.pump_A, vol_01.get()))
        self.vol_01_setLabel.grid(row=line, column=12)
        #Direction
        self.dir_01 = tk.Radiobutton(self.commands, text="INF", variable=dir_01, value=1, command=lambda: self.setDirection(self.pump_A, dir_01.get()))
        self.dir_01.grid(row=line, column=14)
        self.dir_01 = tk.Radiobutton(self.commands, text="WIT", variable=dir_01, value=2, command=lambda: self.setDirection(self.pump_A, dir_01.get()))
        self.dir_01.grid(row=line, column=15)
        
        #PUMP2
        line = 2
        dia_02 = tk.StringVar() 
        dia_02.set("0.000")
        vol_02 = tk.StringVar() 
        vol_02.set("1.000")
        rat_02 = tk.StringVar() 
        rat_02.set("0.000")
        dir_02 = tk.IntVar()
        dir_02.set(0)
        units_02 = tk.StringVar()
        self.pump_02_Label = tk.Label(self.commands, text = "PUMP 2")
        self.pump_02_Label.grid(row=line, column=0)
        #Diameter
        self.dia_02_Label = tk.Entry(self.commands, text = dia_02.get(), textvariable=dia_02, width = 10)
        self.dia_02_Label.grid(row=line, column=1)
        self.dia_02_setLabel = tk.Button(self.commands, text="Set", command=lambda: self.setDiam(self.pump_B, dia_02.get()))
        self.dia_02_setLabel.grid(row=line, column=2)
        #Rate
        self.rat_02_Label = tk.Entry(self.commands, text = rat_02.get(), textvariable=rat_02, width = 10)
        self.rat_02_Label.grid(row=line, column=4)
        self.uni_2 = ttk.Combobox(self.commands, textvariable=units_02, width = 4)
        self.uni_2['values']=('MM','MH','UM','UH')
        self.uni_2.current(0) # 6
        self.uni_2.grid(row=line, column=5)
        self.rat_02_setLabel = tk.Button(self.commands, text="Set", command=lambda: self.setRate(self.pump_B, rat_02.get(), units_02.get()))
        self.rat_02_setLabel.grid(row=line, column=6)
        #Start/stop
        self.start_02_Label = tk.Button(self.commands, text="Start", relief=GROOVE, command=lambda: self.startStopPump(self.pump_B, True))
        self.start_02_Label.grid(row=line, column=8)
        self.stop_02_Label = tk.Button(self.commands, text="Stop", relief=GROOVE, command=lambda: self.startStopPump(self.pump_B, False))
        self.stop_02_Label.grid(row=line, column=9)
        self.filler_02 = tk.Label(self.commands, text = " ")
        self.filler_02.grid(row=line, column=10)
        #Volume
        self.vol_02_Label = tk.Entry(self.commands, text = vol_02.get(), textvariable=vol_02, width = 10)
        self.vol_02_Label.grid(row=line, column=11)
        self.vol_02_setLabel = tk.Button(self.commands, text="Set", command=lambda: self.setVolume(self.pump_B, vol_02.get()))
        self.vol_02_setLabel.grid(row=line, column=12)
        #Direction
        self.dir_02 = tk.Radiobutton(self.commands, text="INF", variable=dir_02, value=1, command=lambda: self.setDirection(self.pump_B, dir_02.get()))
        self.dir_02.grid(row=line, column=14)
        self.dir_02 = tk.Radiobutton(self.commands, text="WIT", variable=dir_02, value=2, command=lambda: self.setDirection(self.pump_B, dir_02.get()))
        self.dir_02.grid(row=line, column=15)
        
        self.close_button = tk.Button(self.exitFrame, text="Close", command=self.my_quit)
        self.close_button.pack()           
        
        #DISPLAY STATUS
        self.table = ttk.Treeview(self.displayFrame, columns=('status', 'diameter', 'rate', 'volume', 'dispensed', 'firmware'), height = 3)
        self.table.column('#0', stretch = False, width = 70)
        self.table.heading('status', text='Status', anchor = W)
        self.table.column('status', stretch = False, width = 100)
        self.table.heading('diameter', text = 'Diameter', anchor = W)
        self.table.column('diameter', stretch = False, width = 57)
        self.table.heading('rate', text = 'Rate', anchor = W)
        self.table.column('rate', stretch = False, width = 70)
        self.table.heading('dispensed', text = 'Dispensed [ml]', anchor = W)
        self.table.column('dispensed', stretch = False, width = 120)
        self.table.heading('volume', text = 'Target volume [ml]', anchor = W)
        self.table.column('volume', stretch = False, width = 100)
        self.table.heading('firmware', text = 'Firmware', anchor = W)
        self.table.column('firmware', stretch = False, width = 90)
            
        self.table.insert("" , 0, iid='02', text="PUMP 2", values=(self.pump_B.getStatus(),self.pump_B.getDiameter(),self.pump_B.getRate(),self.pump_B.getVolume(),self.pump_B.getDispensed(),self.pump_B.getFirmware()))
        self.table.insert("" , 0, iid='01', text="PUMP 1", values=(self.pump_A.getStatus(),self.pump_A.getDiameter(),self.pump_A.getRate(),self.pump_A.getVolume(),self.pump_A.getDispensed(),self.pump_A.getFirmware())) 
        self.table.pack(side = LEFT)      
        
        
        ############### PUSH/PULL
        __vol = tk.StringVar() 
        __vol.set("0.000")
        __delay = tk.IntVar() 
        __delay.set(2)
        __iter = tk.IntVar() 
        __iter.set(1)
        self.__currIter = tk.IntVar() 
        self.__currIter.set(0)
        
        self.pp_setVol_lab = tk.Label(self.functions, text = "Infuse Volume [ml]")
        self.pp_setVol_lab.grid(row=0, column=0)
        self.pp_setVol_ent = tk.Entry(self.functions, text = __vol.get(), textvariable=__vol, width = 10)
        self.pp_setVol_ent.grid(row=0, column=1)
        
        self.pp_setDelay_lab = tk.Label(self.functions, text = "Run Delay [s]")
        self.pp_setDelay_lab.grid(row=0, column=2)
        self.pp_setDelay_ent = tk.Entry(self.functions, text = __delay.get(), textvariable=__delay, width = 10)
        self.pp_setDelay_ent.grid(row=0, column=3)
        
        self.pp_setCycles_lab = tk.Label(self.functions, text = "Iterations")
        self.pp_setCycles_lab.grid(row=0, column=4)
        self.pp_setCycles_ent = tk.Entry(self.functions, text = __iter.get(), textvariable=__iter, width = 10)
        self.pp_setCycles_ent.grid(row=0, column=5)
        
        self.pp_setCycles_lab = tk.Label(self.functions, text = "Current")
        self.pp_setCycles_lab.grid(row=0, column=6)
        self.pp_setCycles_ent = tk.Label(self.functions, text = self.__currIter.get(), textvariable=self.__currIter, width = 10)
        self.pp_setCycles_ent.grid(row=0, column=7)
        
        self.pp_button = tk.Button(self.functions, text="START", relief=GROOVE, 
                command=lambda: self.pushPull_thread(self.pump_A, self.pump_B, __vol.get(), __delay.get(), __iter.get()))
        self.pp_button.grid(row=0, column=8)
        
        self.pp_button = tk.Button(self.functions, text="STOP", relief=GROOVE, 
                command=self.emergencyStop)
        self.pp_button.grid(row=0, column=9)
        
    
    def askFWVer(self):
        a = ['01', '02']
        for x in a: #Check pumd IDs 01 and 02
            if (self.closing == False):
                logging.info("Looking for pump " + x)
                # RATE
                resp = []
                resp = self.serialWrite(x,  commands['Rate'], '')
                if DEBUG:
                    if x == '01':
                        resp = ['0xa', '0x20', '0x20', '0x31', '0x2e', '0x30', '0x30', '0x30', '0x30', '0x20', '0x6d', '0x6c', '0x2f', '0x6d', '0x6e', '0xd', '0xa', '0x31', '0x3a']
                    else:
                        resp = ['0xa', '0x20', '0x20', '0x31', '0x2e', '0x30', '0x30', '0x30', '0x30', '0x20', '0x6d', '0x6c', '0x2f', '0x6d', '0x6e', '0xd', '0xa', '0x32', '0x3a']
                
                if resp:
                    # Check status
                    resp = ''.join(self.fromLogToReadable(resp))
                    resp = resp.split() # Dodgy but it works
                    if x == '01':
                        self.pump_A.rate = resp[0] + ' ' + resp[1]
                        print(self.pump_A.rate)
                        self.updateTable(self.pump_A.address, 'rate', self.pump_A.rate)
                    elif x == '02':
                        self.pump_B.rate = resp[0] + ' ' + resp[1]
                        print(self.pump_B.rate)
                        self.updateTable(self.pump_B.address, 'rate', self.pump_B.rate)
                    else:
                        print("Error in askFWVer")
                        logging.info("Error in askFWVer")
                #DIAMETER
                resp = []
                resp = self.serialWrite(x,  commands['Diameter'], '')
                if DEBUG:
                    if x == '01':
                        resp = ['0xa', '0x20', '0x20', '0x31', '0x30', '0x2e', '0x30', '0x30', '0x30', '0xd', '0xa', '0x31', '0x3a']
                    else:
                        resp = ['0xa', '0x20', '0x20', '0x31', '0x30', '0x2e', '0x30', '0x30', '0x30', '0xd', '0xa', '0x32', '0x3a']
                if resp:
                    # Check status
                    resp = ''.join(self.fromLogToReadable(resp))
                    resp = resp.split() # Dodgy but it works
                    if x == '01':
                        self.pump_A.diameter = resp[0]
                        print(self.pump_A.diameter)
                        self.updateTable(self.pump_A.address, 'diameter', self.pump_A.diameter)
                    elif x == '02':
                        self.pump_B.diameter = resp[0]
                        print(self.pump_B.diameter)
                        self.updateTable(self.pump_B.address, 'diameter', self.pump_B.diameter)
                    else:
                        print("Error in askFWVer")
                        logging.info("Error in askFWVer")
                #CLEAR TARGET VOLUME
                self.serialWrite(x,  commands['ClearTarget'], '')
                #CLEAR INFUSED VOLUME
                self.serialWrite(x,  commands['ClearVol'], '')
                self.ser.reset_input_buffer()
                #VOLUME (already infused)
                resp = []
                resp = self.serialWrite(x,  commands['Volume'], '')
                if DEBUG:
                    if x == '01':
                        resp = ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x30', '0x30', '0x30', '0x30', '0xd', '0xa', '0x31', '0x3a']
                    else:
                        resp = ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x30', '0x30', '0x30', '0x30', '0xd', '0xa', '0x32', '0x3a']
                if resp:
                    # Check status
                    resp = ''.join(self.fromLogToReadable(resp))
                    resp = resp.split() # Dodgy but it works
                    if x == '01':
                        self.pump_A.dispensed = resp[0]
                        print(self.pump_A.dispensed)
                        self.updateTable(self.pump_A.address, 'dispensed', self.pump_A.dispensed)
                    elif x == '02':
                        self.pump_B.dispensed = resp[0]
                        print(self.pump_B.dispensed)
                        self.updateTable(self.pump_B.address, 'dispensed', self.pump_B.dispensed)
                    else:
                        print("Error in askFWVer")
                        logging.info("Error in askFWVer")
                #VOLUME (target)
                resp = []
                resp = self.serialWrite(x,  commands['Target'], '')
                if DEBUG:
                    if x == '01':
                        resp = ['0xa', '0x20', '0x20', '0x20', '0x20', '0x20', '0x20', '0x30', '0x2e', '0xd', '0xa', '0x31', '0x3a']
                    else:
                        resp = ['0xa', '0x20', '0x20', '0x20', '0x20', '0x20', '0x20', '0x30', '0x2e', '0xd', '0xa', '0x32', '0x3a']
                if resp:
                    # Check status
                    resp = ''.join(self.fromLogToReadable(resp))
                    resp = resp.split() # Dodgy but it works
                    if x == '01':
                        self.pump_A.volume = resp[0]
                        print(self.pump_A.volume)
                        self.updateTable(self.pump_A.address, 'volume', self.pump_A.volume)
                    elif x == '02':
                        self.pump_B.volume = resp[0]
                        print(self.pump_B.volume)
                        self.updateTable(self.pump_B.address, 'volume', self.pump_B.volume)
                    else:
                        print("Error in askFWVer")
                        logging.info("Error in askFWVer")
                #VERSION
                resp = self.serialWrite(x,  commands['Version'], '')
                if DEBUG:
                    if x == '01':
                        resp = ['0xa', '0x20', '0x20', '0x50', '0x48', '0x44', '0x31', '0x2e', '0x31', '0x32', '0x61', '0xd', '0xa', '0x31', '0x3a']
                    else:
                        resp = ['0xa', '0x20', '0x20', '0x50', '0x48', '0x44', '0x31', '0x2e', '0x31', '0x32', '0x61', '0xd', '0xa', '0x32', '0x3a']
                if resp:
                    # Check status
                    resp = ''.join(self.fromLogToReadable(resp))
                    resp = resp.split() # Dodgy but it works
                    if x == '01':
                        self.pump_A.firmware = resp[0]
                        print(self.pump_A.firmware)
                        self.updateTable(self.pump_A.address, 'firmware', self.pump_A.firmware)
                    elif x == '02':
                        self.pump_B.firmware = resp[0]
                        print(self.pump_B.firmware)
                        self.updateTable(self.pump_B.address, 'firmware', self.pump_B.firmware)
                    else:
                        print("Error in askFWVer")
                        logging.info("Error in askFWVer")
                time.sleep (200 / 1000.0);
            else:
                logging.warning("Scan pumps operation ABORTED due to user request")

        self.version_button.configure(fg='black')
        self.master.focus() #Just to remove the focus on the button
    
    def startStopPump(self, pumpId, start):
        #print (pumpId.infuse)
        if start == False:
            print("Stopping pump")
            logging.info("Stopping pump")
            self.serialWrite(pumpId.address, commands['Stop'], '')
        else:
            if pumpId.infuse == 1:
                print("Infuse")
                logging.info("Infuse")
                self.serialWrite(pumpId.address, commands['Start' if (start == True) else 'Stop'], '')
                #self.askNews(pumpId.address)
            elif pumpId.infuse == 2:
                print("Withdraw")
                logging.info("Withdraw")
                self.serialWrite(pumpId.address, commands['Withdraw' if (start == True) else 'Stop'], '')
            else:
                print("ERROR. NO DIRECTION SELECTED")
                logging.error("ERROR. NO DIRECTION SELECTED")
                
    def setDiam(self, pumpId, diam):
        diam = float(diam)
        #logging.info('Setting diameter of pump + ' pumpId.address ' to ' + diam + " mm")
        logging.info("Setting Diam to " + str(diam))
        self.serialWrite(pumpId.address, commands['SetDia'], str(diam))
        #DIAMETER
        resp = []
        resp = self.serialWrite(pumpId.address,  commands['Diameter'], '') 
        if DEBUG:
            resp = ['0xa', '0x20', '0x20', '0x31', '0x34', '0x2e', '0x34', '0x33', '0x30', '0xd', '0xa', '0x31', '0x2a'] # Marco debug
        if resp:
            # Check status
            resp = ''.join(self.fromLogToReadable(resp))
            resp = resp.split() # Dodgy but it works
            pumpId.diameter = resp[0]
            print(pumpId.diameter)
            self.updateTable(pumpId.address, 'diameter', pumpId.diameter)
           
    def setVolume(self, pumpId, vol):
        vol = float(vol)
        #logging.info('Setting diameter of pump + ' pumpId.address ' to ' + diam + " mm")
        logging.info("Setting Volume to " + str(vol) + "ml")
        self.serialWrite(pumpId.address, commands['SetVol'], str(vol))
        #self.askVolume(pumpId.address)
        #VOLUME (target)
        resp = []
        resp = self.serialWrite(pumpId.address,  commands['Target'], '')
        if DEBUG:
            resp = ['0xa', '0x20', '0x20', '0x35', '0x31', '0x2e', '0x30', '0x30', '0x30', '0xd', '0xa', '0x31', '0x2a'] # Marco debug
        if resp:
            # Check status
            resp = ''.join(self.fromLogToReadable(resp))
            resp = resp.split() # Dodgy but it works
            pumpId.volume = resp[0]
            print(pumpId.volume)
            self.updateTable(pumpId.address, 'volume', pumpId.volume)
        
    def setDirection(self, pumpId, direction):
        direction = int(direction)
        #logging.info('Setting diameter of pump + ' pumpId.address ' to ' + diam + " mm")
        if direction == 1:
            # Infuse
            print("Set INFUSE")
            logging.info("Set INFUSE")
            pumpId.infuse = 1
        elif direction == 2:
            # Withdraw
            print("Set WITHDRAW")
            logging.info("Set WITHDRAW")
            pumpId.infuse = 2
        else:
            print("DEVELOPMENT ERROR!!!")
            logging.info("Set direction DEVELOPMENT ERROR!!!")
            raise
        #self.askRate(pumpId.address)
        
    def setRate(self, pumpId, rate, units):
        print("Setting rate")
        logging.info("Setting rate")
        if units == 'MM':
            cmd = commands['RateMLM']
        elif units == 'MH':
            cmd = commands['RateMLH']
        elif units == 'UM':
            cmd = commands['RateULM']
        elif units == 'UH':
            cmd = commands['RateULH']
        else:
            print("ERROR: Units not known")
            return
            
        #cmd += ' ' #Marco deleted v0.0.2 (was working in 0.0.1)
        rateRsp = []
        rateRsp = self.serialWrite(pumpId.address, cmd, str(rate))
        #Marco removed on field
        #time.sleep(100/1000.0)
        if DEBUG:
            rateRsp = ['0xa', '0x20', '0x20', '0x4f', '0x4f', '0x52', '0xd', '0xa', '0x31', '0x3a'] # Marco debug
        
        if rateRsp:
            # Check status
            resp = ''.join(self.fromLogToReadable(rateRsp))
            if 'OOR' in resp:
                # Rate not ok
                pumpId.rate = "Out of Range"
                print("Out of range")
        
        rateOut = []
        # Ask for the rate
        rateOut = self.serialWrite(pumpId.address, commands['Rate'], '')
        if DEBUG:
            rateOut = ['0xa', '0x31', '0x3a', '0xa', '0x20', '0x20', '0x31', '0x30', '0x30', '0x2e', '0x30', '0x30', '0x20', '0x75', '0x6c', '0x2f', '0x68', '0x72', '0xd', '0xa', '0x31', '0x3a']  # Marco to remove line

        if rateOut:
            # Update the table of information
            resp = ''.join(self.fromLogToReadable(rateOut))
            resp = resp.split() # Dodgy but it works
            pumpId.rate = resp[0] + ' ' + resp[1]
            print(pumpId.rate)
            self.updateTable(pumpId.address, 'rate', pumpId.rate)
    def clearTarget(self, pump):
        #CLEAR TARGET VOLUME
        self.serialWrite(pump.address,  commands['ClearTarget'], '')
        self.ser.reset_input_buffer()
        
    def updateTable(self, pumpId, col, val):
        """ Used to update what is displayed on the screen about pumps
        """
        #logging.info ('TABLE UPDATE pump '+ str(pumpId) + ': ' + str(col) + ' ' + str(val))
        self.table.set(pumpId, column=col, value=val)
    
    def serialWrite(self, pumpID, cmd, options):
        ''' Writes a command on a serial. Returns the response formatted as a 
            list of strings, each string is the hex representation of a char
        '''
        if pumpID == '01':
            my_pump = self.pump_A
        elif pumpID == '02':
            my_pump = self.pump_B
        else:
            print("DEVELOPMENT ERROR IN PUMP NAMES")
            logging.error("DEVELOPMENT ERROR IN PUMP NAMES")
        # Write on the COM port and get the reply. If the port is not opened,
        # return a message
        toWrite = str(pumpID).zfill(2) + str(cmd) + str(options) + '\r'
        print("Sending " + str(toWrite).rstrip() + " command")
        logging.info("Sending " + str(toWrite).rstrip() + " command")
        try:
            self.ser.write(toWrite.encode())
        except:
            print("Serial write operation failed during command " + str(toWrite).rstrip())
            logging.error("Serial write operation failed during command " + str(toWrite).rstrip())
        else:
            #ToDo: Marco check it works with black pumps (field)
            time.sleep(70/1000.0)
            out = []
            if self.ser.in_waiting > 0:
                #print(self.ser.in_waiting)
                tmp = (self.ser.read(self.ser.in_waiting))
                for ch in tmp:
                    out.append(hex(ch))
                print(out)
                logging.info(out)
            if DEBUG:
                if pumpID == '01':
                    out = ['0xa', '0x31', '0x3a'] # Marco to be removed
                elif pumpID == '02':
                    out = ['0xa', '0x32', '0x3a'] # Marco to be removed
                #return out
            if out:
                #Something came back!!
                if out[0] != '0xa': # Marco change back to !=
                    print("UNEXPECTED RSP!")
                    logging.error("UNEXPECTED RSP!")
                else:
                    rsp_addr = chr(int(out[-2],16))
                    rsp_addr = rsp_addr.zfill(2)
                    if rsp_addr == my_pump.address:
                        # Check status
                        if out[-1] == '0x3e': # >
                            my_pump.status = "Infusing"
                        elif out[-1] == '0x3c': # <
                            my_pump.status = "Withdrawing"
                        elif out[-1] == '0x3a': # :
                            my_pump.status = "Stopped"
                        elif out[-1] == '0x2a': # *
                            my_pump.status = "Stalled"
                        else:
                            print("Unexpected character received")
                            logging.error("Unexpected character received")
                            my_pump.status = "COMM error"
                            return 
                        
                        self.updateTable(my_pump.address, 'status', my_pump.getStatus())
                    else:
                        print("Received PUMP ID is not valid")
                        
            return out
    
    
    def emergencyStop(self):
        """ Call it to stop the push/pull
        """
        self.emergency = True
    
    def pushPull_thread (self, pump1, pump2, volume, delay, cycles):
        '''
        I expect the user to be able to override the volume before calling the 
        function. Delay is the time between a full push ends and a new pull 
        starts
        '''
        def callback():
            if self.closing == False:
                my_volume = float(volume)
                my_delay = int(delay)
                my_cycles = int(cycles)
                self.emergency = False
                INFUSE = 1
                WITHDRAW = 2
                # Check the selected volume
                if float(my_volume) == 0:
                    print("NULL volume! Program not started")
                    logging.error("NULL volume! Program not started")
                    return
                elif pump1.getRate() != pump2.getRate():
                    print("Pumps must have the same flow-rate! Program not started")
                    logging.error("Pumps must have the same flow-rate! Program not started")
                    return
                elif pump1.getUnits() != pump2.getUnits():
                    print("Flow-rate units must be the same! Program not started")
                    logging.error("Flow-rate units must be the same! Program not started")
                    return
                    
                # Set the same flow-rate (just in case)
                #self.setRate(pump1, pump1.getRate, pump1.getUnits)
                #self.setRate(pump2, pump2.getRate, pump2.getUnits)
                # Set direction
                pump1_direction = INFUSE
                pump2_direction = WITHDRAW
                # Push/pull
                for i in range (0, my_cycles):
                    if self.closing == False and self.emergency == False:
                        print("Cycle " + str(i) + ": P1 " + str(pump1.getStatus()) + ". P2 " + str(pump2.getStatus()))
                        logging.info("Cycle " + str(i) + ": P1 " + str(pump1.getStatus()) + ". P2 " + str(pump2.getStatus()))
                        self.__currIter.set(i+1)
                        root.update()
                        # Set the same volume for all the pumps
                        self.setVolume(pump1, my_volume)
                        self.setVolume(pump2, my_volume)
                        # Set direction
                        self.setDirection(pump1, pump1_direction)
                        self.setDirection(pump2, pump2_direction)
                        
                        self.startStopPump(pump1, True)
                        self.startStopPump(pump2, True)
                        
                        self.waituntiltarget(pump1, pump2)
                        
                        # Swap the directions
                        if pump1_direction == INFUSE:
                            pump1_direction = WITHDRAW
                            pump2_direction = INFUSE
                        else:
                            pump1_direction = INFUSE
                            pump2_direction = WITHDRAW
                        
                        
                        pump1.direction = pump1_direction
                        pump2.direction = pump2_direction
                        
                        #self.clearTarget(pump1)
                        #self.clearTarget(pump2)
                        
                        #self.startStopPump(pump1, False)
                        #self.startStopPump(pump2, False)
                        
                        time.sleep(my_delay)
                    else:
                        print("PUSH/PULL operation aborted")
                        break
        
        self.pushPull = threading.Thread(target=callback)
        self.pushPull.start()
    
    def waituntiltarget(self, pump1, pump2):
        """Wait until the pump has reached its target volume."""
        print('Waiting until target reached')
        logging.info('Waiting until target reached')
        
        reached = False
        
        if DEBUG:
            i = 0
            a = [['0xa', '0x20', '0x20', '0x30', '0x2e', '0x30', '0x31', '0x34', '0x31', '0xd', '0xa', '0x31', '0x3e']                                                          ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x30', '0x32', '0x36', '0x33', '0xd', '0xa', '0x31', '0x3e']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x30', '0x33', '0x38', '0x34', '0xd', '0xa', '0x31', '0x3e']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x30', '0x35', '0x30', '0x33', '0xd', '0xa', '0x31', '0x3e']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x30', '0x36', '0x32', '0x33', '0xd', '0xa', '0x31', '0x3e']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x30', '0x37', '0x34', '0x33', '0xd', '0xa', '0x31', '0x3e']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x30', '0x38', '0x36', '0x32', '0xd', '0xa', '0x31', '0x3e']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x30', '0x39', '0x38', '0x34', '0xd', '0xa', '0x31', '0x3e']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x31', '0x31', '0x30', '0x33', '0xd', '0xa', '0x31', '0x3e']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x31', '0x32', '0x32', '0x33', '0xd', '0xa', '0x31', '0x3e']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x31', '0x33', '0x34', '0x33', '0xd', '0xa', '0x31', '0x3e']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x31', '0x34', '0x36', '0x33', '0xd', '0xa', '0x31', '0x3e']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x31', '0x35', '0x38', '0x33', '0xd', '0xa', '0x31', '0x3e']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x31', '0x37', '0x30', '0x34', '0xd', '0xa', '0x31', '0x3e']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x31', '0x38', '0x32', '0x34', '0xd', '0xa', '0x31', '0x3e']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x31', '0x39', '0x34', '0x33', '0xd', '0xa', '0x31', '0x3e']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x32', '0x30', '0x36', '0x35', '0xd', '0xa', '0x31', '0x3e']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x32', '0x31', '0x38', '0x34', '0xd', '0xa', '0x31', '0x3e']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x32', '0x33', '0x30', '0x34', '0xd', '0xa', '0x31', '0x3e']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x32', '0x34', '0x32', '0x35', '0xd', '0xa', '0x31', '0x3e']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x32', '0x35', '0x34', '0x36', '0xd', '0xa', '0x31', '0x3e']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x32', '0x36', '0x36', '0x37', '0xd', '0xa', '0x31', '0x3e']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x32', '0x37', '0x38', '0x37', '0xd', '0xa', '0x31', '0x3e']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x32', '0x39', '0x30', '0x37', '0xd', '0xa', '0x31', '0x3e']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x33', '0x30', '0x32', '0x38', '0xd', '0xa', '0x31', '0x3e']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x33', '0x31', '0x34', '0x38', '0xd', '0xa', '0x31', '0x3e']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x33', '0x32', '0x36', '0x38', '0xd', '0xa', '0x31', '0x3e']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x33', '0x33', '0x38', '0x39', '0xd', '0xa', '0x31', '0x3e']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x33', '0x35', '0x31', '0x30', '0xd', '0xa', '0x31', '0x3e']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x33', '0x36', '0x33', '0x31', '0xd', '0xa', '0x31', '0x3e']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x33', '0x37', '0x35', '0x31', '0xd', '0xa', '0x31', '0x3e']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x33', '0x38', '0x37', '0x32', '0xd', '0xa', '0x31', '0x3e']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x33', '0x39', '0x39', '0x33', '0xd', '0xa', '0x31', '0x3e']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x34', '0x31', '0x31', '0x33', '0xd', '0xa', '0x31', '0x3e']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x34', '0x32', '0x33', '0x34', '0xd', '0xa', '0x31', '0x3e']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x34', '0x33', '0x35', '0x34', '0xd', '0xa', '0x31', '0x3e']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x34', '0x34', '0x37', '0x34', '0xd', '0xa', '0x31', '0x3e']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x34', '0x35', '0x39', '0x35', '0xd', '0xa', '0x31', '0x3e']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x34', '0x37', '0x31', '0x35', '0xd', '0xa', '0x31', '0x3e']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x34', '0x38', '0x33', '0x35', '0xd', '0xa', '0x31', '0x3e']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x34', '0x39', '0x35', '0x36', '0xd', '0xa', '0x31', '0x3e']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x34', '0x39', '0x35', '0x36', '0xd', '0xa', '0x31', '0x3e']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x35', '0x30', '0x30', '0x30', '0xd', '0xa', '0x31', '0x3a']]
            b = [['0xa', '0x20', '0x20', '0x30', '0x2e', '0x30', '0x30', '0x31', '0x39', '0xd', '0xa', '0x32', '0x3c']                                                          ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x30', '0x31', '0x34', '0x30', '0xd', '0xa', '0x32', '0x3c']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x30', '0x32', '0x36', '0x31', '0xd', '0xa', '0x32', '0x3c']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x30', '0x33', '0x38', '0x32', '0xd', '0xa', '0x32', '0x3c']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x30', '0x35', '0x30', '0x31', '0xd', '0xa', '0x32', '0x3c']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x30', '0x36', '0x32', '0x32', '0xd', '0xa', '0x32', '0x3c']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x30', '0x37', '0x34', '0x32', '0xd', '0xa', '0x32', '0x3c']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x30', '0x38', '0x36', '0x31', '0xd', '0xa', '0x32', '0x3c']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x30', '0x39', '0x38', '0x32', '0xd', '0xa', '0x32', '0x3c']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x31', '0x31', '0x30', '0x32', '0xd', '0xa', '0x32', '0x3c']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x31', '0x32', '0x32', '0x32', '0xd', '0xa', '0x32', '0x3c']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x31', '0x33', '0x34', '0x32', '0xd', '0xa', '0x32', '0x3c']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x31', '0x34', '0x36', '0x32', '0xd', '0xa', '0x32', '0x3c']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x31', '0x35', '0x38', '0x31', '0xd', '0xa', '0x32', '0x3c']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x31', '0x37', '0x30', '0x33', '0xd', '0xa', '0x32', '0x3c']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x31', '0x38', '0x32', '0x32', '0xd', '0xa', '0x32', '0x3c']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x31', '0x39', '0x34', '0x32', '0xd', '0xa', '0x32', '0x3c']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x32', '0x30', '0x36', '0x33', '0xd', '0xa', '0x32', '0x3c']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x32', '0x31', '0x38', '0x33', '0xd', '0xa', '0x32', '0x3c']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x32', '0x33', '0x30', '0x33', '0xd', '0xa', '0x32', '0x3c']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x32', '0x34', '0x32', '0x33', '0xd', '0xa', '0x32', '0x3c']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x32', '0x35', '0x34', '0x35', '0xd', '0xa', '0x32', '0x3c']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x32', '0x36', '0x36', '0x35', '0xd', '0xa', '0x32', '0x3c']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x32', '0x37', '0x38', '0x36', '0xd', '0xa', '0x32', '0x3c']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x32', '0x39', '0x30', '0x36', '0xd', '0xa', '0x32', '0x3c']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x33', '0x30', '0x32', '0x37', '0xd', '0xa', '0x32', '0x3c']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x33', '0x31', '0x34', '0x36', '0xd', '0xa', '0x32', '0x3c']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x33', '0x32', '0x36', '0x36', '0xd', '0xa', '0x32', '0x3c']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x33', '0x33', '0x38', '0x38', '0xd', '0xa', '0x32', '0x3c']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x33', '0x35', '0x30', '0x38', '0xd', '0xa', '0x32', '0x3c']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x33', '0x36', '0x33', '0x30', '0xd', '0xa', '0x32', '0x3c']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x33', '0x37', '0x35', '0x30', '0xd', '0xa', '0x32', '0x3c']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x33', '0x38', '0x37', '0x30', '0xd', '0xa', '0x32', '0x3c']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x33', '0x39', '0x39', '0x31', '0xd', '0xa', '0x32', '0x3c']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x34', '0x31', '0x31', '0x31', '0xd', '0xa', '0x32', '0x3c']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x34', '0x32', '0x33', '0x32', '0xd', '0xa', '0x32', '0x3c']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x34', '0x33', '0x35', '0x32', '0xd', '0xa', '0x32', '0x3c']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x34', '0x34', '0x37', '0x33', '0xd', '0xa', '0x32', '0x3c']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x34', '0x35', '0x39', '0x34', '0xd', '0xa', '0x32', '0x3c']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x34', '0x37', '0x31', '0x34', '0xd', '0xa', '0x32', '0x3c']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x34', '0x38', '0x33', '0x33', '0xd', '0xa', '0x32', '0x3c']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x34', '0x39', '0x35', '0x35', '0xd', '0xa', '0x32', '0x3c']                                                       ,
                    ['0xa', '0x20', '0x20', '0x30', '0x2e', '0x35', '0x30', '0x30', '0x30', '0xd', '0xa', '0x32', '0x3a'] ]
    
        while (reached != True) and (self.closing == False) and (self.emergency != True):
            resp1 = []
            resp1 = self.serialWrite(pump1.address,  commands['Volume'], '')  
            if DEBUG:
                resp1 = a[i]
            if resp1:
                # Check status
                resp1 = ''.join(self.fromLogToReadable(resp1))
                _resp1 = resp1.split() # Dodgy but it works
                if (len(_resp1[0]) < 3) or not('1' in _resp1[-1]):
                    print("Unexpected string received pump 1")
                    logging.error("Unexpected string received pump 1")
                    print("Received " + resp1)
                    #Do not update the GUI
                else:
                    pump1.dispensed = _resp1[0]
                    self.updateTable(pump1.address, 'dispensed', pump1.dispensed)
                
            resp2 = []
            resp2 = self.serialWrite(pump2.address,  commands['Volume'], '') 
            if DEBUG:
                resp2 = b[i]
            if resp2:
                # Check status
                resp2 = ''.join(self.fromLogToReadable(resp2))
                _resp2 = resp2.split() # Dodgy but it works
                if (len(_resp2[0]) < 3) or not('2' in _resp2[-1]):
                    print("Unexpected string received pump 2")
                    logging.error("Unexpected string received pump 2")
                    print("Received " + resp2)
                    #Do not update the GUI
                else:
                    pump2.dispensed = _resp2[0]
                    self.updateTable(pump2.address, 'dispensed', pump2.dispensed)
                
            if resp1 and resp2:
                if ':' in resp1 and ':' in resp2:
                    # pump has already come to a halt
                    print("Pumps stopped correctly")
                    logging.info("Pumps stopped correctly")
                    reached = True
                
                # MARCO - not good because if they meet at half ramp, they stop
                # Check if they're the same - if they are, break, otherwise continue
                #elif pump1.dispensed == pump2.dispensed:
                #    print('Target volume reached, stopped')
                #    logging.info('Target volume reached, stopped')
                #   reached = True
                else:
                    #Still running
                    my_timer = 50/1000.0
                    time.sleep(my_timer)
            else:
                if DEBUG:
                    print("No reply from the pumps")
                    logging.error("No reply from the pumps")
                else:
                    pass
                
            if DEBUG:
                i += 1
        print("Wait for target function ended with >> reached = " + str(reached) + " >> self.emergency = " + str(self.emergency) + " >> self.closing = " + str(self.closing))
        logging.info("Wait for target function ended")

    
    def fromLogToReadable(self, lista):
        my_lista = lista[:]
        # Convert the list of strings to int
        my_lista = [int(i,16) for i in my_lista]
        my_lista = [chr(i) for i in my_lista]
        return my_lista                

    def openPort(self):
        """ User level.
            Open a COM port as 8N2 frame. COM port and baudrate are provided by the user
        """
        self.ser.parity=serial.PARITY_NONE
        self.ser.stopbits=serial.STOPBITS_TWO
        self.ser.bytesize=serial.EIGHTBITS
        self.ser.port = self.COMnumberChosen.get()
        self.ser.baudrate = self.baudrateChosen.get()
        print("Opening " + str(self.ser.port) + " port at baudrate: " + str(self.ser.baudrate))
        # Just to be sure close it, in case something has changed
        if self.ser.isOpen():
            print("COM port already open. Closing the COM port . . .")
            try:
                self.ser.close()
            except:
                pass
        # Now open the port
        try:
            self.ser.open()
            print("COM port now open")
        except:
            print("Unable to open the COM port")
        
        try:
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
        except:
            pass
    
    def choseCOM(self):
        """ Low level.
            Show a list of COM ports
        """
        self.COMnumberChosen = ttk.Combobox(self.connectionFrame, textvariable = self.COMnumber.get(), state = 'readonly') #3
        self.COMnumberChosen['values'] = self.serial_ports() # 4#
        if len(self.COMnumberChosen["values"]) == 0:
            self.COMnumberChosen['values'] = 'ERROR'
        self.COMnumberChosen.current(0) # 6
        self.COMnumberChosen.pack(side = LEFT)
        
    def choseBaudrate(self):
        """ Low level.
            Show a list of possible baudrates
        """
        self.baudrateChosen = ttk.Combobox(self.connectionFrame, textvariable=self.baudrate.get(), state='readonly') #3
        self.baudrateChosen['values'] = (19200, 9600, 2400, 1200, 300) # 4
        self.baudrateChosen.current(1) # 6
        self.baudrateChosen.pack(side = LEFT)
       
    def serial_ports(self):
        """ Low level.
            Show the COM ports that are detected by the OS
        """
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # this excludes your current terminal "/dev/tty"
            ports = glob.glob('/dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')
        else:
            raise EnvironmentError('Unsupported platform')
    
        result = []
        for port in ports:
            try:
                s = serial.Serial(port)
                s.close()
                result.append(port)
            except (OSError, serial.SerialException):
                pass
        return result
    
    def my_quit(self):
        """ User level.
            Close the COM port and shut down the interface correctly
        """
        try:
            a = self.pushPull.isAlive()
            if a == True:
                print("Closing pushPull thread whilst still alive")
                logging.warn("Closing pushPull thread whilst still alive")
        except:
            pass
        self.closing = True
        try:
            print("Closing COM port . . .")
            logging.warn("Closing COM port . . .")
            self.ser.close()
        except:
            pass
        quit()


root = tk.Tk()
root.title("ruinsPy")
#root.geometry("200x150")
#root.resizable(0, 0)
app = PumPy_GUI(root)

root.mainloop()