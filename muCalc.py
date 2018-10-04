import numpy as np
#Use the first part for a slab of material 
#Use the second part for a glass device with embedded channels

def calculate_mu(p, x, my_t, my_h, T_meas):
    #p      = area fraction of glass
    #x  = neutron attenuation coefficient
    #my_t   = thickness of the whole device
    #my_h   = thickkess of the channel
    #T_meas = measured transmission of the empty cell
    return p*np.exp(-x*my_t) + (1-p)*np.exp(-x*(my_t-my_h)) - T_meas

print("\n\n#=====================================================================")
print("\t\tNEUTRON ATTENUATION COEFFICIENT")
print("#=====================================================================\n\n")
    
#=====================================================================
#FIRST - SLAB OF A MATERIAL
#=====================================================================
t = 4.65    # thickness t [mm]
T = 0.91    # measured transmission [0 to 1]

mu1 = -np.log(T)/t

print("Solid material of {} mm: mu = {:.4} mm-1".format(t, mu1))

#=====================================================================
#DEVICE OF ONE MATERIAL
#=====================================================================
#Very rudimental but good to have a first approximation
phi = 200/600   # Area fraction of glass
t   = 4.65      # total thickness of glass [mm]
h   = 250/1000  # thichness of the channel [mm]
T   = 0.91      # measured transmission [0 to 1]

mu = np.linspace(0, 1, 10000)
    
for i in mu:
    a = calculate_mu(phi, i, t, h, T)
    if a < 0.001 and a > -0.001:
        print("Material with channels: mu = {:.4} mm-1".format(i))
        break

#Very cool solution with SYMPY, BUT AT THE MOMENT TOO SLOW 
# ToDo - TO BE IMPROVED
#import sympy as sp
#phi = 200/600   # Area fraction of glass
#t = 4.65    # total thickness of glass [mm]
#h = 250/1000    # thichness of the channel [mm]
#T = 0.91    # measured transmission [0 to 1]
#x = sp.Symbol('x', real=True)
#phi, t, h, T = sp.symbols('phi,t,h,T', constant = True)    
#out = sp.solve(phi*sp.exp((-1)*x*t) + (1-phi)*sp.exp((-1)*x*(t-h)) - T, x)
##sp.solve(phi*sp.exp(-x*t) + (1-phi)*sp.exp(-x*(t-h)) - T, x)
#print(out)
