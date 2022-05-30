#!/usr/bin/env python
# coding: utf-8

yyyymmdd = '2022-03-09'
init = '08'
EXTRACT_DIR = '/home/modelman/forecast/validation/grads/nc'
OUT_DIR = '/home/modelman/forecast/output/validation/20220309/00'

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patch
import datetime as dt 
from netCDF4 import Dataset
#import cartopy.crs as ccrs

# open netCDF files and extract variables

fname = Path(EXTRACT_DIR) / f'./wrf_24hr_rain_day1_{yyyymmdd}_{init}PHT.nc'

d1 = Dataset(fname)
wrf = d1.variables['p24'][:, :]
lats = d1.variables['lat'][:]
lons = d1.variables['lon'][:]

fname = Path(EXTRACT_DIR) / f'./gsmap_24hr_rain_day1_{yyyymmdd}_{init}PHT_re.nc'

d2 = Dataset(fname)
gsmap = d2.variables['rsum'][:, :]
lats = d2.variables['lat'][:]
lons = d2.variables['lon'][:]

# ncdump function

def ncdump(nc_fid, verb=True):
    '''
    ncdump outputs dimensions, variables and their attribute information.
    The information is similar to that of NCAR's ncdump utility.
    ncdump requires a valid instance of Dataset.

    Parameters
    ----------
    nc_fid : netCDF4.Dataset
        A netCDF4 dateset object
    verb : Boolean
        whether or not nc_attrs, nc_dims, and nc_vars are printed

    Returns
    -------
    nc_attrs : list
        A Python list of the NetCDF file global attributes
    nc_dims : list
        A Python list of the NetCDF file dimensions
    nc_vars : list
        A Python list of the NetCDF file variables
    '''
    def print_ncattr(key):
        """
        Prints the NetCDF file attributes for a given key

        Parameters
        ----------
        key : unicode
            a valid netCDF4.Dataset.variables key
        """
        try:
            print ("\t\ttype:", repr(nc_fid.variables[key].dtype))
            for ncattr in nc_fid.variables[key].ncattrs():
                print ('\t\t%s:' % ncattr, repr(nc_fid.variables[key].getncattr(ncattr)))
        except KeyError:
            print ("\t\tWARNING: %s does not contain variable attributes" % key)

    # NetCDF global attributes
    nc_attrs = nc_fid.ncattrs()
    if verb:
        print ("NetCDF Global Attributes:")
        for nc_attr in nc_attrs:
            print ('\t%s:' % nc_attr, repr(nc_fid.getncattr(nc_attr)))
    nc_dims = [dim for dim in nc_fid.dimensions]  # list of nc dimensions
    # Dimension shape information.
    if verb:
        print ("NetCDF dimension information:")
        for dim in nc_dims:
            print ("\tName:", dim )
            print ("\t\tsize:", len(nc_fid.dimensions[dim]))
            print_ncattr(dim)
    # Variable information.
    nc_vars = [var for var in nc_fid.variables]  # list of nc variables
    if verb:
        print ("NetCDF variable information:")
        for var in nc_vars:
            if var not in nc_dims:
                print ('\tName:', var)
                print ("\t\tdimensions:", nc_fid.variables[var].dimensions)
                print ("\t\tsize:", nc_fid.variables[var].size)
                print_ncattr(var)
    return nc_attrs, nc_dims, nc_vars

# Get all netCDF atributes, dimensions, variables:
nc_attrs, nc_dims, nc_vars = ncdump(d1)

#------------------------------------------------#
#            TOTAL RAINFALL CATEGORY             #
#------------------------------------------------#

print("Getting contingency function for total rainfall ...")

def calculate_contingency(fcst,obs):
    contingency = fcst*0
    locs = np.ma.where(np.ma.logical_and((fcst > 0), (obs > 0))) #hit
    if len(locs[0]) > 0: 
        contingency[locs] = 4
    locs = np.ma.where(np.ma.logical_and((fcst > 0), (obs == 0))) #false alarm
    if len(locs[0]) > 0:
        contingency[locs] = 3
    locs = np.ma.where(np.ma.logical_and((fcst == 0), (obs > 0))) #miss
    if len(locs[0]) > 0:
        contingency[locs] = 2
    locs = np.ma.where(np.ma.logical_and((fcst == 0), (obs == 0))) #correct negative
    if len(locs[0]) > 0:
        contingency[locs] = 1
 
    return contingency

CONT=calculate_contingency(wrf[:,:],gsmap[:,:])

# Contingency table functions

hit = np.count_nonzero(CONT == 4)
f_alarm = np.count_nonzero(CONT == 3)
miss = np.count_nonzero(CONT == 2)
c_neg = np.count_nonzero(CONT == 1)

fcst_yes = hit + f_alarm
fcst_no = miss + c_neg
obs_yes = hit + miss
obs_no = f_alarm + c_neg
totalobs = obs_yes+obs_no
totalfcst = fcst_yes+fcst_no

# Forecast metrics 
pod = (hit / (hit + miss)        )*100
far = (f_alarm / (hit + f_alarm) )*100
sr  = (hit / (hit + f_alarm)     )*100

# Format to whole number
pod = '{:0.2f} %'.format(pod)
far = '{:0.2f} %'.format(far)
sr = '{:0.2f} %'.format(sr)

# Prepare contingency table
data =  [
            [          'Yes',        'No',         'Total'       ],
            [ 'Yes'  , int(f'{hit}')    ,  int(f'{f_alarm}') , int(f'{fcst_yes}') ],
            [ 'No'   , int(f'{miss}')   ,  int(f'{c_neg}')   , int(f'{fcst_no}')  ],
            [ 'Total', int(f'{obs_yes}'),  int(f'{obs_no}')  , int(f'{totalobs}') ],
        ]
column_headers = data.pop(0)
row_headers = [x.pop(0) for x in data]
cell_text = []
for row in data:
    cell_text.append([f'{x}' for x in row])
rcolors = plt.cm.BuPu(np.full(len(row_headers), 0.1))
ccolors = plt.cm.BuPu(np.full(len(column_headers), 0.1))

# save contingency table plot as netCDF file
print("Saving contingency table to netCDF file...")
w_nc_fid = Dataset(Path(EXTRACT_DIR) / f'./contingency_{yyyymmdd}_{init}PHT.nc', 'w', format='NETCDF4')
w_nc_fid.description = "Contingency Table calculated from WRF Ensemble and GSMaP"
# Using our previous dimension information, we can create the new dimensions
data = {}
for dim in nc_dims:
    w_nc_fid.createDimension(dim, d1.variables[dim].size)
    data[dim] = w_nc_fid.createVariable(dim, d1.variables[dim].dtype, (dim,))
    # You can do this step yourself but someone else did the work for us.
    for ncattr in d1.variables[dim].ncattrs():
        data[dim].setncattr(ncattr, d1.variables[dim].getncattr(ncattr))
# Assign the dimension data to the new NetCDF file.
#w_nc_fid.variables['time'][:] = time
w_nc_fid.variables['lat'][:] = lats
w_nc_fid.variables['lon'][:] = lons

# Ok, time to create our departure variable
w_nc_var = w_nc_fid.createVariable('cont', 'f8', ('lat', 'lon'))
w_nc_var.setncatts({'long_name': u"Contingency Table (WRF VERSUS GSMaP)",        'units': u"1", 'level_desc': u'Surface',        'var_desc': u"Contingency Table\n"})
w_nc_fid.variables['cont'][:] = CONT
w_nc_fid.close()  # close the new file

print("Done!")

#------------------------------------------------#
#            DRY RAINFALL CATEGORY               #
#------------------------------------------------#

print("Getting contingency function for dry rainfall category...")

def calculate_cont_dry(fcst,obs):
    contingency = fcst*0
    locs = np.ma.where(np.ma.logical_and(np.ma.logical_and((fcst >= 0.1), (fcst < 5)),
                                         np.ma.logical_and((obs >= 0.1),(obs < 5))
                                        )
                                        )#hit
    if len(locs[0]) > 0: 
        contingency[locs] = 4
    locs = np.ma.where(np.ma.logical_and(np.ma.logical_and((fcst >= 0.1), (fcst < 5)),
                                         (obs >= 5)
                                        )
                                        ) #false alarm
    if len(locs[0]) > 0:
        contingency[locs] = 3
    locs = np.ma.where(np.ma.logical_and((fcst >= 5),
                                         np.ma.logical_and((obs >= 0.1),(obs < 5))
                                        )
                                        ) #miss
    if len(locs[0]) > 0:
        contingency[locs] = 2
    locs = np.ma.where(np.ma.logical_and((fcst >= 5), (obs >= 5))) #correct negative
    if len(locs[0]) > 0:
        contingency[locs] = 1
    locs = np.ma.where(np.ma.logical_or((fcst == 0), (obs == 0))) #no rain case
    if len(locs[0]) > 0:
        contingency[locs] = np.nan
 
    return contingency

DRY=calculate_cont_dry(wrf[:,:],gsmap[:,:])

# Contingency table functions

hit = np.count_nonzero(DRY == 4)
f_alarm = np.count_nonzero(DRY == 3)
miss = np.count_nonzero(DRY == 2)
c_neg = np.count_nonzero(DRY == 1)

fcst_yes = hit + f_alarm
fcst_no = miss + c_neg
obs_yes = hit + miss
obs_no = f_alarm + c_neg
totalobs = obs_yes+obs_no
totalfcst = fcst_yes+fcst_no
# Forecast metrics 
pod1 = (hit / (hit + miss)        )*100
far1 = (f_alarm / (hit + f_alarm) )*100
sr1  = (hit / (hit + f_alarm)     )*100

# format to whole number
pod1 = '{:0.2f} %'.format(pod1)
far1 = '{:0.2f} %'.format(far1)
sr1 = '{:0.2f} %'.format(sr1)

# Prepare contingency table
data1 =  [
            [          'Yes',        'No',         'Total'       ],
            [ 'Yes'  , int(f'{hit}')    ,  int(f'{f_alarm}') , int(f'{fcst_yes}') ],
            [ 'No'   , int(f'{miss}')   ,  int(f'{c_neg}')   , int(f'{fcst_no}')  ],
            [ 'Total', int(f'{obs_yes}'),  int(f'{obs_no}')  , int(f'{totalobs}') ],
        ]
column_headers1 = data1.pop(0)
row_headers1 = [x.pop(0) for x in data1]
cell_text1 = []
for row in data1:
    cell_text1.append([f'{x}' for x in row])
rcolors1 = plt.cm.BuPu(np.full(len(row_headers1), 0.1))
ccolors1 = plt.cm.BuPu(np.full(len(column_headers1), 0.1))

#------------------------------------------------#
#            LOW RAINFALL CATEGORY               #
#------------------------------------------------#

print("Getting contingency function for low rainfall category...")

def calculate_cont_low(fcst,obs):
    contingency = fcst*0
    locs = np.ma.where(np.ma.logical_and(np.ma.logical_and((fcst >= 5), (fcst < 20)),
                                        (obs >= 5),(obs < 20)
                                        )
                                        ) #hit
    if len(locs[0]) > 0: 
        contingency[locs] = 4
    locs = np.ma.where(np.ma.logical_and(np.ma.logical_and((fcst >= 5), (fcst < 20)),
                                        np.ma.logical_or((obs >= 20),
                                        np.ma.logical_and((obs >=0.1),(obs < 5)))
                                        )
                                        ) #false alarm
    if len(locs[0]) > 0:
        contingency[locs] = 3
    locs = np.ma.where(np.ma.logical_and(np.ma.logical_or((fcst >= 20),
                                        np.ma.logical_and((fcst >=0.1),(fcst < 5))),
                                        np.ma.logical_and((obs >= 5), (obs < 20))
                                        )
                                        ) #miss
    if len(locs[0]) > 0:
        contingency[locs] = 2
    locs = np.ma.where(np.ma.logical_and(np.ma.logical_or((fcst >= 20),
                                        np.ma.logical_and((fcst >=0.1),(fcst < 5))),
                                        np.ma.logical_or((obs >= 20),
                                        np.ma.logical_and((obs >=0.1),(obs < 5)))
                                        )
                                        ) #correct negative
    if len(locs[0]) > 0:
        contingency[locs] = 1
    locs = np.ma.where(np.ma.logical_or((fcst == 0), (obs == 0))) #no rain case
    if len(locs[0]) > 0:
        contingency[locs] = np.nan
 
    return contingency

LOW=calculate_cont_low(wrf[:,:],gsmap[:,:])

# Contingency table functions

hit = np.count_nonzero(LOW == 4)
f_alarm = np.count_nonzero(LOW == 3)
miss = np.count_nonzero(LOW == 2)
c_neg = np.count_nonzero(LOW == 1)

fcst_yes = hit + f_alarm
fcst_no = miss + c_neg
obs_yes = hit + miss
obs_no = f_alarm + c_neg
totalobs = obs_yes+obs_no
totalfcst = fcst_yes+fcst_no
# Forecast metrics 
pod2 = (hit / (hit + miss)        )*100
far2 = (f_alarm / (hit + f_alarm) )*100
sr2  = (hit / (hit + f_alarm)     )*100

# format to whole number
pod2 = '{:0.2f} %'.format(pod2)
far2 = '{:0.2f} %'.format(far2)
sr2 = '{:0.2f} %'.format(sr2)

# Prepare contingency table
data2 =  [
            [          'Yes',        'No',         'Total'       ],
            [ 'Yes'  , int(f'{hit}')    ,  int(f'{f_alarm}') , int(f'{fcst_yes}') ],
            [ 'No'   , int(f'{miss}')   ,  int(f'{c_neg}')   , int(f'{fcst_no}')  ],
            [ 'Total', int(f'{obs_yes}'),  int(f'{obs_no}')  , int(f'{totalobs}') ],
        ]
column_headers2 = data2.pop(0)
row_headers2 = [x.pop(0) for x in data2]
cell_text2 = []
for row in data2:
    cell_text2.append([f'{x}' for x in row])
rcolors2 = plt.cm.BuPu(np.full(len(row_headers2), 0.1))
ccolors2 = plt.cm.BuPu(np.full(len(column_headers2), 0.1))

#------------------------------------------------#
#         MODERATE RAINFALL CATEGORY             #
#------------------------------------------------#

print("Getting contingency function for moderate rainfall category...")

def calculate_cont_moderate(fcst,obs):
    contingency = fcst*0
    locs = np.ma.where(np.ma.logical_and(np.ma.logical_and((fcst >= 20), (fcst < 35)),
                                        (obs >= 20),(obs < 35)
                                        )
                                        ) #hit
    if len(locs[0]) > 0: 
        contingency[locs] = 4
    locs = np.ma.where(np.ma.logical_and(np.ma.logical_and((fcst >= 20), (fcst < 35)),
                                        np.ma.logical_or((obs >= 35),
                                        np.ma.logical_and((obs >=0.1),(obs < 20)))
                                        )
                                        ) #false alarm
    if len(locs[0]) > 0:
        contingency[locs] = 3
    locs = np.ma.where(np.ma.logical_and(np.ma.logical_or((fcst >= 35),
                                        np.ma.logical_and((fcst >=0.1),(fcst < 20))),
                                        np.ma.logical_and((obs >= 20), (obs < 35))
                                        )
                                        ) #miss
    if len(locs[0]) > 0:
        contingency[locs] = 2
    locs = np.ma.where(np.ma.logical_and(np.ma.logical_or((fcst >= 35),
                                        np.ma.logical_and((fcst >=0.1),(fcst < 20))),
                                        np.ma.logical_or((obs >= 35),
                                        np.ma.logical_and((obs >=0.1),(obs < 20)))
                                        )
                                        ) #correct negative
    if len(locs[0]) > 0:
        contingency[locs] = 1
    locs = np.ma.where(np.ma.logical_or((fcst == 0), (obs == 0))) #no rain case
    if len(locs[0]) > 0:
        contingency[locs] = np.nan
 
    return contingency

MOD=calculate_cont_moderate(wrf[:,:],gsmap[:,:])

# Contingency table functions

hit = np.count_nonzero(MOD == 4)
f_alarm = np.count_nonzero(MOD == 3)
miss = np.count_nonzero(MOD == 2)
c_neg = np.count_nonzero(MOD == 1)

fcst_yes = hit + f_alarm
fcst_no = miss + c_neg
obs_yes = hit + miss
obs_no = f_alarm + c_neg
totalobs = obs_yes+obs_no
totalfcst = fcst_yes+fcst_no
# Forecast metrics 
pod3 = (hit / (hit + miss)        )*100
far3 = (f_alarm / (hit + f_alarm) )*100
sr3  = (hit / (hit + f_alarm)     )*100

# format to whole number
pod3 = '{:0.2f} %'.format(pod3)
far3 = '{:0.2f} %'.format(far3)
sr3 = '{:0.2f} %'.format(sr3)

# Prepare contingency table
data3 =  [
            [          'Yes',        'No',         'Total'       ],
            [ 'Yes'  , int(f'{hit}')    ,  int(f'{f_alarm}') , int(f'{fcst_yes}') ],
            [ 'No'   , int(f'{miss}')   ,  int(f'{c_neg}')   , int(f'{fcst_no}')  ],
            [ 'Total', int(f'{obs_yes}'),  int(f'{obs_no}')  , int(f'{totalobs}') ],
        ]
column_headers3 = data3.pop(0)
row_headers3 = [x.pop(0) for x in data3]
cell_text3 = []
for row in data3:
    cell_text3.append([f'{x}' for x in row])
rcolors3 = plt.cm.BuPu(np.full(len(row_headers3), 0.1))
ccolors3 = plt.cm.BuPu(np.full(len(column_headers3), 0.1))

#------------------------------------------------#
#            HEAVY RAINFALL CATEGORY             #
#------------------------------------------------#

print("Getting contingency function for heavy rainfall category...")

def calculate_cont_heavy(fcst,obs):
    contingency = fcst*0
    locs = np.ma.where(np.ma.logical_and(np.ma.logical_and((fcst >= 35), (fcst < 50)),
                                        (obs >= 35),(obs < 50)
                                        )
                                        ) #hit
    if len(locs[0]) > 0: 
        contingency[locs] = 4
    locs = np.ma.where(np.ma.logical_and(np.ma.logical_and((fcst >= 35), (fcst < 50)),
                                        np.ma.logical_or((obs >= 50),
                                        np.ma.logical_and((obs >=0.1),(obs < 35)))
                                        )
                                        ) #false alarm
    if len(locs[0]) > 0:
        contingency[locs] = 3
    locs = np.ma.where(np.ma.logical_and(np.ma.logical_or((fcst >= 50),
                                        np.ma.logical_and((fcst >=0.1),(fcst < 35))),
                                        np.ma.logical_and((obs >= 35), (obs < 50))
                                        )
                                        ) #miss
    if len(locs[0]) > 0:
        contingency[locs] = 2
    locs = np.ma.where(np.ma.logical_and(np.ma.logical_or((fcst >= 50),
                                        np.ma.logical_and((fcst >=0.1),(fcst < 35))),
                                        np.ma.logical_or((obs >= 50),
                                        np.ma.logical_and((obs >=0.1),(obs < 35)))
                                        )
                                        ) #correct negative
    if len(locs[0]) > 0:
        contingency[locs] = 1
    locs = np.ma.where(np.ma.logical_or((fcst == 0), (obs == 0))) #no rain case
    if len(locs[0]) > 0:
        contingency[locs] = np.nan
 
    return contingency

HEAVY=calculate_cont_heavy(wrf[:,:],gsmap[:,:])

# Contingency table functions

hit = np.count_nonzero(HEAVY == 4)
f_alarm = np.count_nonzero(HEAVY == 3)
miss = np.count_nonzero(HEAVY == 2)
c_neg = np.count_nonzero(HEAVY == 1)

fcst_yes = hit + f_alarm
fcst_no = miss + c_neg
obs_yes = hit + miss
obs_no = f_alarm + c_neg
totalobs = obs_yes+obs_no
totalfcst = fcst_yes+fcst_no
# Forecast metrics 
pod4 = (hit / (hit + miss)        )*100
far4 = (f_alarm / (hit + f_alarm) )*100
sr4  = (hit / (hit + f_alarm)     )*100

# format to whole number
pod4 = '{:0.2f} %'.format(pod4)
far4 = '{:0.2f} %'.format(far4)
sr4 = '{:0.2f} %'.format(sr4)

# Prepare contingency table
data4 =  [
            [          'Yes',        'No',         'Total'       ],
            [ 'Yes'  , int(f'{hit}')    ,  int(f'{f_alarm}') , int(f'{fcst_yes}') ],
            [ 'No'   , int(f'{miss}')   ,  int(f'{c_neg}')   , int(f'{fcst_no}')  ],
            [ 'Total', int(f'{obs_yes}'),  int(f'{obs_no}')  , int(f'{totalobs}') ],
        ]
column_headers4 = data4.pop(0)
row_headers4 = [x.pop(0) for x in data4]
cell_text4 = []
for row in data4:
    cell_text4.append([f'{x}' for x in row])
rcolors4 = plt.cm.BuPu(np.full(len(row_headers4), 0.1))
ccolors4 = plt.cm.BuPu(np.full(len(column_headers4), 0.1))

#------------------------------------------------#
#          EXTREME RAINFALL CATEGORY             #
#------------------------------------------------#

print("Getting contingency function for extreme rainfall category...")

def calculate_cont_extreme(fcst,obs):
    contingency = fcst*0
    locs = np.ma.where(np.ma.logical_and((fcst >= 50),
                                        (obs >= 50)
                                        )
                                        ) #hit
    if len(locs[0]) > 0: 
        contingency[locs] = 4
    locs = np.ma.where(np.ma.logical_and((fcst >= 50),
                                        np.ma.logical_and((obs >=0.1),(obs < 50))
                                        )
                                        ) #false alarm
    if len(locs[0]) > 0:
        contingency[locs] = 3
    locs = np.ma.where(np.ma.logical_and(np.ma.logical_and((fcst >=0.1),(fcst < 50)),
                                        (obs >= 50)
                                        )
                                        ) #miss
    if len(locs[0]) > 0:
        contingency[locs] = 2
    locs = np.ma.where(np.ma.logical_and(np.ma.logical_and((fcst >=0.1),(fcst < 50)),
                                        np.ma.logical_and((obs >=0.1),(obs < 50))
                                        )
                                        ) #correct negative
    if len(locs[0]) > 0:
        contingency[locs] = 1
    locs = np.ma.where(np.ma.logical_or((fcst == 0), (obs == 0))) #no rain case
    if len(locs[0]) > 0:
        contingency[locs] = np.nan
 
    return contingency

EXT=calculate_cont_extreme(wrf[:,:],gsmap[:,:])

# Contingency table functions

hit = np.count_nonzero(EXT == 4)
f_alarm = np.count_nonzero(EXT == 3)
miss = np.count_nonzero(EXT == 2)
c_neg = np.count_nonzero(EXT == 1)

fcst_yes = hit + f_alarm
fcst_no = miss + c_neg
obs_yes = hit + miss
obs_no = f_alarm + c_neg
totalobs = obs_yes+obs_no
totalfcst = fcst_yes+fcst_no

# Forecast metrics 
pod5 = (hit / (hit + miss)        )*100
far5 = (f_alarm / (hit + f_alarm) )*100
sr5  = (hit / (hit + f_alarm)     )*100

# format to whole number
pod5 = '{:0.2f} %'.format(pod5)
far5 = '{:0.2f} %'.format(far5)
sr5 = '{:0.2f} %'.format(sr5)

# Prepare contingency table
data5 =  [
            [          'Yes',        'No',         'Total'       ],
            [ 'Yes'  , int(f'{hit}')    ,  int(f'{f_alarm}') , int(f'{fcst_yes}') ],
            [ 'No'   , int(f'{miss}')   ,  int(f'{c_neg}')   , int(f'{fcst_no}')  ],
            [ 'Total', int(f'{obs_yes}'),  int(f'{obs_no}')  , int(f'{totalobs}') ],
        ]
column_headers5 = data5.pop(0)
row_headers5 = [x.pop(0) for x in data5]
cell_text5 = []
for row in data5:
    cell_text5.append([f'{x}' for x in row])
rcolors5 = plt.cm.BuPu(np.full(len(row_headers5), 0.1))
ccolors5 = plt.cm.BuPu(np.full(len(column_headers5), 0.1))

# plotting variable settings
x_range=pd.date_range(f'{yyyymmdd}-{init}',periods=25, freq='H').strftime('%Y-%m-%d %H:00')
fig_background_color = 'white'
fig_border = 'black'
obs_title = 'Observation (GSMaP)'
fcst_title = 'Forecast (WRF)'

title_text = f'Contingency Table (24-hr Total Rainfall)\nfrom {yyyymmdd} {init}:00 to {x_range[24]} PHT'
footer_text = f'Probability of Detection = {pod}\nFalse Alarm Ratio = {far}\nSuccess Ratio = {sr}'

title_text1 = f'Contingency Table (24-hr Dry Rainfall)\nfrom {yyyymmdd} {init}:00 to {x_range[24]} PHT'
footer_text1 = f'Probability of Detection = {pod1}\nFalse Alarm Ratio = {far1}\nSuccess Ratio = {sr1}'

title_text2 = f'Contingency Table (24-hr Low Rainfall)\nfrom {yyyymmdd} {init}:00 to {x_range[24]} PHT'
footer_text2 = f'Probability of Detection = {pod2}\nFalse Alarm Ratio = {far2}\nSuccess Ratio = {sr2}'

title_text3 = f'Contingency Table (24-hr Moderate Rainfall)\nfrom {yyyymmdd} {init}:00 to {x_range[24]} PHT'
footer_text3 = f'Probability of Detection = {pod3}\nFalse Alarm Ratio = {far3}\nSuccess Ratio = {sr3}'

title_text4 = f'Contingency Table (24-hr Heavy Rainfall)\nfrom {yyyymmdd} {init}:00 to {x_range[24]} PHT'
footer_text4 = f'Probability of Detection = {pod4}\nFalse Alarm Ratio = {far4}\nSuccess Ratio = {sr4}'

title_text5 = f'Contingency Table (24-hr Extreme Rainfall)\nfrom {yyyymmdd} {init}:00 to {x_range[24]} PHT'
footer_text5 = f'Probability of Detection = {pod5}\nFalse Alarm Ratio = {far5}\nSuccess Ratio = {sr5}'

print("Plotting contingency tables...")

# figure plot settings

plt.figure(linewidth=2,
           edgecolor='black',
           facecolor='white',
#           tight_layout={'pad':1},
           dpi=300)
plt.rcParams["figure.figsize"] = (20,6)
fig, ((ax1,ax2,ax3),(ax4,ax5,ax6)) = plt.subplots(ncols=3,nrows=2)

ax1.get_xaxis().set_visible(False)
ax1.get_yaxis().set_visible(False)
ax1.set_frame_on(False)
ax1.table(cellText=cell_text1,
                      rowLabels=row_headers1,
                      rowColours=rcolors1,
                      rowLoc='center',
                      colColours=ccolors1,
                      colLabels=column_headers1,
                      loc='upper center')
ax1.set_title(title_text1+'\n')
# Add footer
ax1.text(0.5, 0.35, footer_text1, horizontalalignment='center', size=12, weight='normal')
ax1.text(0.35, 1., obs_title, horizontalalignment='center',size=10, weight='normal')
ax1.text(-0.11, 0.65, fcst_title, horizontalalignment='center',size=10, weight='normal',rotation='vertical')

ax2.get_xaxis().set_visible(False)
ax2.get_yaxis().set_visible(False)
ax2.set_frame_on(False)
ax2.table(cellText=cell_text2,
                      rowLabels=row_headers2,
                      rowColours=rcolors2,
                      rowLoc='center',
                      colColours=ccolors2,
                      colLabels=column_headers2,
                      loc='upper center')
ax2.set_title(title_text2+'\n')
# Add footer
ax2.text(0.5, 0.35, footer_text2, horizontalalignment='center', size=12, weight='normal')
ax2.text(0.35, 1.,obs_title, horizontalalignment='center',size=10, weight='normal')
ax2.text(-0.11, 0.65, fcst_title, horizontalalignment='center',size=10, weight='normal',rotation='vertical')

ax3.get_xaxis().set_visible(False)
ax3.get_yaxis().set_visible(False)
ax3.set_frame_on(False)
ax3.table(cellText=cell_text3,
                      rowLabels=row_headers3,
                      rowColours=rcolors3,
                      rowLoc='center',
                      colColours=ccolors3,
                      colLabels=column_headers3,
                      loc='upper center')
ax3.set_title(title_text3+'\n')
# Add footer
ax3.text(0.5, 0.35, footer_text3, horizontalalignment='center', size=12, weight='normal')
ax3.text(0.35, 1., obs_title, horizontalalignment='center',size=10, weight='normal')
ax3.text(-0.11, 0.65, fcst_title, horizontalalignment='center',size=10, weight='normal',rotation='vertical')

ax4.get_xaxis().set_visible(False)
ax4.get_yaxis().set_visible(False)
ax4.set_frame_on(False)
ax4.table(cellText=cell_text4,
                      rowLabels=row_headers4,
                      rowColours=rcolors4,
                      rowLoc='center',
                      colColours=ccolors4,
                      colLabels=column_headers4,
                      loc='upper center')
ax4.set_title(title_text4+'\n')
# Add footer
ax4.text(0.5, 0.35, footer_text4, horizontalalignment='center', size=12, weight='normal')
ax4.text(0.35, 1., obs_title, horizontalalignment='center',size=10, weight='normal')
ax4.text(-0.11, 0.65, fcst_title, horizontalalignment='center',size=10, weight='normal',rotation='vertical')

ax5.get_xaxis().set_visible(False)
ax5.get_yaxis().set_visible(False)
ax5.set_frame_on(False)
ax5.table(cellText=cell_text5,
                      rowLabels=row_headers5,
                      rowColours=rcolors5,
                      rowLoc='center',
                      colColours=ccolors5,
                      colLabels=column_headers5,
                      loc='upper center')
ax5.set_title(title_text5+'\n')
# Add footer
ax5.text(0.5, 0.35, footer_text5, horizontalalignment='center', size=12, weight='normal')
ax5.text(0.35, 1., obs_title, horizontalalignment='center',size=10, weight='normal')
ax5.text(-0.11, 0.65, fcst_title, horizontalalignment='center',size=10, weight='normal',rotation='vertical')

ax6.get_xaxis().set_visible(False)
ax6.get_yaxis().set_visible(False)
ax6.set_frame_on(False)
ax6.table(cellText=cell_text,
                      rowLabels=row_headers,
                      rowColours=rcolors,
                      rowLoc='center',
                      colColours=ccolors,
                      colLabels=column_headers,
                      loc='upper center')
ax6.set_title(title_text+'\n')
# Add footer
ax6.text(0.5, 0.35, footer_text, horizontalalignment='center', size=12, weight='normal')
ax6.text(0.35, 1., obs_title, horizontalalignment='center',size=10, weight='normal')
ax6.text(-0.11, 0.65, fcst_title, horizontalalignment='center',size=10, weight='normal',rotation='vertical')

# Contingency table legend
ax5.text(0.5, 0.2, 'Guide for contingency table',horizontalalignment='center',size=10, weight='normal')
ax5.text(0.4, 0.1, 'Observation',horizontalalignment='center',size=8, weight='normal')
ax5.text(0.06, -0.18, 'Forecast',horizontalalignment='center',size=8, weight='normal',rotation='vertical')

ax5.text(0.1, -0.05, 'Yes',horizontalalignment='center',size=8, weight='normal')
ax5.text(0.1, -0.15, 'No',horizontalalignment='center',size=8, weight='normal')
ax5.text(0.1, -0.25, 'Total',horizontalalignment='center',size=8, weight='normal')

ax5.text(0.25, 0.05, 'Yes',horizontalalignment='center',size=8, weight='normal')
ax5.text(0.51, 0.05, 'No',horizontalalignment='center',size=8, weight='normal')
ax5.text(0.78, 0.05, 'Total',horizontalalignment='center',size=8, weight='normal')

ax5.text(0.25, -0.05, 'HIT',horizontalalignment='center',size=8, weight='heavy')
ax5.text(0.51, -0.05, 'FALSE ALARM',horizontalalignment='center',size=8, weight='heavy')
ax5.text(0.78, -0.05, 'FORECAST YES',horizontalalignment='center',size=8, weight='heavy')
ax5.text(0.25, -0.15, 'MISS',horizontalalignment='center',size=8, weight='heavy')
ax5.text(0.51, -0.15, 'CORRECT NEGATIVE',horizontalalignment='center',size=8, weight='heavy')
ax5.text(0.78, -0.15, 'FORECAST NO',horizontalalignment='center',size=8, weight='heavy')
ax5.text(0.25, -0.25, 'OBSERVED YES',horizontalalignment='center',size=8, weight='heavy')
ax5.text(0.51, -0.25, 'OBSERVED NO',horizontalalignment='center',size=8, weight='heavy')
ax5.text(0.78, -0.25, 'TOTAL GRIDPTS',horizontalalignment='center',size=8, weight='heavy')
#ax5.add_patch(patch.Rectangle((0,0), 3, 3, edgecolor='black', facecolor='none',zorder=300))

out_file = Path(OUT_DIR) / f'contingency_{yyyymmdd}_{init}PHT.png'
out_file.parent.mkdir(parents=True,exist_ok=True)
plt.savefig(str(out_file), dpi=300,bbox_inches='tight')
print("Done!")
