# RTD CALCULATION FOR MICROFLUIDIC - SANS
# USE: To calculate the RTD around a POINT in the channel -> overillumination!
#
# Assumptions: 
# - Rectangular beam of beam_width x beam_height mm (TO BE SPECIFIED)
# - Chip in use: Dolomite microreactor chip, 250 ul - Part number 3000281
# - Newtonian fluids

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def RTD_taylorDiff(D, width, height, L, Q, t):
    # RTD_taylorDiff  calculates the RTD considering Taylor diffusion, for
    # SQUARE channels
    # D = self-diffusion constant [m2 s-1]
    # width = width of the channel [mm]
    # height = height of the channel [mm]
    # L = total length of the reactor[mm]
    # Q = imposed flow rate [mm3 s-1]
    # t = time vector - should have the same dimension of E(t)
    # f_diff = set to 0 if you want to use Taylor Dstar approximation, to 1 to
    # use Taylor-Aris
    #
    #
    
    D = D*1000000 #mm2s-1
    
    # Plug flow: calculations
    area  = width*height # mm2
    Vavg = Q/area #mm/s
    Tavg = L/Vavg # s
    d_t = 2*width*height/(width+height)

    #theta = t/Tavg
    deltaT = t[1]-t[0]   # Time difference between two elements in a vector
    E = np.zeros (np.size(t), dtype = np.float64)
    
    Dstar = getCorrectAxialDispersion(Vavg, d_t, D, L)
    #if not f_diff:
    #    Dstar = np.power(Vavg,2)*np.power(height,2)/(210*D)  # Taylor
    #else:
    #    Dstar = D + ((Vavg^2)*(height^2))/(210*D) # Taylor-Aris

    const0 = 4*np.pi*Dstar/(Vavg*L)
    const1 = np.power(const0,-0.5)
    #print(np.power(Vavg,2), np.power(height,2), D, Dstar, const0)

    #Calculate the residence time based on t
    for i in range (0,np.size(t)):
        
        if Dstar/(Vavg*L) < 0.01:
            tmp_00 = np.power(Vavg, 3)
            tmp_000 = tmp_00/(4*np.pi*Dstar*L)
            arg_01 = np.power(tmp_00, 0.5)
            
            tmp_01 = L - Vavg*t[i]
            tmp_02 = np.power(tmp_01, 2)
            tmp_03 = tmp_02/(4*Dstar*L/Vavg)
            arg_02 = np.exp(-tmp_03)
            
        else:
            tmp_00 = 4*np.pi*Dstar*t[i]
            tmp_000 = np.power(tmp_00, 0.5)
            arg_01 = Vavg/tmp_000
            
            tmp_01 = L - Vavg*t[i]
            tmp_02 = np.power(tmp_01, 2)
            tmp_03 = tmp_02/(4*Dstar*t[i])
            arg_02 = np.exp(-tmp_03)
        
        #And eventually all together
        E[i] = arg_01 * arg_02   
    
    E = E/(np.sum(E))
    
    if Dstar/(Vavg*L) < 0.01:
        #Plug flow - symmetric RTD
        tmp = np.power(Vavg, 3)
        tmp = 2*Dstar*L/tmp
        tmp *= 2
        std = np.power(tmp, 0.5)
    else:
        #Not so plug flow - Asymmetric RTD
        tmp = Dstar/(Vavg*L)
        tmp = np.power(tmp, 2)
        tmp = tmp * 8
        tmp = tmp+2*Dstar/(Vavg*L)
        
        tmp = tmp * L**2 / Vavg**2
        
        tmp *= 2
        std = np.power(tmp, 0.5)
    
    return [E, std, Vavg, Tavg] 

def getCorrectAxialDispersion(u, d_t, D, L):
    # Check wether general Taylor or Taylor-Aris constant is needed
    #
    # u = fluid speed in mm/s
    # d_t = hydraulic diameter in mm
    # D = diffusion constant in mm2/s
    # L = channel length in mm
    Bo = u*d_t/D #Boltzman constant
    x = L/d_t #To be implemented check
    
    if Bo < 100: #Levenspiel
        #print ("Using Taylor-Aris")
        D_star = D + np.power(u, 2)*np.power(d_t, 2)/(192*D)
    else:
        #print("Using Taylor")
        D_star = np.power(u, 2)*np.power(d_t, 2)/(192*D)
    
    return D_star
    
def mLmin_to_mLh(flowrate):
    #From mL/min to mL/h
    return flowrate*60.

def mLh_to_mm3s(flowrate):
    return flowrate*1000./3600

#Functions
def plotLogLog(x, y):
    plt.plot(x, y, linewidth=1.0)
    plt.yscale('log')
    plt.xscale('log')
    plt.show()
    
def plotLinLin(x, y):
    plt.plot(x, y, linewidth=1.0)
    plt.show()

#====================================== Main Program =================================    
    
#Channel
width = 400 #um channel
height = 250 #um channel
glass = 200 # um glass between two adjacent channels
L_point = 1000
print("Calculating for L = {}".format(L_point))

#Beam
beam_width = 23 #mm 
beam_height = 7 #mm

#Flow
Q = mLmin_to_mLh(0.1) #ml/h
#Diffusion
#D = 2.299*np.power(10.,-9) #m2 s-1 self diff of H2O in H2O at 25 degrees 
D = 0.9*np.power(10.,-9) #m2/s butanol

#Adjustments - Do not modify
width = width/1000 # mm
height = height/1000 #mm
glass = glass/1000 #mm
ChNumber = beam_height/(width+glass)
stepN = np.around(ChNumber, decimals=0)

#Geometrical Information
Lmin = L_point - beam_width*stepN
Lmax = L_point + beam_width*stepN
tmp = np.abs(Lmin-Lmax)/stepN

L =  np.arange(Lmin, Lmax, tmp) #2680 #mm channel length (from 0 to 3000, steo 10)
print("You are illuminating {} mm".format(Lmax-Lmin))

#Rescale
Q = mLh_to_mm3s(Q) # mm3/s

#Create time vector and results empty vector
t = np.arange(0.1, 500, 0.1)    #s (from 0.1 to 500, steps of 0.1)
if t[0] == 0:
    raise NameError('Please do not start time from 0')
E = np.zeros ((np.size(t), np.size(L)))
RTD = np.zeros(np.size(L))
total = np.zeros(np.size(t))

#Single channel RTD
for i in range(0, np.size(L)):
    #print("Cycle = {}".format(i))
    [E[:,i], RTD[i], Vavg, Tavg] = RTD_taylorDiff(D, width, height, L[i], Q, t)

#Total illuminated area RTD
for i in range(0,np.size(t)):
    total[i] = np.sum(E[i,:])
total = total/np.sum(total)

#Plot the results
plt.plot(t, E)
plt.plot(t, total)
plt.show()

#Save the data - standard deviation
header = "time\t"
for i in range(0, np.size(L)):
    header = header + "L_" + str(L[i]) + "\t"

header = header + "Sum_total\t"
filename = "RTD_L_" + str(L_point) + ".dat"
np.savetxt(filename, np.c_[t, E, total], header = header)