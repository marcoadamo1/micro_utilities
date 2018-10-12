import numpy as np

#______________________@__element_B
#_____________________@@@______
#____________________@___@_____
#___________________@@@_@@@____
#__________________@_______@___
#_________________@@@_____@@@__
#________________@___@___@___@_
#____element_A__@@@_@@@_@@@_@@@   element_C


# MODIFY FROM HERE
element_A = "D2O" #Element 1 (D2O)
element_B = "baxxodur" #Element 2 (baxxodur)
element_C = "active" #Element 3 (active)
#Concentrations in each syringe
#           [El1,   El2,    El3]
pump_1 = [100,   0,      0] # element_A - D2O
pump_2 = [1,    99,      0] # element_B - baxxodur
pump_3 = [88,    0,     12] # element_C - active
#Ranges
initial_A = 5.  #[0:100]
final_A = 95.  #[0:100]
initial_C = 95. #[0:100]
final_C = 5   #[0:100]
#Steps
step_A = 5
step_C = 3
#Flowrate (not mandatory)
flow = 6 # mlh
# MODIFY TO HERE


#==================================================================================================
#==================================================================================================
#==================================================================================================
#==================================================================================================
temp = [0,0,0]

def ternary_thread(initial_A, final_A, initial_C, final_C, step_A, step_C):
    total = 1 #to have in %
    rows = step_A*step_C
    res = np.zeros((rows, 3), dtype = float)
    if initial_C < final_C:
        print("ERROR!!! Plase make sure that initial_C is bigger than final_C")
        return res
        
    #Save locally the parameters - no jokes from geeks
    my_initial_A = initial_A/100.0
    my_final_A = final_A/100.0
    my_initial_C = initial_C/100.0
    my_final_C = final_C/100.0
    my_total = total
    act_flowC = my_initial_C * my_total
    act_flowA = my_initial_A * (my_total - act_flowC) 
    act_flowB = (my_total - act_flowA - act_flowC)
    if (act_flowA+act_flowB+act_flowC) != my_total :
        print ("CALCULATION ERROR")
        raise
    #Initialise the direction of the ramps
    goUP = True 
    flowDelta_AB = 0
    flowDelta_C = abs(my_total*(my_final_C-my_initial_C))/(step_C-1)    #Fixed
    
    print("Pump 1 at " + str(act_flowA) + ", Pump 2 at " + str(act_flowB) + ", Pump 3 at " + str(act_flowC))
    temp[0] = act_flowA
    temp[1] = act_flowB
    temp[2] = act_flowC
    
    my_time = 0
    
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
        
        #print("Calculated flow A" + str(act_flowA))
        #print("Calculated flow B" + str(act_flowB))
        
        flowDelta_AB = abs((my_total-act_flowC)*(my_final_A-my_initial_A))/(step_A+1)
        #print("Delta AB = " + str(flowDelta_AB))

        for _AB in range(0, step_A):
            #print ("____AB____ iteration" + str(_AB))            
            #print("Step ramp: " + str(_AB))
            if (goUP == True):
                act_flowA = act_flowA + flowDelta_AB
                act_flowB = my_total-act_flowC-act_flowA
            else:
                act_flowA = act_flowA - flowDelta_AB
                act_flowB = my_total-act_flowC-act_flowA
            
            print("{:.2f}\t{:.2f}\t{:.2f}\t".format(act_flowA*100, act_flowB*100, act_flowC*100))
            #res[_C*step_A+_AB,0]
            tmp = _C*step_A+_AB
            res[tmp,0] = act_flowA*100
            res[tmp,1] = act_flowB*100
            res[tmp,2] = act_flowC*100
            

        my_time = 0
        #Update C flow
        act_flowC-=flowDelta_C
        act_flowA = (my_total-flowDelta_C)
        #if (_C != (step_C-1)):
        #    #self.serialCMD(pump3, self.commands['Rate'], act_flowC)
        #    print("Pump 3 at " + str(act_flowC))
        #else:
        #    print("Pump 3 not set, last iteration!")
        #    print("Pump 3 at " + str(act_flowC))
        goUP = not(goUP)
            
        
    #FINAL STABILISATION
    act_flowC = my_final_C * my_total 
    act_flowA = my_final_A * (my_total - act_flowC)
    act_flowB = (my_total - act_flowA - act_flowC)
    print("Pump 1 at " + str(act_flowA) + ", Pump 2 at " + str(act_flowB) + ", Pump 3 at " + str(act_flowC))
        
    return res

volumes = ternary_thread(initial_A, final_A, initial_C, final_C, step_A, step_C)
concentrations = np.zeros (volumes.shape)
flowrates = np.zeros (volumes.shape)
flowrates = flow*volumes/100


for i in range (0, len(concentrations)):
    concentrations[i,0] = volumes[i,0]*pump_1[0]/100+volumes[i,1]*pump_2[0]/100+volumes[i,2]*pump_3[0]/100
    concentrations[i,1] = volumes[i,0]*pump_1[1]/100+volumes[i,1]*pump_2[1]/100+volumes[i,2]*pump_3[1]/100
    concentrations[i,2] = volumes[i,0]*pump_1[2]/100+volumes[i,1]*pump_2[2]/100+volumes[i,2]*pump_3[2]/100
    print(concentrations[i,])

HEADER = "{}\t{}\t{}\n{}\t{}\t{}\n".format(element_A, element_B, element_C, temp[0]*flow,temp[1]*flow,temp[2]*flow)
np.savetxt("concentrations.dat", concentrations, fmt='%.4f', delimiter='\t', newline='\n', header=HEADER, footer='', comments='')
np.savetxt("volumes.dat", volumes, fmt='%.4f', delimiter='\t', newline='\n', header=HEADER, footer='', comments='')
np.savetxt("flowrates_mlmin.dat", flowrates, fmt='%.4f', delimiter='\t', newline='\n', header=HEADER, footer='', comments='')

