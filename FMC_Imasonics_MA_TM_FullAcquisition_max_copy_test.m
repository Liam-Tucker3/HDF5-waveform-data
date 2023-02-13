addpath('PythonCommunication')
pythonComms = fopen('PythonCommunication\Busy','w');
pythonComms = fclose(pythonComms);
%Let Python Know We're a bit busy!

activate;
FMC_Imasonics_MA_TM_mode_final_version_MA_v2;


load('C:\Users\Administrator\Documents\Vantage-4.1.1-1910211400\Data\FMC_Data_TM_JD\TotalAQ.mat','TotalAQ'); %TotalAQ
position = length(TotalAQ);
TotalAQ{position+1} = RcvData{1,1}; %Save The DATA to a cell in a structure on the workspace
save('C:\Users\Administrator\Documents\Vantage-4.1.1-1910211400\Data\FMC_Data_TM_JD\TotalAQ.mat','TotalAQ');

full_filename = strcat("", "example.h5");
h5 = H5F.create(full_filename);
plist = "H5G_DEFAULT";
base_group = = H5G.create(h5, "acq_data", plist, plist, plist); % Creating outer group
t_group = = H5G.create(base_group, "transmitter1", plist, plist, plist);
r_group = = H5G.create(t_group, "receiver1", plist; plist, plist);
this_filepath = "/acq_data/transmitter1/receiver1/data";
rand_data = int8(randi([-15 15], 32, 32, 4096));
h5create(full_filename, this_filepath, size(rand_data), 'Datatype', 'int8', ...
          'ChunkSize',[16 16 32],'Deflate',4);
h5write(full_filename, this_filepath, rand_data)


clear RcvData
%Let Python know we are done with our acquisition
delete('PythonCommunication\Busy')


