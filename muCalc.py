import numpy as np

phi = 200/600   # Area fraction of glass
t = 4.65    # mm of glass
h = 250/1000    # thichness of the channel
T = 0.91    # transmission of the empty


mu = -np.log(T)/t

print("Neutron attenuation coefficient mu = {:.4} mm-1".format(mu))