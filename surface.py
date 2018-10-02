from tkinter import *
from tkinter import ttk
from tkinter.filedialog import askopenfilename, askdirectory

from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 unused import

import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.ticker import LinearLocator, FormatStrFormatter
    
import numpy as np
import pandas as pd

from pathlib import Path
import os

#This routines expects data into columns (the first is the q-vector, the second the intensity).
#Further columns (i.e. error, smearing) would be skipped


# Mode types
# - 0 -> export only a big matrix, with the run number in the first row and q in the first column - Origin!
# - 1 -> export 3 files: X, Y as single columns and Z as a 2D matrix
# - 2 -> export 3 files: X, Y and Z, where all are a single column
mode = 0
SKIPROWS = 40 #Number of header lines from GRASP (if data is in line 41, SKIPROWS=40)
alsoVisualise = True #Change to True to visualise the data in 3D
toClip = False #You can clip the data to remove outliers (NOT RECOMMENDED)

root = Tk()

def OpenFile():
    path = Path(askdirectory(initialdir="C:/",
                           title = "Choose a file.")) #Change 
    print ("Opening files in {}".format(path))
    files = os.listdir(path)

    # START - DO NOT TOUCH
    toRemove = np.loadtxt(path / files[0], skiprows=SKIPROWS)
    linesInFile = len(toRemove[:,1])
    # END of DO NOT TOUCH

    number = np.arange(0, len(files), 1, dtype=int) # Step (or D2O concentration)
    if mode == 0 or mode == 1: # 2D!
        I_total = np.zeros((linesInFile, len(files))) # Neutron intensity
    else:
        I_total = np.zeros((linesInFile* len(files)))

    Q_total = toRemove[:,0] # Scattering vector
    #E_total = np.zeros((linesInFile, len(files)))

    if len(files) == 0:
        print ("No files in the selected folder")
        return
    else:
        i = 0
        for filename in files:
            tmp = path / filename
            print(filename)
            d = np.loadtxt(tmp, skiprows=SKIPROWS) #To access a full column: d[:,0]
            if (len(d[:,0]) != linesInFile):
                # Just in case someone manually modified a single file
                raise ValueError('Dimensions do not agree')
            if mode == 0 or mode == 1: # 2D!
                I_total[:, i] = d[:,1]
            else: # mode == 2, just columns
                for idx,item in enumerate(d[:,1]):
                    I_total[i*linesInFile + idx] = item # 1D vector
            i+=1
            
        if toClip == True:
            #To clip the data, usually not needed (i.e. set max and min in origin if need to clip)
            min_value = 0.001
            max_value = None
            np.clip(I_total, a_min = min_value, a_max = max_value, out = I_total)

        if alsoVisualise == True: # To visualise data
            fig = plt.figure()
            ax = fig.gca(projection='3d')

            # Make data.
            X = number
            Y = Q_total
            X, Y = np.meshgrid(X, Y)
            Z = I_total
            # Plot the surface.
            surf = ax.plot_surface(X, Y, np.log(Z), cmap=cm.hot,
                                   linewidth=0, antialiased=False)
            # Add a color bar which maps values to colors.
            fig.colorbar(surf, shrink=0.5, aspect=5)
            plt.show()
        
        if mode == 0: # Single flie
            I = pd.Index(Q_total)
            C = pd.Index(number)
            df = pd.DataFrame(data=I_total, index=I, columns=C)
            output = path.parent / 'XYZ_CV.csv'
            df.to_csv(output)
        else: # Three files 
            output = ["X_CV.dat", "Y_CV.dat", "Z_CV.dat"]
            for i in output:
                output[i] = path.parent / output[i]
            np.savetxt(output[0], number, fmt='%.18e', delimiter='\t', newline='\n', footer='', comments='')
            np.savetxt(output[1], Q_total, fmt='%.18e', delimiter='\t', newline='\n', footer='', comments='')
            np.savetxt(output[2], I_total, fmt='%.18e', delimiter='\t', newline='\n', footer='', comments='')
    
    quit()
    

Title = root.title( "File Opener")
#Menu Bar
menu = Menu(root)
root.config(menu=menu)

file = Menu(menu)

file.add_command(label = 'Open', command = OpenFile)
file.add_command(label = 'Exit', command = lambda:exit())

menu.add_cascade(label = 'File', menu = file)

root.mainloop()