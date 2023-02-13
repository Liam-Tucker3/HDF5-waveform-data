# -*- coding: utf-8 -*-
"""
Created on Tue Oct 25 13:24:52 2022
@author: Verasonics
"""
__version__ = '1.1'  #Updated 2/13/2023
__author__ = 'Liam Tucker'

import h5py
import numpy as np

# Python HDF5 documentation: https://docs.h5py.org/en/stable/index.html
# Matlab HDF5 documentation: https://www.mathworks.com/help/matlab/hdf5-files.html

'''
Reading from Existing HDF5 file
'''
# Opening HDF5 file
hfr = h5py.File("p_test.h5", "r")

# Printing a list of groups in the file
print(hfr.keys())

# Accessing specific piece of metadata
print(hfr.attrs.get('NSrc'), hfr.attrs.get('NRec'))
print(hfr.attrs.get('NSrcPos'), hfr.attrs.get('NRecPos'))

# Accessing acquisition data from transmitter position 1, receiver position 1
transmitter1 = hfr.get('transmitter1')
print(transmitter1.keys())
receiver1 = transmitter1.get('receiver1')
print(receiver1.keys())
data11 = receiver1.get('data')
print(data11)

# Accessing acquisition data from transmitter position 1, receiver position 2
data12 = hfr.get('transmitter1/receiver2/data')
print(data12)

# Printing out the shape of data from transmitter position 1, receiver position 1
np_data11= np.array(data11)
print(np_data11)
print(len(data1), len(data1[0]), len(data1[0][0]))

# Accessing group level metadata
for k in transmitter1.attrs.keys(): print(k, transmitter1.attrs[k])
for k in receiver1.attrs.keys(): print(k, receiver1.attrs[k])

# Closing HDF5 file
hfr.close()
# NOTE: If there's an error before closing HDF5 file, it's still considered open by Python
# And the file cannot be deleted until it is closed.

'''
Writing to HDF5 File
'''

# Creating file
hf = h5py.File(filename, 'w')

# Writing attributes to file
ex_attrs = {'attr1': 1
         'attr2': 'A'
         'attr3': 'Example'
         'attr4': 4.0
         'attr5': [5, 10, 15, 20, 25] }
hf.attrs.update(ex_attrs) # Updating multiple attributes at a time
new_attr = 'ABCDEFG'
hf.attrs['attr6'] = new_attr # Updating one attribute at a time
for k in hf.attrs.keys(): print(k, hf.attrs[k]) # Printing attributes
  
# Creating groups in HDF5 file
t1 = hf.create_group('t1')
r11 = t1.create_group('r1')
r12 = hf.create_group('t1/r2')
r21 = hf.create_group('t2/r1')
print(hf.keys())
print(t1.keys())

# Writing data to hdf5 file
example_data1 = np.array([ [1, 2, 3], [4, 5, 6], [7, 8, 9] ])
example_data2 = np.array([ [10, 20, 30, 40], [50, 60, 70, 80], [90, 100, 110, 120], [130, 140, 150, 160] ])
example_data3 = np.array([ [1, 11, 111], [2, 22, 222], [3, 33, 333] ])

r11.create_dataset('example_data', data = example_data1, compression="gzip", compression_opts=4) # compression_opts in [0, 9] where 9 is max compression
r12.create_dataset('example_data', data = example_data2, chunks = (2, 2)) # Data shored in 2x2 chunks instead of contiguously
r21.create_dataset('example_data', data = example_data3) # No compression, no chunking

data11 = receiver11.get('example_data')
print(data11)

# Closing file
hf.close()
