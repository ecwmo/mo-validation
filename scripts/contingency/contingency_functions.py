# Title: Functions for contigency tables
# Author: Kevin Henson
# Last edited: May 12, 2022

import numpy as np

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

def calc_cont_total(fcst,obs):
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

def calc_cont_dry(fcst,obs):
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

def calc_cont_low(fcst,obs):
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

def calc_cont_mod(fcst,obs):
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

def calc_cont_heavy(fcst,obs):
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

def calc_cont_ext(fcst,obs):
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