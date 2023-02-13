"""
Created on Wed Sep 21 09:07:07 2022

@author: Jacob TenHarmsel
"""

__version__ = '1.2'  #Updated 1/18/2023
__author__ = 'Jacob TenHarmsel, Liam Tucker'

import serial
import time
import matlab.engine
import numpy as np
import os
import h5py
import csv
import threading

from math import sqrt, ceil
from pywintypes import com_error
import dask
from dask import array
from dask import delayed

#Scan Description - Update for each test
h5_filename = "p_test.h5"

ovr_metadata = {'Date': '2023-01-18',
                'Time': '17:10:00.000',
                'Sample': 'A',
                'Water Temp': 18,
                'Desc': 'Calibration Testing',
                'Operator': 'letucker',
                'Mode': 'FMC'}

"""
READ BEFORE RUNNING SCAN - For current setup, MUST verify that transducers are in line with eachother

"""

# Function to SEND ASCII (serial) command to the specific COM port
def SendAsciiCmd(ser, cmd):
    cmd =cmd +'\r'
    ser.write(cmd.encode())
    return SerReadASCIIResponse(ser)

# Function to get Response for each positioning command from the individual COM port
def SerReadASCIIResponse(ser):
    ret = ''
    while (True):
        ch = ser.read(1)
        if (len(ch) < 1 or ch == '\r'):
            return ret
        ret += str(ch, 'utf-8')

# Function to get the binary response for each positioning command from the individual COM port
def SerReadSerialBinaryResponse(ser):
    ret = []
    while (True):
        ch = ser.read(1)
        if (len(ch) < 1 or ch == '\r'):
            return(ret)
        ch = ch.hex()
        ret.append(ch)

"""
Function for keeping only desired data

"""
def setAcqMode(mode):
    if mode == "FMC": # Shortcut to specify FMC
        sources = []
        receivers = []
        for i in range(32):
            sources.append(i + 1)
            receivers.append(i + 33)
        acq_mode = [sources, receivers]
        return acq_mode
    if mode == "Reflective":
        sources = []
        receivers = []
        for i in range(32):
            sources.append(i + 1)
            receivers.append(i + 1)
        acq_mode = [sources, receivers]
        return acq_mode
    else: # Default is FMC
        sources = []
        receivers = []
        for i in range(32):
            sources.append(i + 1)
            receivers.append(i + 33)
        acq_mode = [sources, receivers]
        return acq_mode

"""
Function for writing RcvData to HDF5 file

"""
def writeToHDF5(this_tuple):
    
    thread_start_time = time.perf_counter()
    # Getting args
    h5_filename = this_tuple[0]
    s_groupname = this_tuple[1]
    r_groupname = this_tuple[2]
    rcvData = this_tuple[3]
    s_index = this_tuple[4]
    r_index = this_tuple[5]
    
    # Converting RcvData to np array
    formatted_data = np.array(rcvData)
    
    # Adding to h5py file
    hf = h5py.File(h5_filename, 'r+')
    this_name = s_groupname + str(s_index) +'/' + r_groupname + str(r_index)
    this_group = hf.create_group(this_name)
    this_group.attrs['SrcPos'] = s_index # To be used in h5file2su script
    this_group.attrs['RecPos'] = r_index # To be used in h5file2su script
    this_group.create_dataset('data', data=formatted_data, compression="gzip", compression_opts=4)
    hf.close()
    
    thread_end_time = time.perf_counter()
    thread_elapsed_time = thread_end_time - thread_start_time
    print(f"Wrote Source Pos {s_index} Receiver Pos {r_index} data to HDF5 file in {thread_elapsed_time:0.2F} seconds.")

"""
Function to create, initial hdf5 file

"""

def createHDF5(filename, attrs):
    hf = h5py.File(filename, 'w')
    hf.attrs.update(attrs) # Setting overall metadata
    hf.close()
    

"""
Function for motor control and data aquisition

"""
        
def motorControl(h5_filename, ovr_metadata):
    
    """General Motor Initilization """
    
    rotary_motor_init = 's r0x24 31' #Rotary motor software position stepper mode
    abs_move = 's r0xc8 256' #Sets position to relative move. trapezoidal profile
    start = 't 1' #Start command
    stop = 't 0' #Stop command
    
    """Large Motor"""
    
    ser_1 = serial.Serial('COM3',9600,timeout=1) #Large Motor - COM based on CME port selection
    
    #20,000 counts for 1 degree movement on large motor
    large_motor_movement = 's r0xca -1800000' #Large Motor Movement - Currently 90 degree rotation
    large_motor_return = 's r0xca 5400000' #Return to original state, currently 270 degrees
    large_max_vel = 's r0xcb 3400000' #Sets maximum velocity for motor - .1 counts/second - 4,000,000 is 20 deg/sec
    large_motor_radius = 38.6 #Radius in mm
    num_source_locations = 4
    
    SendAsciiCmd(ser_1, rotary_motor_init)
    SendAsciiCmd(ser_1, abs_move)
    SendAsciiCmd(ser_1, large_motor_movement)
    SendAsciiCmd(ser_1, large_max_vel)
    
    """Small Motor"""
    
    ser_2 = serial.Serial('COM4',9600,timeout=1) #Small Motor - COM based on CME port selection
    
    #25,000 counts for 1 degree movement on small motor
    small_motor_initial_movement = 's r0xca -1500000' #Small motor moving from initial position to first scan position
    small_motor_movement = 's r0xca 750000' #Small Motor Movement - Currently 30 degree rotation
    small_motor_return = 's r0xca -3000000'#Return to original position, currently 120 degree rotation
    small_motor_final_return = 's r0xca 1500000' #Small motor return to initial position from final scan
    small_max_vel = 's r0xcb 5000000' #Sets maximum velocity for motor - .1 counts/second - 5,000,000 is 20 deg/sec
    small_motor_radius = 38.6 #Radius in mm
    num_receiver_locations = 5 
    
    SendAsciiCmd(ser_2, rotary_motor_init)
    SendAsciiCmd(ser_2, abs_move)
    SendAsciiCmd(ser_2, small_motor_movement)
    SendAsciiCmd(ser_2, small_max_vel)
    
    # For timing purposes
    start_time = time.perf_counter()    
    
    # Specifying which data we are capturing
    acq_params = setAcqMode("FMC")
    f = open('sourceModes.csv', 'w+', newline='')
    with f:
        write = csv.writer(f)
        write.writerow(acq_params[0])       
    f.close()
    f = open('receiverModes.csv', 'w+', newline='')
    with f:
        write = csv.writer(f)
        write.writerow(acq_params[1])
    f.close()
    
    # Setting filenames
    r_groupname = "receiver"
    s_groupname = "transmitter"
    
    # Creating initial HDF5 file
    createHDF5(h5_filename, ovr_metadata)
    
    # Creating list of threads
    thread_list = []
    
    """Motor Movement"""
    
    #Moving from initial position to first scan position
    SendAsciiCmd(ser_2, small_motor_initial_movement)
    SendAsciiCmd(ser_2, start)
    time.sleep(2)
    
    i=0
    while i<num_source_locations:
        
        source_angle = 0
        if i==0:
            print("Beginning DAQ for first source position")
            
        if i!=0:
            print("")
            print("Now Moving To Source Position",i+1)
            source_angle = -i*90 +360
            SendAsciiCmd(ser_1, start)
            time.sleep(4)
                 
  
        j=0        
        while j<num_receiver_locations:

            if j!=0:
                SendAsciiCmd(ser_2, small_motor_movement)
                SendAsciiCmd(ser_2, start)
                time.sleep(2)
                
            fan_beam_angle = 240 - source_angle - j*30
           
            
            eng1.FMC_Imasonics_MA_TM_FullAcquisition_max_copy_test_1108(nargout=0)
            
            time.sleep(1)
            
            while os.path.isfile('Busy.txt') is True:
                time.sleep(1)  
    
            RcvData = eng1.workspace['RcvData']
            arg_tuple = (h5_filename, s_groupname, r_groupname, RcvData, i+1, j+1)
            this_thread = threading.Thread(target=writeToHDF5, args=(arg_tuple,))
            thread_list.append(this_thread)
            this_thread.start()

            print("DAQ complete for receiver position",j+1)    
                
            j+=1

        SendAsciiCmd(ser_2, small_motor_return)
        SendAsciiCmd(ser_2, start)
        i+=1
        
    time.sleep(6)
    SendAsciiCmd(ser_2, small_motor_final_return)
    SendAsciiCmd(ser_2, start)
    SendAsciiCmd(ser_1, large_motor_return)
    SendAsciiCmd(ser_1, start)
    
    # Joining all threads writing to HDF5 file
    for i in range(len(thread_list)):
        thread_list[i].join()
        
    print("Process complete")
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    
    print("")
    print("Ultrasound Imaging Complete")
    print(f"Data Acquisition time is {elapsed_time:0.2F} seconds.")
   
    os.remove('receiverModes.csv')
    os.remove('sourceModes.csv')

    
"""
Running Of Scan

"""

#Activating MATLAB environment
eng1 = matlab.engine.start_matlab()
eng1.activate(nargout=0)
time.sleep(10)

#Motor Control with DAQ calls
motorControl(h5_filename, ovr_metadata)

eng1.quit()
