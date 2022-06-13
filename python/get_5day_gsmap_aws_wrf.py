# Description: get 5 day wrf, aws, ang gsmap data
# Author: Kevin Henson
# Last edited: June 17, 2022

import pandas as pd
import numpy as np
import xarray as xr
from datetime import timedelta
from os import path

def get_5day_gsmap_aws_wrf(dt,stn):

    wrf_dir = '/home/modelman/forecast/output/stations_fcst_for_validation/json/'
    gsmap_dir = "/home/modelman/forecast/validation/gsmap/nc/"
    aws_dir = "/home/modelman/forecast/input/aws_files/"

    # Intialize dataframe for each station
    df_gsmap = pd.DataFrame(columns=['time','precip',])
    aws_cols = ['name', 'timestamp', 'rr','temp','rh','hi']
    df_aws = pd.DataFrame(columns = aws_cols)

    # Loop through past 5 days
    for day in reversed(np.arange(1, 6)):

        # Set date variable
        dt_var = dt - timedelta(int(day))

        # Access gsmap file and data
        gsmap_fn = gsmap_dir + "gsmap_gauge_" + str(dt_var) + "_00_ph.nc"
        if path.exists(gsmap_fn):
            gsmap_df = xr.open_dataset(gsmap_fn)
            df_temp_gsmap = gsmap_df.sel(lon=stn['lon'], lat=stn['lat'], method="nearest").to_dataframe()
            df_temp_gsmap = df_temp_gsmap['precip'].reset_index(level='time')
        
        aws_fn = aws_dir + 'stn_obs_24hr_' + str(dt_var) +'_08PHT.csv'
        if path.exists(aws_fn):
            aws_df = pd.read_csv(aws_fn,
                                usecols=aws_cols, na_values="-999.000000")
            aws_df = aws_df[aws_df['name'] == stn['name']]
        
        # Append daily data
        if path.exists(gsmap_fn):
            df_gsmap = pd.concat([df_gsmap,df_temp_gsmap])
        if path.exists(aws_fn):
            df_aws = pd.concat([df_aws,aws_df])

    df_gsmap = df_gsmap.reset_index(drop=True)
    df_aws = df_aws.reset_index(drop=True)

    # Fill-in missing timesteps
    df_aws['timestamp'] = pd.to_datetime(df_aws['timestamp'])
    df_gsmap['time'] = pd.to_datetime(df_gsmap['time'])
    dt_var = dt - timedelta(5)
    dt_var_str = str(dt_var)
    date_str = str(dt)
    start = pd.to_datetime(dt_var_str + ' 09:00:00+08:00')
    end = pd.to_datetime(date_str + ' 08:00:00+08:00')
    dates = pd.date_range(start=start, end=end, freq='1H')

    df_aws = df_aws.set_index('timestamp').reindex(dates).reset_index().reindex(columns=df_aws.columns)
    cols = df_aws.columns.difference(['rr','temp','rh','hi'])
    df_aws[cols] = df_aws[cols].ffill()
    df_aws['timestamp'] = dates

    df_gsmap= df_gsmap.set_index('time').reindex(dates).reset_index().reindex(columns=df_gsmap.columns)
    cols = df_gsmap.columns.difference(['precip'])
    df_gsmap[cols] = df_gsmap[cols].ffill()
    df_gsmap['time'] = dates

    print(df_aws)
    print(df_gsmap)

    # # Append 5-day station data
    # df_all_stns_gsmap = pd.concat([df_all_stns_gsmap, df_gsmap]).reset_index(drop=True)
    # df_all_stns_aws = pd.concat([df_all_stns_aws, df_aws]).reset_index(drop=True)

    # Add station name column
    df_gsmap.insert(loc = 0, column = 'name', value = stn['name'])

    print('Saved ' + stn['name'] + ' data')

    # Initialize wrf data table
    wrf_vars = {'rain': [], 'temp': [], 'rh': [], 'hi': []}

    # Access wrf fcst from 5 days ago
    wrf_fn = wrf_dir + 'forecast_lufft_stations_' + dt_var_str + '_08PHT.json'
    if path.exists(wrf_fn):
        df_wrf = pd.read_json(wrf_fn, orient='index')

        # Get 5-day data from wrf fcst json file

        for i in np.arange(0,120,1):
            for key in wrf_vars.keys():
                wrf_vars[key].append(df_wrf['forecast'][stn['name']]['hr'][i][key])

                # Set missing values to NaN
                wrf_vars[key] = [np.nan if v is None else v for v in wrf_vars[key]]

    return wrf_vars, df_aws, df_gsmap, dt_var_str