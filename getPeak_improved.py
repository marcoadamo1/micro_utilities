import os
from pathlib import Path # Check this library, very cool
import numpy as np
#import matplotlib.pyplot as plt
from tkinter import *
from tkinter import ttk
from tkinter.filedialog import askopenfilename, askdirectory

import peakutils
from peakutils.plot import plot as pplot
from matplotlib import pyplot


root = Tk(  )

HEADER = "Mod_Q\tI\tErr_I\tSigma_Q\n\n"
SKIPROWS = 40

def smooth(x,window_len=11,window='hanning'):
    
    if x.ndim != 1:
        raise ValueError("smooth only accepts 1 dimension arrays.")

    if x.size < window_len:
        raise ValueError("Input vector needs to be bigger than window size.")


    if window_len<3:
        return x


    if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
        raise ValueError("Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'")

    s=np.r_[x[window_len-1:0:-1],x,x[-2:-window_len-1:-1]]
    #print(len(s))
    if window == 'flat': #moving average
        w=np.ones(window_len,'d')
    else:
        w=eval('np.'+window+'(window_len)')

    y=np.convolve(w/w.sum(),s,mode='valid')
    return y

def getPeak():
    ### =============  FOLDER LOADING  =============
    path = Path(askdirectory(initialdir="C:/Users/adamo/OneDrive - Imperial College London/",
                           title = "Choose a file."))
    print ("Opening files in {}".format(path))
    
    files = os.listdir(path)
    toRemove = np.loadtxt(path / files[0], skiprows=SKIPROWS)
    linesInFile = len(toRemove[:,1])

    ### =============  DECLARATION  =============
    I_total = np.zeros(linesInFile)
    Q_total = np.zeros(linesInFile)
    E_total = np.zeros(linesInFile)
    peakPosition = np.zeros(len(files))
    peakIntensity = np.zeros(len(files))
    number = np.arange(1, len(files)+1, 1, dtype=int)

    i = 0
    exit = False
    for filename in files:
        if not exit:
            ### =============  FILE LOADING  =============
            print(filename) #Check if it reads in the correct order
            tmp = path / filename
            d = np.loadtxt(tmp, skiprows=40) #To access a full column: d[:,0]
            if (len(d[:,0]) != linesInFile):
                # Just in case someone manually modified a single file
                print("File length not expected")
                raise
            I_total = d[:,1]
            Q_total = d[:,0]
            #E_total = d[:,2]
            #sigma_total = d[:,3]
            
            ### =============  SMOOTH THE SIGNALS  =============
            windowLen = 11
            windowIdx = int(windowLen/2)
            a = smooth(I_total,window_len=windowLen,window='blackman')
            a = a[windowIdx:-windowIdx]
            if len(a) != len(I_total):
                print("Unexpected length of the smoothed signal!")
                print(len(a),len(I_total))
                raise ValueError("Unexpected vector length")
            if 0: #DEBUG: check if the smoothing is ok
                pyplot.plot(I_total)
                pyplot.plot(a)
                pyplot.yscale('log')
                pyplot.xscale('log')
                pyplot.show()
            I_total = a #Save the smooth signal for interpolation
            
            ### =============  GET PEAK POSITIONS  =============
            indexes = peakutils.indexes(I_total, thres=0.3, min_dist=40)
            tmp = peakutils.interpolate(Q_total, I_total, width=3, ind=indexes)
            
            if (tmp.size > 1):
                print(tmp.size)
                pyplot.figure(figsize=(10,6))
                pplot(Q_total, I_total, indexes)
                pyplot.title('First estimate')
                pyplot.show()
                peakPosition[i] = Q_total[0]
            else:
                peakPosition[i] = tmp
            print(peakPosition[i])
            #try:
            #    peakPosition[i] = peakutils.interpolate(Q_total, I_total, ind=indexes)
            #    print("...{}".format(peaks_x))
            #except:
            #    print("ABORT")
            #    peakPosition[i] = Q_total[np.argmax(I_total)]
            #exit = True
            
            # Get the maximum value for each file
            #peakPosition[i] = Q_total[np.argmax(I_total)]
            peakIntensity[i] = np.max(I_total)
            i+=1

    output = ["peak_pos.dat", "peak_int.dat"]
    for i in range(0, len(output)):
        output[i] = path.parent / output[i]
    np.savetxt(output[1], np.c_[number,peakPosition], fmt='%.18e', delimiter='\t', newline='\n', header="number\tpeakPosition\t", footer='', comments='')
    np.savetxt(output[2], np.c_[number,peakIntensity], fmt='%.18e', delimiter='\t', newline='\n', header="number\tpeakPosition\t", footer='', comments='')
    

    
    
    
    
    
    

Title = root.title( "Peak Position")
#label = ttk.Label(root, text ="I'm BATMAN!!!",foreground="red",font=("Helvetica", 16))
#label.pack()

#Menu Bar

menu = Menu(root)
root.config(menu=menu)

file = Menu(menu)

file.add_command(label = 'Open', command = getPeak)
file.add_command(label = 'Exit', command = lambda:exit())

menu.add_cascade(label = 'File', menu = file)





root.mainloop()