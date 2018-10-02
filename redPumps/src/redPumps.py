import tkinter as tk
import sys
import threading
import time
import serial
import glob
import logging
import queue
import ast
from tkinter import ttk, StringVar, IntVar, PhotoImage
from tkinter.constants import LEFT, TOP, BOTTOM,W, GROOVE
import os.path 
from pathlib import Path

FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
SW_INFO = "redPumps v.1.0.0"

#Create every time a file (loosing the old)
#logging.basicConfig(filename = 'redPumps.log', level=logging.DEBUG, filemode='w', format=FORMAT)
#Append to the same file
logging.basicConfig(filename = 'redPumps.log', level=logging.DEBUG, filemode='a', format=FORMAT)
DEBUG = False
class pump(object):
    """ A syringe pump
    """ 
#     def __init__(self, address, status, diameter, rate, units, dispensed, warnings):
    def __init__(self, address):
        """Return a Customer object whose name is *name*.""" 
        self.address = str(address).zfill(2) #Id
        self.status = 'NOT DETECTED'            #stopped, running, etc
        self.diameter = '0'           #internal diameter
        self.rate = '0'               #pumping rate
        self.units = 'UNKNOWN'             #pumping units
        self.dispensed = '0'          #dispensed volume
        self.warnings = 'N/A'          #warnings
        self.firmware = 'N/A'          #warnings
        self.detected = False          #JUST IN CASE WE NEED IT LATER
    def setAddress(self, address):
        self.address = str(address).zfill(2)
    def setDiameter(self, diameter):
        #Maximum of 4 digits plus 1 decimal point
        self.diameter = str(diameter).zfill(5)
        
    def getStatus(self):
        return self.status
    def getDiameter(self):
        return self.diameter
    def getUnits(self):
        return self.units
    def getRate(self):
        return self.rate
    def getDispensed(self):
        return self.dispensed
    def getWarnings(self):
        return self.warnings
    def getFirmware(self):
        return self.firmware

class RepeatedTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer     = None
        self.interval   = interval #Seconds
        self.function   = function
        self.args       = args
        self.kwargs     = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = threading.Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False

class popupWindow(object):
    #Just to setup the address. Use it for the grey pumps
    def __init__(self,master):
        top = self.top = tk.Toplevel(master)
        self.isOk = False
        
        self.l = tk.Label(top,text="Make sure you have:\n- set the correct BAUDRATE\n\
        - opened the correct COM port\n- connected ONLY ONE PUMP\n\n\n\
        (If you use the pumps without display, \nthe baudrate has to be 19200)\n\n\
        Please, insert an address from 00 to 99\n\n")
        self.l.pack()
        
        self.e = tk.Entry(top)
        self.e.pack()
        self.e.focus()
        
        self.b = tk.Button(top,text='Ok',command=self.cleanup)
        self.b.pack()
        
        self.c = tk.Button(top,text='Go Back',command=self.goBack)
        self.c.pack()
        
    def cleanup(self):
        self.value = self.e.get()
        try:
            a = int(self.value)            
            #Is it a valid value?
            if a in range(0,100):
                self.value = str(a)
                self.isOk = True
            else:
                print("Not valid: " + str(self.value))
                logging.warning("Not valid: " + str(self.value))
        except:
            print("The user input failed. Inserted: " + str(self.value))
            logging.warning("The user input failed. Inserted: " + str(self.value))

        self.top.destroy()
        
    def goBack(self):
        self.top.destroy()

class redPumps_GUI(tk.Frame):    
    #Serial 
    commands = {
                'Diameter':'DIA', 
                'Rate':'RAT', 
                'millilitersPerMin':'MM', 
                'Volume':'VOL', 
                'InfusionDir':'DIRINF',
                'WithdrawDir': 'DIRWDR', 
                'Start': 'RUN',
                'Stop': 'STP',
                'Version': 'VER',
                'Address': '* ADR',
                'Baudrate': 'B',
                'BeepOnOff': 'BUZ12'
    }
    prompts = {
                'Infusing'       :'I',
                'Withdrawing'    :'W',
                'Stopped'        :'S',
                'Paused'          :'P',
                'Phase Paused'   :'T',
                'Trigger Wait'  :'U' ,
                'Alarm'  :'A' 
        }
    alarms = {
                'Pump reset'         :'R',
                'STALL'              :'S',
                'Safe Comm time out' :'T',
                'Pumping prg ERROR'  :'E',
                'Phase Out Of Range' :'O'
        }
    def __init__(self, master):
        tk.Frame.__init__(self,master)
        self.pack()
        #Frames
        self.createFrames()
        self.baudrate = tk.StringVar()
        self.COMnumber = tk.StringVar()
        self.closing = False
        # Pumps
        self.pump_A = pump('1')
        self.pump_B = pump('2')
        self.pump_C = pump('3')
        #
        self.createWidgets()
        # SERIAL 
        self.ser = serial.Serial()
        self.q = queue.Queue()
        logging.exception("____________________________________ PumpPy ____________________________________")
        
    def createFrames(self):
        #Menu
        self.menubar = tk.Menu(root)
        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="Exit", command = self.my_quit)
        self.setAddMenu = tk.Menu(self.menubar, tearoff=0)
        self.setAddMenu.add_command(label = "Set Address", command = self.popup)
        self.setHelpMenu = tk.Menu(self.menubar, tearoff=0)
        self.setHelpMenu.add_command(label = "About redPumps", command = self.getSWInfo)
        
        self.menubar.add_cascade(label="File", menu=self.filemenu)
        self.menubar.add_cascade(label="Preferences", menu=self.setAddMenu)
        self.menubar.add_cascade(label="Help", menu=self.setHelpMenu)
        
        #self.menubar.add_command(label="Quit", command=self.my_quit())
        #self.menubar.add_command(label="Setup")
        root.config(menu=self.menubar)
        #Connection
        self.connectionFrame = tk.Frame()
        self.connectionFrame.pack(expand = False, side = TOP)
        #Scan pumps
        self.scanFrame = tk.Frame()
        self.scanFrame.pack(expand = False, side = TOP)
        #Visualisation
        self.displayFrame = tk.Frame()
        self.displayFrame.pack(expand = False, side = TOP)
        
        #Frame containing commands for pumps and ramps
        self.my_commands = tk.Frame()
        self.my_commands.pack(expand = False, side = TOP, pady = 8)
        #Commands
        self.commandFrame = tk.LabelFrame(self.my_commands, text = "Pump Manager")
        self.commandFrame.grid(row = 0, column = 0)
        
        #Frame for RAMPS and TERNARY
        self.ramps_and_ternary = tk.Frame()
        self.ramps_and_ternary.pack(expand = False, side = TOP, pady = 10)
        #Two sub-frames:
        self.rampFrame = tk.LabelFrame(self.ramps_and_ternary, text = "Ramp Manager")
        self.rampFrame.grid(row = 0, column = 0, ipady=2)
        self.ternaryFrame = tk.LabelFrame(self.ramps_and_ternary, text = "TPD - Ternary Phase Diagram")
        self.ternaryFrame.grid(row = 0, column = 1, padx = 8)
        #Frame containing commands for ternary systems
        #Subframe image
        self.t_imgFrame = tk.Frame(self.ternaryFrame)
        self.t_imgFrame.pack(expand = False, side = LEFT)
        #Subframe settings
        self.t_settings = tk.Frame(self.ternaryFrame)
        self.t_settings.pack(expand = False, side = LEFT)
        #Sub-subframe pump C
        self.t_pumpCFrame = tk.LabelFrame(self.t_settings, text = "Pump C")
        self.t_pumpCFrame.pack(expand = False, side = TOP)
        #Sub-subframe pump A and B
        self.t_pumpsABFrame = tk.LabelFrame(self.t_settings, text = "Pumps A&B")
        self.t_pumpsABFrame.pack(expand = False, side = TOP)
        #Subframe commands
        self.t_commandsFrame = tk.Frame(self.ternaryFrame)
        self.t_commandsFrame.pack(expand = False, side = LEFT)
        
        #Exit program
        self.exitFrame = tk.Frame()
        self.exitFrame.pack(expand = True, side = BOTTOM)
        
    def createWidgets(self):
        #CONNECTION
        self.labelSelectCOM = tk.Label(self.connectionFrame, text="Select a COM port:")
        self.labelSelectCOM.pack( side = LEFT)
        
        self.choseCOM()
        self.choseBaudrate()
        
        #DO NOT put brackets in the callback name or it will call the function
        self.openCOM = tk.Button(self.connectionFrame, text="open", relief=GROOVE, command=self.openPort)
        self.openCOM.configure(fg = "red")
        self.openCOM.pack(side = LEFT)
        self.openCOM.focus()
        
        self.version_button = tk.Button(self.scanFrame, text="Scan Pumps", command=self.askFWVer, width = 15, height=3, relief=GROOVE, fg='blue')
        self.version_button.pack()
        
        #=======================================================================
        
        #DISPLAY STATUS
        self.table = ttk.Treeview(self.displayFrame, columns=('status', 'diameter', 'units', 'rate', 'dispensed', 'warnings', 'firmware'), height = 3)
        self.table.column('#0', stretch = False, width = 70)
        self.table.heading('status', text='Status', anchor = W)
        self.table.column('status', stretch = False, width = 100)
        self.table.heading('diameter', text = 'Diameter', anchor = W)
        self.table.column('diameter', stretch = False, width = 57)
        self.table.heading('units', text = 'Units', anchor = W)
        self.table.column('units', stretch = False, width = 70)
        self.table.heading('rate', text = 'Rate', anchor = W)
        self.table.column('rate', stretch = False, width = 50)
        self.table.heading('dispensed', text = 'Volume', anchor = W)
        self.table.column('dispensed', stretch = False, width = 70)
        self.table.heading('warnings', text = 'Warnings', anchor = W)
        self.table.column('warnings', stretch = False, width = 100)
        self.table.heading('firmware', text = 'Firmware', anchor = W)
        self.table.column('firmware', stretch = False, width = 90)
          
          
        self.table.insert("" , 0, iid='03', text="PUMP 3", values=(self.pump_C.getStatus(),self.pump_C.getDiameter(),self.pump_C.getUnits(),self.pump_C.getRate(),self.pump_C.getDispensed(),self.pump_C.getWarnings(),self.pump_C.getFirmware()))
        self.table.insert("" , 0, iid='02', text="PUMP 2", values=(self.pump_B.getStatus(),self.pump_B.getDiameter(),self.pump_B.getUnits(),self.pump_B.getRate(),self.pump_B.getDispensed(),self.pump_B.getWarnings(),self.pump_B.getFirmware()))
        self.table.insert("" , 0, iid='01', text="PUMP 1", values=(self.pump_A.getStatus(),self.pump_A.getDiameter(),self.pump_A.getUnits(),self.pump_A.getRate(),self.pump_A.getDispensed(),self.pump_A.getWarnings(),self.pump_A.getFirmware())) 
        self.table.pack(side = LEFT)
        
        #=======================================================================
        #########################  PUMP MANAGER  ###############################
        #=======================================================================
        #Start/stop pumps and diameter
        self.diameterLabel = tk.Label(self.commandFrame, text = "Diameter")
        self.diameterLabel.grid(row=0, column=1)
        self.diameterLabel = tk.Label(self.commandFrame, text = " ")
        self.diameterLabel.grid(row=0, column=3)
        self.diameterLabel = tk.Label(self.commandFrame, text = "Rate")
        self.diameterLabel.grid(row=0, column=4)
        self.diameterLabel = tk.Label(self.commandFrame, text = " ")
        self.diameterLabel.grid(row=0, column=7)
        self.startStopLabel = tk.Label(self.commandFrame, text = "Command")
        self.startStopLabel.grid(row=0, column=8)
        self.startStopLabel = tk.Label(self.commandFrame, text = "Volume")
        self.startStopLabel.grid(row=0, column=11)
        
        #PUMP 1
        line = 1
        dia_01 = StringVar() 
        dia_01.set("0.000")
        vol_01 = StringVar() 
        vol_01.set("1.000")
        rat_01 = StringVar() 
        rat_01.set("0.000")
        dir_01 = IntVar()
        dir_01.set(0)
        units_01 = StringVar()
        self.pump_02_Label = tk.Label(self.commandFrame, text = "PUMP 1")
        self.pump_02_Label.grid(row=line, column=0)
        #Diameter
        self.dia_01_Label = tk.Entry(self.commandFrame, text = dia_01.get(), textvariable=dia_01, width = 10)
        self.dia_01_Label.grid(row=line, column=1)
        self.dia_01_setLabel = tk.Button(self.commandFrame, text="Set", command=lambda: self.setDiam(self.pump_A, dia_01.get()))
        self.dia_01_setLabel.grid(row=line, column=2)
        #Rate        
        self.rat_01_Label = tk.Entry(self.commandFrame, text = rat_01.get(), textvariable=rat_01, width = 10)
        self.rat_01_Label.grid(row=line, column=4)
        self.uni_01 = ttk.Combobox(self.commandFrame, textvariable=units_01, width = 4)
        self.uni_01['values']=('MM','MH','UM','UH')
        self.uni_01.current(0) # 6
        self.uni_01.grid(row=line, column=5)
        self.rat_01_setLabel = tk.Button(self.commandFrame, text="Set", command=lambda: self.setRate(self.pump_A, rat_01.get(), units_01.get()))
        self.rat_01_setLabel.grid(row=line, column=6)
        #Start/stop
        self.start_01_Label = tk.Button(self.commandFrame, text="Start", relief=GROOVE, command=lambda: self.startStopPump(self.pump_A, True))
        self.start_01_Label.grid(row=line, column=8)
        self.stop_01_Label = tk.Button(self.commandFrame, text="Stop", relief=GROOVE, command=lambda: self.startStopPump(self.pump_A, False))
        self.stop_01_Label.grid(row=line, column=9)
        self.filler_01 = tk.Label(self.commandFrame, text = " ")
        self.filler_01.grid(row=line, column=10)
        #Volume
        self.vol_01_Label = tk.Entry(self.commandFrame, text = vol_01.get(), textvariable=vol_01, width = 10)
        self.vol_01_Label.grid(row=line, column=11)
        self.vol_01_setLabel = tk.Button(self.commandFrame, text="Set", command=lambda: self.setVolume(self.pump_A, vol_01.get()))
        self.vol_01_setLabel.grid(row=line, column=12)
        #Direction
        self.dir_01 = tk.Radiobutton(self.commandFrame, text="INF", variable=dir_01, value=1, command=lambda: self.setDirection(self.pump_A, dir_01.get()))
        self.dir_01.grid(row=line, column=14)
        self.dir_01 = tk.Radiobutton(self.commandFrame, text="WIT", variable=dir_01, value=2, command=lambda: self.setDirection(self.pump_A, dir_01.get()))
        self.dir_01.grid(row=line, column=15)
        
        #PUMP2
        line = 2
        dia_02 = StringVar() 
        dia_02.set("0.000")
        vol_02 = StringVar() 
        vol_02.set("1.000")
        rat_02 = StringVar() 
        rat_02.set("0.000")
        dir_02 = IntVar()
        dir_02.set(0)
        units_02 = StringVar()
        self.pump_02_Label = tk.Label(self.commandFrame, text = "PUMP 2")
        self.pump_02_Label.grid(row=line, column=0)
        #Diameter
        self.dia_02_Label = tk.Entry(self.commandFrame, text = dia_02.get(), textvariable=dia_02, width = 10)
        self.dia_02_Label.grid(row=line, column=1)
        self.dia_02_setLabel = tk.Button(self.commandFrame, text="Set", command=lambda: self.setDiam(self.pump_B, dia_02.get()))
        self.dia_02_setLabel.grid(row=line, column=2)
        #Rate
        self.rat_02_Label = tk.Entry(self.commandFrame, text = rat_02.get(), textvariable=rat_02, width = 10)
        self.rat_02_Label.grid(row=line, column=4)
        self.uni_2 = ttk.Combobox(self.commandFrame, textvariable=units_02, width = 4)
        self.uni_2['values']=('MM','MH','UM','UH')
        self.uni_2.current(0) # 6
        self.uni_2.grid(row=line, column=5)
        self.rat_02_setLabel = tk.Button(self.commandFrame, text="Set", command=lambda: self.setRate(self.pump_B, rat_02.get(), units_02.get()))
        self.rat_02_setLabel.grid(row=line, column=6)
        #Start/stop
        self.start_02_Label = tk.Button(self.commandFrame, text="Start", relief=GROOVE, command=lambda: self.startStopPump(self.pump_B, True))
        self.start_02_Label.grid(row=line, column=8)
        self.stop_02_Label = tk.Button(self.commandFrame, text="Stop", relief=GROOVE, command=lambda: self.startStopPump(self.pump_B, False))
        self.stop_02_Label.grid(row=line, column=9)
        self.filler_02 = tk.Label(self.commandFrame, text = " ")
        self.filler_02.grid(row=line, column=10)
        #Volume
        self.vol_02_Label = tk.Entry(self.commandFrame, text = vol_02.get(), textvariable=vol_02, width = 10)
        self.vol_02_Label.grid(row=line, column=11)
        self.vol_02_setLabel = tk.Button(self.commandFrame, text="Set", command=lambda: self.setVolume(self.pump_B, vol_02.get()))
        self.vol_02_setLabel.grid(row=line, column=12)
        #Direction
        self.dir_02 = tk.Radiobutton(self.commandFrame, text="INF", variable=dir_02, value=1, command=lambda: self.setDirection(self.pump_B, dir_02.get()))
        self.dir_02.grid(row=line, column=14)
        self.dir_02 = tk.Radiobutton(self.commandFrame, text="WIT", variable=dir_02, value=2, command=lambda: self.setDirection(self.pump_B, dir_02.get()))
        self.dir_02.grid(row=line, column=15)
        
        #PUMP 3
        line = 3
        dia_03 = StringVar() 
        dia_03.set("0.000")
        vol_03 = StringVar() 
        vol_03.set("1.000")
        rat_03 = StringVar() 
        rat_03.set("0.000")
        dir_03 = IntVar()
        dir_03.set(0)
        units_03 = StringVar()
        self.pump_02_Label = tk.Label(self.commandFrame, text = "PUMP 3")
        self.pump_02_Label.grid(row=line, column=0)
        #Diameter
        self.dia_03_Label = tk.Entry(self.commandFrame, text = dia_03.get(), textvariable=dia_03, width = 10)
        self.dia_03_Label.grid(row=line, column=1)
        self.dia_03_setLabel = tk.Button(self.commandFrame, text="Set", command=lambda: self.setDiam(self.pump_C, dia_03.get()))
        self.dia_03_setLabel.grid(row=line, column=2)
        #Rate
        self.rat_03_Label = tk.Entry(self.commandFrame, text = rat_03.get(), textvariable=rat_03, width = 10)
        self.rat_03_Label.grid(row=line, column=4)
        self.uni_3 = ttk.Combobox(self.commandFrame, textvariable=units_03, width = 4)
        self.uni_3['values']=('MM','MH','UM','UH')
        self.uni_3.current(0) # 6
        self.uni_3.grid(row=line, column=5)
        self.rat_03_setLabel = tk.Button(self.commandFrame, text="Set", command=lambda: self.setRate(self.pump_C, rat_03.get(), units_03.get()))
        self.rat_03_setLabel.grid(row=line, column=6)
        #Start/stop
        self.start_03_Label = tk.Button(self.commandFrame, text="Start", relief=GROOVE, command=lambda: self.startStopPump(self.pump_C, True))
        self.start_03_Label.grid(row=line, column=8)
        self.stop_03_Label = tk.Button(self.commandFrame, text="Stop", relief=GROOVE, command=lambda: self.startStopPump(self.pump_C, False))
        self.stop_03_Label.grid(row=line, column=9)
        self.filler_03 = tk.Label(self.commandFrame, text = " ")
        self.filler_03.grid(row=line, column=10)
        #Volume
        self.vol_03_Label = tk.Entry(self.commandFrame, text = vol_03.get(), textvariable=vol_03, width = 10)
        self.vol_03_Label.grid(row=line, column=11)
        self.vol_03_setLabel = tk.Button(self.commandFrame, text="Set", command=lambda: self.setVolume(self.pump_C, vol_03.get()))
        self.vol_03_setLabel.grid(row=line, column=12)
        #Direction
        self.dir_03 = tk.Radiobutton(self.commandFrame, text="INF", variable=dir_03, value=1, command=lambda: self.setDirection(self.pump_C, dir_03.get()))
        self.dir_03.grid(row=line, column=14)
        self.dir_03 = tk.Radiobutton(self.commandFrame, text="WIT", variable=dir_03, value=2, command=lambda: self.setDirection(self.pump_C, dir_03.get()))
        self.dir_03.grid(row=line, column=15)        
        
        #=======================================================================
        #########################  RAMP MANAGER  ###############################
        #=======================================================================
        
        line = 0
        initialVal = IntVar()
        initialVal.set(5)
        finalVal = IntVar()
        finalVal.set(95)
        totalFLow = StringVar()
        totalFLow.set('1.0')
        stepNum = IntVar()
        stepNum.set(10)
        stepTime = IntVar()
        stepTime.set(2)
        stabStart = IntVar()
        stabStart.set(10)
        stabEnd = IntVar()
        stabEnd.set(10)
        self.fromLabel = tk.Label(self.rampFrame, text='From %')
        self.fromLabel.grid(row=line, column=0)
        self.fromENtry = tk.Entry(self.rampFrame, text=initialVal.get(), textvariable=initialVal, width = 3)
        self.fromENtry.grid(row=line, column=1)
        line+=1
        self.toLabel = tk.Label(self.rampFrame, text='to %')
        self.toLabel.grid(row=line, column=0)
        self.toENtry = tk.Entry(self.rampFrame, text=finalVal.get(), textvariable=finalVal, width = 3)
        self.toENtry.grid(row=line, column=1)
        line+=1
        self.totalFLowLabel = tk.Label(self.rampFrame, text='Total Flow')
        self.totalFLowLabel.grid(row=line, column=0)
        self.totalFLowEntry = tk.Entry(self.rampFrame, text=totalFLow.get(), textvariable=totalFLow, width = 3)
        self.totalFLowEntry.grid(row=line, column=1)
        line+=1
        self.stepNLabel = tk.Label(self.rampFrame, text='Step #')
        self.stepNLabel.grid(row=line, column=0)
        self.stepNLabelEntry = tk.Entry(self.rampFrame, text=stepNum.get(), textvariable=stepNum, width = 3)
        self.stepNLabelEntry.grid(row=line, column=1)
        line+=1
        self.stepTLabel = tk.Label(self.rampFrame, text='Step time (s)')
        self.stepTLabel.grid(row=line, column=0)
        self.stepTEntry = tk.Entry(self.rampFrame, text=stepTime.get(), textvariable=stepTime, width = 3)
        self.stepTEntry.grid(row=line, column=1)
        line+=1
        self.stabStartLabel = tk.Label(self.rampFrame, text='Stabilisation at start (s)')
        self.stabStartLabel.grid(row=line, column=0)
        self.stabStartEntry = tk.Entry(self.rampFrame, text=stabStart.get(), textvariable=stabStart, width = 3)
        self.stabStartEntry.grid(row=line, column=1)
        line+=1
        self.stabEndLabel = tk.Label(self.rampFrame, text='Stabilisation at end (s)')
        self.stabEndLabel.grid(row=line, column=0)
        self.stabEndEntry = tk.Entry(self.rampFrame, text=stabEnd.get(), textvariable=stabEnd, width = 3)
        self.stabEndEntry.grid(row=line, column=1)
        
        line+=1
        #self.seq_button = tk.Button(self.rampFrame, text="START RAMP", command=self.ramp_thread)
        self.seq_button = tk.Button(self.rampFrame, text="START RAMP", relief=GROOVE, 
                command=lambda: self.ramp_thread(initialVal.get(), finalVal.get(), 
                totalFLow.get(), stepNum.get(), stepTime.get(), stabStart.get(), stabEnd.get()))
        self.seq_button.grid(row=line, column=0)
        
        #=======================================================================
        #########################  TERNARY MANAGER  ############################
        #=======================================================================
        
        t_initial_A_Val = IntVar()  #A starting at
        t_initial_A_Val.set(0)
        t_final_A_Val = IntVar()    #A finishing at
        t_final_A_Val.set(100)
        t_steps_A = IntVar()    #A points to be done
        t_steps_A.set(10)
        t_flowTot = IntVar()    #Total flow
        t_flowTot.set(1)
        t_initial_C_Val = IntVar()  #C starting at
        t_initial_C_Val.set(95)
        t_final_C_Val = IntVar()    #C finishing at
        t_final_C_Val.set(50)
        t_steps_C = IntVar()    #C lines to be done
        t_steps_C.set(5)
        t_stepTime = IntVar()   #step duration s
        t_stepTime.set(1)
        t_stabStart = IntVar()  #stabilisation time
        t_stabStart.set(5)
        t_stabRamp = IntVar()   #stabilisation after each ramp
        t_stabRamp.set(10)
        
        #Marco changed 27th June 2018
        p = Path(os.path.abspath(sys.argv[0])).parents[1] 
        tmp = p / "ternary.gif"
        self.imgTernary = PhotoImage(file =tmp)
        #Marco end of changed 27th June 2018
        self.t_imgLabel = tk.Label(self.t_imgFrame, image =self.imgTernary)
        self.t_imgLabel.pack(side = TOP)
        self.formula1Label = tk.Label(self.t_imgFrame, text = "Fc = Pc * Ftot")
        self.formula1Label.pack(side = TOP)
        self.formula2Label = tk.Label(self.t_imgFrame, text = "Fab = (1-Pc)*Qtot")
        self.formula2Label.pack(side = TOP)
        self.formula3Label = tk.Label(self.t_imgFrame, text = "Fa = Pa * Fab")
        self.formula3Label.pack(side = TOP)
        
        line = 0
        #Pump C (PUMP C = pump 3)
        self.t_C_fromLabel = tk.Label(self.t_pumpCFrame, text='Pc - Range (%total): ')
        self.t_C_fromLabel.grid(row=line, column=0)
        self.t_C_fromENtry = tk.Entry(self.t_pumpCFrame, text=t_initial_C_Val.get(), textvariable=t_initial_C_Val, width = 3)
        self.t_C_fromENtry.grid(row=line, column=1)
        self.t_C_toLabel = tk.Label(self.t_pumpCFrame, text='to: ')
        self.t_C_toLabel.grid(row=line, column=2)
        self.t_C_toEntry = tk.Entry(self.t_pumpCFrame, text=t_final_C_Val.get(), textvariable=t_final_C_Val, width = 3)
        self.t_C_toEntry.grid(row=line, column=3)
        line+=1
        self.t_C_stepLabel = tk.Label(self.t_pumpCFrame, text='Step Pump C ')
        self.t_C_stepLabel.grid(row=line, column=0)
        self.t_C_stepEntry = tk.Entry(self.t_pumpCFrame, text=t_steps_C.get(), textvariable=t_steps_C, width = 3)
        self.t_C_stepEntry.grid(row=line, column=1)
        
        line = 0
        #Pumps A & B (PUMP A = pump1, PUMP B = pump2)
        self.t_A_fromLabel = tk.Label(self.t_pumpsABFrame, text='Pa - Range: ')
        self.t_A_fromLabel.grid(row=line, column=0)
        self.t_A_fromENtry = tk.Entry(self.t_pumpsABFrame, text=t_initial_A_Val.get(), textvariable=t_initial_A_Val, width = 3)
        self.t_A_fromENtry.grid(row=line, column=1)
        self.t_A_toLabel = tk.Label(self.t_pumpsABFrame, text='to: ')
        self.t_A_toLabel.grid(row=line, column=2)
        self.t_A_toEntry = tk.Entry(self.t_pumpsABFrame, text=t_final_A_Val.get(), textvariable=t_final_A_Val, width = 3)
        self.t_A_toEntry.grid(row=line, column=3)
        line+=1
        self.t_A_stepLabel = tk.Label(self.t_pumpsABFrame, text='Step Pumps A&B ')
        self.t_A_stepLabel.grid(row=line, column=0)
        self.t_A_stepEntry = tk.Entry(self.t_pumpsABFrame, text=t_steps_A.get(), textvariable=t_steps_A, width = 3)
        self.t_A_stepEntry.grid(row=line, column=1)
        
        
        #General ternary
        line = 0
        self.t_flowLabel = tk.Label(self.t_commandsFrame, text='Total flow')
        self.t_flowLabel.grid(row=line, column=0)
        self.t_flowEntry = tk.Entry(self.t_commandsFrame, text=t_flowTot.get(), textvariable=t_flowTot, width = 3)
        self.t_flowEntry.grid(row=line, column=1)
        line+=1
        self.t_stepTLabel = tk.Label(self.t_commandsFrame, text='Step time (s)')
        self.t_stepTLabel.grid(row=line, column=0)
        self.t_stepTEntry = tk.Entry(self.t_commandsFrame, text=t_stepTime.get(), textvariable=t_stepTime, width = 3)
        self.t_stepTEntry.grid(row=line, column=1)
        line+=1
        self.t_stabStartLabel = tk.Label(self.t_commandsFrame, text='Stabilisation at start (s)')
        self.t_stabStartLabel.grid(row=line, column=0)
        self.t_stabStartEntry = tk.Entry(self.t_commandsFrame, text=t_stabStart.get(), textvariable=t_stabStart, width = 3)
        self.t_stabStartEntry.grid(row=line, column=1)
        line+=1
        self.t_stabEndLabel = tk.Label(self.t_commandsFrame, text='Stabilisation after each scan (s)')
        self.t_stabEndLabel.grid(row=line, column=0)
        self.t_stabEndEntry = tk.Entry(self.t_commandsFrame, text=t_stabRamp.get(), textvariable=t_stabRamp, width = 3)
        self.t_stabEndEntry.grid(row=line, column=1)
        line+=1
        self.mpb = ttk.Progressbar(self.t_commandsFrame,orient ="horizontal",length = 200, mode ="determinate")
        self.mpb.grid(row=line, column=0)
        self.mpb["maximum"] = 100
        
        line+=1
        self.ternaryButton = tk.Button(self.t_commandsFrame, text="START TERNARY", relief=GROOVE, 
                command=lambda: self.ternary_thread(t_initial_A_Val.get(), t_final_A_Val.get(), t_initial_C_Val.get(),\
                                                    t_final_C_Val.get(), t_flowTot.get(), t_steps_A.get(), t_stepTime.get(),\
                                                    t_steps_C.get(), t_stabStart.get(), t_stabRamp.get()))
        self.ternaryButton.grid(row=line, column=0, pady = 15)
        
        
        #=========================== END TREEVIEW ==============================
 
        self.close_button = tk.Button(self.exitFrame, text="Close", command=self.my_quit)
        self.close_button.pack()
        #self.close_button.place(relx=0.5, rely=0.5, anchor=CENTER)
        
                 
#         self.start_button = tk.Button(self.commandFrame, text="Start", command=self.startCMD)
#         self.start_button.pack(side=LEFT, after = self.startStopLabel)
#           
#         self.stop_button = tk.Button(self.commandFrame, text="Stop", command=self.stopCMD)
#         self.stop_button.pack(side=LEFT, after = self.start_button)
        
#         
#         
#         
#         self.queue_button = tk.Button(text="Print queue", command=self.printQueue)
#         self.queue_button.pack()
#         
#         
#         self.update_button = tk.Button(text="UP", command=self.UP)
#         self.update_button.pack()
#            
    
    
    def ramp_thread(self, initial, final, total, step, delta, start, end):
        def callback():
            my_total = float(total)
            act_flowA = my_total*initial/100.0
            act_flowB = my_total*final/100.0
            flowDelta = (act_flowB - act_flowA)/step
            pump1 = self.pump_A.address
            pump2 = self.pump_B.address
            my_delta = delta - 2*(100/1000) - 2*(100/1000)
            logging.info("Ramp thread - START")
            print("Ramp thread - START")
            
            
            if not self.closing:
                #Initial stabilisation
                self.serialCMD(pump1, self.commands['Rate'], act_flowA)
                self.serialCMD(pump2, self.commands['Rate'], act_flowB)
                self.serialCMD(pump1, self.commands['Start'], '') #Starts even if it is already started (not sure what the user does)
                self.serialCMD(pump2, self.commands['Start'], '') #Starts even if it is already started
                self.askRate(1)
                self.askRate(2)
                print("Initial stabilisation started: " + str(start) + " seconds")
                print(str(act_flowA) + "\t" + str(act_flowB))
                
                logging.info("PUMP 1\tPUMP2\tstep")
                logging.info(str(act_flowA) + "\t" + str(act_flowB) + "\t" + " -2")
                
                my_time = 0
                scanTime = start/10.0
                while my_time < start:
                    if not self.closing:
                        my_time = my_time+scanTime
                        time.sleep(scanTime)
                        #print(str(my_time))
                    else:
                        print("Ramp ABORTED due to user request")
                        logging.warning("Ramp ABORTED due to user request")
                        break
                
                logging.info(str(act_flowA) + "\t" + str(act_flowB) + "\t" + " -1")     
                           
                #Ramp
                for x in range(0, step):
                    if not self.closing:
                        #logging.info("Step ramp: " + str(x))
                        act_flowA = act_flowA + flowDelta
                        act_flowB = my_total-act_flowA
                        self.serialCMD(pump1, self.commands['Rate'], act_flowA)
                        self.serialCMD(pump2, self.commands['Rate'], act_flowB)
                        self.askRate(1)
                        self.askRate(2)
                        print(str(act_flowA) +"\t" + str(act_flowB))
                        logging.info(str(act_flowA) + "\t" + str(act_flowB) + "\t" + str(x))
                        time.sleep(my_delta)
                    else:
                        logging.warning("Ramp ABORTED due to user request")
                        print("Ramp ABORTED in for cycle due to user request")
                        break
                
                if not self.closing:
                    #Final stabilisation
                    act_flowA = my_total*final/100.0
                    act_flowB = my_total*initial/100.0
                    self.serialCMD(pump1, self.commands['Rate'], act_flowA)
                    self.serialCMD(pump2, self.commands['Rate'], act_flowB)
                    self.askRate(1)
                    self.askRate(2)
                    logging.info(str(act_flowA) + "\t" + str(act_flowB) + "\t")
                    print(str(act_flowA) + "\t" + str(act_flowB) + "\t" )
                
                    my_time = 0
                    scanTime = end/10.0
                    while my_time < end:
                        if not self.closing:
                            my_time = my_time+scanTime
                            time.sleep(scanTime)
                            #print(str(my_time))
                        else:
                            print("Ramp ABORTED due to user request")
                            logging.warning("Ramp ABORTED due to user request")
                            break
                else:
                    print("Ramp ABORTED due to user request")
                    logging.warning("Ramp ABORTED due to user request")
            else:
                print("Ramp ABORTED due to user request")
                logging.warning("Ramp ABORTED due to user request")
            
            print("End of ramps")
            logging.info("Ramp thread - end")
            
        self.ramp = threading.Thread(target=callback)
        self.ramp.start()
        
        
    def ternary_thread(self, initial_A, final_A, initial_C, final_C, total, step_A, delta_A, step_C, start_time, ramp_pause):
        def updateProgess(step):
            #To update the progress bar
            self.mpb.step(step)
        def callback():
            #Save locally the parameters - no jokes from geeks
            logging.info("Ternary thread - start")
            my_initial_A = initial_A/100.0
            my_final_A = final_A/100.0
            my_initial_C = initial_C/100.0
            my_final_C = final_C/100.0
            #Progressbar
            my_delta_A = delta_A - 2*(100/1000) - 3*(100/1000)
            my_progress_step = 100/(step_A*step_C*my_delta_A + start_time + ramp_pause*step_C)
            my_total = total
            act_flowC = my_initial_C * my_total
            act_flowA = my_initial_A * (my_total - act_flowC) 
            act_flowB = (my_total - act_flowA - act_flowC)
            print(act_flowC, act_flowA)
            if (act_flowA+act_flowB+act_flowC) != my_total :
                print ("CALCULATION ERROR")
                raise
            #Set the serial parameters
            pump1 = self.pump_A.address
            pump2 = self.pump_B.address
            pump3 = self.pump_C.address
            #Initialise the direction of the ramps
            goUP = True 
            flowDelta_AB = 0
            flowDelta_C = abs(my_total*(my_final_C-my_initial_C))/(step_C-1)    #Fixed
            
            if not self.closing:
                #Initial stabilisation
                self.serialCMD(pump1, self.commands['Rate'], act_flowA)
                self.serialCMD(pump2, self.commands['Rate'], act_flowB)
                self.serialCMD(pump3, self.commands['Rate'], act_flowC)
                self.serialCMD(pump1, self.commands['Start'], '') #Starts even if it is already started (not sure what the user does)
                self.serialCMD(pump2, self.commands['Start'], '') #Starts even if it is already started
                self.serialCMD(pump3, self.commands['Start'], '') #Starts even if it is already started
                self.askRate(1)
                self.askRate(2)
                self.askRate(3)
                print("Initial stabilisation started: " + str(start_time) + "seconds")
                
                print("Pump 1 at " + str(act_flowA) + ", Pump 2 at " + str(act_flowB) + ", Pump 3 at " + str(act_flowC))
                
                my_time = 0
                scanTime = start_time/10.0
                #This bullshit is to avoid interface freeze
                while my_time < start_time:
                    if not self.closing:
                        my_time = my_time+scanTime
                        time.sleep(scanTime)
                        #print(str(my_time))
                    else:
                        #print("Ramp ABORTED due to user request")
                        logging.warning("Ramp ABORTED due to user request")
                        break
        
                updateProgess(my_progress_step*start_time)                
                #TERNARY
                print ("Start of the triangle")
                for _C in range (0,step_C):
                    print ("____C____ iteration " + str(_C))
                    if (goUP == True):
                        act_flowA = my_initial_A * (my_total - act_flowC)
                        act_flowB = (my_total - act_flowA - act_flowC)
                    else:
                        act_flowA = my_final_A * (my_total - act_flowC)
                        act_flowB = (my_total - act_flowA - act_flowC)
                    
                    print("Calculated flow A" + str(act_flowA))
                    print("Calculated flow B" + str(act_flowB))
                    
                    flowDelta_AB = abs((my_total-act_flowC)*(my_final_A-my_initial_A))/(step_A+1)
                    print("Delta AB = " + str(flowDelta_AB))
                    if not self.closing:
                        for _AB in range(0, step_A):
                            #print ("____AB____ iteration" + str(_AB))
                            #bullshit
                            # my_act_step+=1
                            updateProgess(my_progress_step)
                            
                            if not self.closing:
                                logging.info("Step ramp: " + str(_AB))
                                if (goUP == True):
                                    act_flowA = act_flowA + flowDelta_AB
                                    act_flowB = my_total-act_flowC-act_flowA
                                else:
                                    act_flowA = act_flowA - flowDelta_AB
                                    act_flowB = my_total-act_flowC-act_flowA
                                self.serialCMD(pump1, self.commands['Rate'], act_flowA)
                                self.serialCMD(pump2, self.commands['Rate'], act_flowB)
                                self.askRate(1)
                                self.askRate(2)
                                self.askRate(3)
                                print(str(act_flowA) +"\t" + str(act_flowB) + "\t" + str(act_flowC))
                                #Keep the flow for delta_A seconds
                                time.sleep(my_delta_A)
                            else:
                                logging.warning("Ramp ABORTED due to user request")
                                #print("Ramp ABORTED in for cycle due to user request")
                                break
                    else:
                        logging.warning("Ramp ABORTED due to user request")
                        #print("Ramp ABORTED in for cycle due to user request")
                        break
                    #Stabilise the ramp (you will thank me for this)
                    print("Start stabilisation after ramp")
                    my_time = 0
                    scanTime = ramp_pause/10.0
                    while my_time < ramp_pause:
                        print("Waiting new ramp")
                        if not self.closing:
                            my_time = my_time+scanTime
                            time.sleep(scanTime)
                            #print(str(my_time))
                        else:
                            #print("Ramp ABORTED due to user request")
                            logging.warning("Ramp ABORTED due to user request")
                            break
                    updateProgess(my_progress_step*ramp_pause)
                    #Update C flow
                    act_flowC-=flowDelta_C
                    act_flowA = (my_total-flowDelta_C)
                    if (_C != (step_C-1)):
                        self.serialCMD(pump3, self.commands['Rate'], act_flowC)
                        logging.info("Pump 3 at " + str(act_flowC))
                    else:
                        logging.info("Pump 3 not set, last iteration!")
                        print("Pump 3 at " + str(act_flowC))
                    goUP = not(goUP)
                    
                
                print("Pump 3 still at " + str(act_flowC))
                
                if not self.closing:
                    #Final stabilisation
                    act_flowC = my_final_C * my_total 
                    act_flowA = my_final_A * (my_total - act_flowC)
                    act_flowB = (my_total - act_flowA - act_flowC)
                    self.serialCMD(pump1, self.commands['Rate'], act_flowA)
                    self.serialCMD(pump2, self.commands['Rate'], act_flowB)
                    self.serialCMD(pump3, self.commands['Rate'], act_flowC)
                    self.askRate(1)
                    self.askRate(2)
                    self.askRate(3)
                    logging.info("Final stabilisation started: " + str(start_time) + "seconds")
                    logging.info("Pump 1 at " + str(act_flowA) + ", Pump 2 at " + str(act_flowB) + ", Pump 3 at " + str(act_flowC))
                
                    my_time = 0
                    scanTime = start_time/10.0
                    while my_time < start_time:
                        if not self.closing:
                            my_time = my_time+scanTime
                            time.sleep(scanTime)
                            #print(str(my_time))
                        else:
                            #print("Ramp ABORTED due to user request")
                            logging.warning("Ramp ABORTED due to user request")
                            break
                else:
                    print("Ramp ABORTED due to user request")
                    logging.warning("Ramp ABORTED due to user request")
            else:
                print("Ramp ABORTED due to user request")
                logging.warning("Ramp ABORTED due to user request")
            
            self.mpb.stop()
            logging.info("Ramp thread - end")
            
        self.ternary = threading.Thread(target=callback)
        self.ternary.daemon = True
        self.ternary.start()
        
    def popup(self):
        #To set the address
        self.w = popupWindow(self.master)
        self.master.wait_window(self.w.top)
        #Check boundaries
        if self.w.isOk == True:
            self.setADDR(self.commands["Address"], str(self.w.value))
            logging.info("Address set to " + str(self.w.value))
    
    def getSWInfo(self):
        #Retrieve the SW version
        self.warningPopUp(SW_INFO)
            

    def startStopPump(self, pumpId, start):
        logging.info('Starting' if (start == True) else 'Stopping' + ' pump ' + pumpId.address)
        self.serialCMD(pumpId.address, self.commands['Start' if (start == True) else 'Stop'], '')
        self.askNews(pumpId.address)
    def setDiam(self, pumpId, diam):
        diam = float(diam)
        #logging.info('Setting diameter of pump + ' pumpId.address ' to ' + diam + " mm")
        self.serialCMD(pumpId.address, self.commands['Diameter'], str(diam))
        self.askDiameter(pumpId.address)
    def setVolume(self, pumpId, vol):
        vol = float(vol)
        #logging.info('Setting diameter of pump + ' pumpId.address ' to ' + diam + " mm")
        self.serialCMD(pumpId.address, self.commands['Volume'], str(vol))
        self.askVolume(pumpId.address)
    def setDirection(self, pumpId, direction):
        direction = int(direction)
        #logging.info('Setting diameter of pump + ' pumpId.address ' to ' + diam + " mm")
        if direction == 1:
            self.serialCMD(pumpId.address, self.commands['InfusionDir'], '')
        elif direction == 2:
            self.serialCMD(pumpId.address, self.commands['WithdrawDir'], '')
        else:
            print("DEVELOPMENT ERROR!!!")
            raise
        self.askRate(pumpId.address)
    def setRate(self, pumpId, rate, units):
        #logging.info('Setting rate of pump + ' pumpId.address ' to ' + rate + " mm")
        if (pumpId.getStatus() ==  'Infusing') or (pumpId.getStatus()== 'Withdrawing'):
            units = ''
            logging.warning("Skip units!")
        else:
            rate = float(rate)
        self.serialCMD(pumpId.address, self.commands['Rate'], str(rate)+str(units))
        self.askRate(pumpId.address)
        
#     def UP(self):
#         # To retrieve information from the treeview - JUST A TRY
#         children = self.table.get_children()
#         print(children)
#         print (self.table.item('01').get('values'))
#         prova = self.table.item('01').get('values')
#         print (prova[2])
#         print (self.table.item('01'))
#         
#         #To update a field
#         self.table.set('01', column='diameter', value='CACCA') 
        
    def choseBaudrate(self):
        #Choose baudrate
        self.baudrateChosen = ttk.Combobox(self.connectionFrame, textvariable=self.baudrate.get(), state='readonly') #3
        self.baudrateChosen['values'] = (19200, 9600, 2400, 1200, 300) # 4
        self.baudrateChosen.current(1) # 6
        self.baudrateChosen.pack(side = LEFT)
        
    def choseCOM(self):
        #Choose COM
        self.COMnumberChosen = ttk.Combobox(self.connectionFrame, textvariable=self.COMnumber.get(), state='readonly') #3
        self.COMnumberChosen['values'] = self.serial_ports() # 4#
        if len(self.COMnumberChosen["values"]) == 0:
            self.COMnumberChosen['values'] = 'ERROR'
        self.COMnumberChosen.current(0) # 6
        self.COMnumberChosen.pack(side = LEFT)
        
    def showPumpInfo(self):
        self.labelSelectCOM = tk.Label(text="Select a COM port:") # 1
        self.labelSelectCOM.pack()
        
    def warningPopUp(self, string):
        top = tk.Toplevel()
        label1 = tk.Label(top, text=string, height=10, width=50)
        label1.pack()
        
        button = tk.Button(top, text="Continue", command=top.destroy)
        button.pack()
    
    def openPort(self):
        self.ser.port=self.COMnumberChosen.get()
        self.ser.baudrate=self.baudrateChosen.get()
        self.ser.parity=serial.PARITY_NONE
        self.ser.stopbits=serial.STOPBITS_ONE
        self.ser.bytesize=serial.EIGHTBITS
        self.ser.timeout = 0
        logging.info('Opening ' + self.COMnumberChosen.get() + ' at baudrate ' + self.baudrateChosen.get())
        #Just to be sure close it, in case something has changed
        try:
            self.ser.close()
        except:
            pass
        #Now open the port
        try:
            self.ser.open()
            logging.info ('openPort ok')
            self.openCOM.configure(fg = "green")
            self.version_button.configure(fg="red")
            #Reset serial queues
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            #Start listening
            self.handle_readSerial()
            self.rt = RepeatedTimer(1, self.printQueue) # it auto-starts, no need of rt.start()
        except:
            logging.error ('openPort operation failed')
        
        self.version_button.configure(fg = "red")
        self.version_button.focus()
        
    def setADDR(self, cmd, options):
        options = str(options[:3]).zfill(2)
        toWrite = str(cmd) + str(options) + '\r'
        try:
            self.ser.write(toWrite.encode())
        except:
            logging.error("Error during serialCMD command: " + str(toWrite) )
        time.sleep(50/1000)
        
    def serialCMD(self, pumpId, cmd, options):
        if options != '':
            options = str(options)
            options = str(options[:5]).zfill(5)
        toWrite = str(pumpId).zfill(2) + str(cmd) + str(options) + '\r'
        try:
            self.ser.write(toWrite.encode())
        except:
            logging.error("Error during serialCMD command: " + str(toWrite) )
        time.sleep(100/1000)
        
    def askFWVer(self):
#         self.lostPump(1)
#         self.lostPump(2)
#         self.lostPump(3)
        #Scan range
        for x in range(0, 4):
            if (self.closing == False):
                logging.info("Looking for pump " + str(x))
                print("Looking for pump " + str(x))
                self.serialCMD(x,  self.commands['Rate'], '')   
                time.sleep (100.0 / 1000.0);
                self.serialCMD(x,  self.commands['Diameter'], '')  
                time.sleep (100.0 / 1000.0);
                self.serialCMD(x,  self.commands['Volume'], '')  
                time.sleep (100.0 / 1000.0);
                self.serialCMD(x,  self.commands['Version'], '')
                time.sleep (200.0 / 1000.0);
            else: #Impossible
                logging.warning("Scan pumps operation ABORTED due to user request")

        self.version_button.configure(fg='black')
        self.master.focus() #Just to remove the focus on the button

        
    def handle_readSerial(self):
        """ Reads serial messages
        """
        def serial_callback():
            flagToCompact = False
            output = ''
            while not self.closing:
                #Makes it possible to close when closing is set
                if self.ser.inWaiting():
                    rcv_char = self.ser.readline(self.ser.inWaiting())#.decode('utf-8')
                    #print("rcv_char" + str(rcv_char))
                    if rcv_char ==  serial.to_bytes([0x02]):
#                         logging.info('Found STX')
                        flagToCompact = True
                        output = ''
                    elif rcv_char ==  serial.to_bytes([0x03]):
#                         print('Found ETX')
                        logging.debug(output)
                        self.q.put(output)
                        flagToCompact = False
                    
                    if (flagToCompact    and (rcv_char !=  serial.to_bytes([0x02])) \
                                        and (rcv_char !=  serial.to_bytes([0x03]))\
                                        and (rcv_char !=  serial.to_bytes([0x00]))):
                        #Build the output
                        try:
                            output = output + rcv_char.decode()
                        except:
                            logging.error("serial_callback " + output)
        self.rcv = threading.Thread(target=serial_callback)
        self.rcv.start()
        
    def serial_ports(self):
        """ Lists serial port names
    
            :raises EnvironmentError:
                On unsupported or unknown platforms
            :returns:
                A list of the serial ports available on the system
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
        #return ["COM1", "COM2", "COM3"] #debug
        return result
    
    def drain(self):
        while True:
            try:
                yield self.q.get_nowait()
            except queue.Empty: 
                break
    
    def update(self, pumpObj, data):
        len_data = len(data)
        #print (data, len_data)
        if (len_data == 0):
            logging.error("ERROR SERIAL RCV - NULL STR")
            exit()
        
        flagCheckData = True
        flagAlarm = False
        
        if data[0] == self.prompts['Infusing']:
            pumpObj.status = 'Infusing'
            if (len_data == 1 ):
                flagCheckData = False
            
        elif data[0] == self.prompts['Withdrawing']:
            pumpObj.status = 'Withdrawing'
            if (len_data == 1 ):
                flagCheckData = False
            
        elif data[0] == self.prompts['Stopped']:
            pumpObj.status = 'Stopped'
            if (len_data == 1 ):
                flagCheckData = False
            
        elif data[0] == self.prompts['Paused']:
            pumpObj.status = 'Paused'
            if (len_data == 1 ):
                flagCheckData = False
            
        elif data[0] == self.prompts['Phase Paused']:
            pumpObj.status = 'Phase Paused'
            if (len_data == 1 ):
                flagCheckData = False
            
        elif data[0] == self.prompts['Trigger Wait']:
            pumpObj.status = 'Trigger Wait'
            if (len_data == 1 ):
                flagCheckData = False
            
        elif data[0] == self.prompts['Alarm']:
            pumpObj.status = 'Alarm'
            flagCheckData = False
            flagAlarm = True
            
            if (len_data < 3):
                logging.error("ERROR SERIAL RCV - SHORT STR")
                exit()
                
            if (data[1] != '?'):
                logging.error("ERROR SERIAL RCV - Not found '?'")
                exit()
            
            if data[2] == self.alarms['Pump reset']:
                pumpObj.warnings = 'Pump reset'
            elif data[2] == self.alarms['STALL']:
                pumpObj.warnings = 'STALL'
            elif data[2] == self.alarms['Safe Comm time out']:
                pumpObj.warnings = 'Safe Comm time out'
            elif data[2] == self.alarms['Pumping prg ERROR']:
                pumpObj.warnings = 'Pumping prg ERROR'
            elif data[2] == self.alarms['Phase Out Of Range']:
                pumpObj.warnings = 'Phase Out Of Range' 
            else:
                logging.error ("Alarm " + data + "from pump " + pumpObj.address + 'is NOT handled')
                #self.lostPump(pumpObj.address)
                exit()
            self.updateTable(pumpObj.address, 'warnings', pumpObj.warnings)
        else:
            logging.info ("RSP " + data + "from pump " + pumpObj.address + 'is NOT handled')
            #self.lostPump(pumpObj.address)
            exit()

        self.updateTable(pumpObj.address, 'status', pumpObj.status)        
        
        if flagCheckData :
            flagCheckData = False
            flagAlarm = True
            if data[1] == '?':
                if data[2:len_data] == 'NA':
                    pumpObj.warnings = 'Command Not Applicable'
                elif data[2:len_data] == 'OOR':
                    pumpObj.warnings = 'Data Out Of Range'
                elif data[2:len_data] == 'COM':
                    pumpObj.warnings = 'Invalid Packet Received'
                elif data[2:len_data] == 'IGN':
                    pumpObj.warnings = 'Command Ignored'
                else:
                    pumpObj.warnings = 'Command Not Recognised'
                
                self.updateTable(pumpObj.address, 'warnings', pumpObj.warnings)
            elif data[1:3] == 'NE':
                pumpObj.firmware = data[1:]
                logging.info ("FW version for pump " + pumpObj.address + " " + data[1:])
                print("FW version for pump " + pumpObj.address + " " + data[1:])
                               
                pumpObj.detected = True          #warnings
                self.updateTable(pumpObj.address, 'firmware', pumpObj.firmware)
            else:
#                 logging.info ('Pump ' + pumpObj.address + ' is ' + pumpObj.status + ' ERROR: ' + pumpObj.warnings)
#                 exit()
                try:
                    value = ast.literal_eval(data[1:6])
                except:
                    print("ERROR! " + str(data[1:6]) + str(len(data)))
                if (data[6:8] == 'ML') or (data[6:8] == 'UL'):
                    # It is a dispensed volume
                    volUnits = 'ul'
                    if (data[6:8] == 'ML'):
                        volUnits = 'ml'
                    pumpObj.volume = str(value) + str(volUnits)
                    self.updateTable(pumpObj.address, 'dispensed', pumpObj.volume)
                elif (data[6:8] == 'MH') or (data[6:8] == 'MM') or (data[6:8] == 'UM') or (data[6:8] == 'UH'):
                    # It is a flowrate
                    flowUnits = 'ml/min'
                    if (data[6:8] == 'MH'):
                        flowUnits = 'ml/h'
                    elif (data[6:8] == 'UM'):
                        flowUnits = 'ul/min'
                    elif (data[6:8] == 'UH'):
                        flowUnits = 'ul/h'
                    else:
                        #already set
                        pass
                    pumpObj.units = flowUnits
                    self.updateTable(pumpObj.address, 'units', pumpObj.units)
                    pumpObj.rate = value
                    self.updateTable(pumpObj.address, 'rate', pumpObj.rate)
                else:
                    #If nothing is added, it is a diameter
                    pumpObj.diameter = data[1:6]
                    self.updateTable(pumpObj.address, 'diameter', pumpObj.diameter)
        
        if not flagAlarm:
            self.updateTable(pumpObj.address, 'warnings', 'OK')
            flagAlarm =  False                
                    
                    
                
    def updateTable(self, pumpId, col, val):
        """ Used to update what is displayed on the screen about pumps
        """
        #logging.info ('TABLE UPDATE pump '+ str(pumpId) + ': ' + str(col) + ' ' + str(val))
        self.table.set(pumpId, column=col, value=val)
        
            
       
    def printQueue(self):
        for item in self.drain():
            if DEBUG == True:
                logging.debug('Dequeuing ' + item)
            if item[:2] == '01':
                #logging.info('Message from PUMP 1')
                self.update(self.pump_A, item[2:])                    
            elif item[:2] == '02':
                #logging.info('Message from PUMP 2')
                self.update(self.pump_B, item[2:])
            elif item[:2] == '03':
                #logging.info('Message from PUMP 3')
                self.update(self.pump_C, item[2:])
            else:
                logging.error("ERROR - NOT SUPPORTED PUMP")
                
#         if self.pump_A.detected==True:
#             self.askNews(1)
#         if self.pump_B.detected==True:
#             self.askNews(2)
#         if self.pump_C.detected==True:
#             self.askNews(3)
        
    def askNews(self, pump):
        self.serialCMD(pump,  self.commands['Rate'], '')   
        #time.sleep (100.0 / 1000.0);
        self.serialCMD(pump,  self.commands['Diameter'], '')  
        #time.sleep (100.0 / 1000.0);
        self.serialCMD(pump,  self.commands['Volume'], '')  
        #time.sleep (100.0 / 1000.0);
    
    def askRate(self, pump):
        self.serialCMD(pump,  self.commands['Rate'], '')   
        #time.sleep (50.0 / 1000.0);
    
    def askVolume(self, pump):
        self.serialCMD(pump,  self.commands['Volume'], '')   
        #time.sleep (100.0 / 1000.0);
        
    def askDiameter(self, pump):
        self.serialCMD(pump,  self.commands['Diameter'], '')   
        #time.sleep (100.0 / 1000.0);
        
    def my_quit(self):
        self.closing = True
        try:
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            self.ser.close()
        except:
            pass
        try:
            self.rt.stop()
        except:
            pass
        quit()


root = tk.Tk()
root.title("redPumps")
root.geometry("850x550")
root.resizable(1, 1)
app = redPumps_GUI(root)

root.mainloop()
