#Use to calculate the SLD from the D2O percentage


y1 = -0.561     #SLD H2O
y2 = 6.39       #SLD D2O

x1 = 0          #% D2O
x2 = 100        #% D2O

d1 = 1          #density pure H2O
d2 = 1.11       #density pure D2O

x = float(input("Please, insert the percentage of D2O (min 0, max 100) "))

SLD = y1 + (x-x1)*(y2-y1)/(x2-x1)
density = d1 + (x-x1)*(d2-d1)/(x2-x1) #Density of the solvent

print ("Calculated SLD = {} x 10^(-6) A^(-2)".format(SLD))
print ("Corresponding density = {} g/cm3".format(density))