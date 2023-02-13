# -*- coding: utf-8 -*-
"""
Created on Tue Oct 25 13:24:52 2022


@author: Verasonics
"""

import h5py
import numpy as np

# Printing a list of groups in the file
hfr = h5py.File("p_test.h5", "r")
print(hfr.keys())

# Accessing specific piece of metadata
print(hfr.attrs.get('NSrc'), hfr.attrs.get('NRec'))
print(hfr.attrs.get('NSrcPos'), hfr.attrs.get('NRecPos'))

dt = hfr.get('transmitter1/receiver1/data')
dt = np.array(dt)
print(dt)
print(dt[:,1])
print(dt[0,1])
print("\n\n\n\n")
# Accessing acquisition data from transmitter position 1, receiver position 1
transmitter1 = hfr.get('transmitter1')
print(transmitter1.keys())
receiver1 = transmitter1.get('receiver1')
print(receiver1.keys())
data11 = receiver1.get('data')

# Printing out the shape of data1
data1= np.array(data11)
print(data1)
print(len(data1), len(data1[0]), len(data1[0][0]))

# Accessing group level metadata
for k in transmitter1.attrs.keys(): print(k, transmitter1.attrs[k])
for k in receiver1.attrs.keys(): print(k, receiver1.attrs[k])

# Accessing, and printing out shape of data2
receiver2 = transmitter1.get('receiver2')
print(receiver2.keys())
data12 = receiver2.get('data')
data2 = np.array(data12)
print(data2)
print(len(data2), len(data2[0]), len(data2[0][0]))

# Closing HDF5 file
hfr.close()
# NOTE: If there's an error before closing HDF5 file, it's still considered open by Python
# And the file cannot be deleted until it is closed.