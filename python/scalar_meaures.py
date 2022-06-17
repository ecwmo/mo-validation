# Description: Statistical error metrics
# Author: Kevin Henson
# Last edited: June 17, 2022

import matplotlib.pyplot as plt
import datetime as dt
import pandas as pd
import numpy as np
from get_5day_gsmap_aws_wrf import get_5day_gsmap_aws_wrf
from scipy.stats import pearsonr
from pathlib import Path
# import sys

today = dt.date.today()
# today = dt.date(2022, 7, 5) # for testing

# set monthly calculation of metrics to occur every 5th of month 
if today.day == 5:
    print("Getting month average scalar accuracy measures")

    date_str = str(today)
    date_str_nohyphen = date_str.replace('-','')

    wrf_dir = '/home/modelman/forecast/output/stations_fcst_for_validation/json/'
    gsmap_dir = "/home/modelman/forecast/validation/gsmap/nc/"
    aws_dir = "/home/modelman/forecast/input/aws_files/"
    outdir = "/home/modelman/forecast/output/validation/" + date_str_nohyphen + "/00/"
    station_list = pd.read_csv('stations_lufft.csv')

    first = today.replace(day=2)
    lastMonth = first - dt.timedelta(days=2)
    first_of_lastMonth = lastMonth.replace(day=3)
    day_count = (first - first_of_lastMonth).days + 1

    # Set aws cols for extraction
    aws_cols = ['name', 'timestamp', 'rr', 'temp','rh','hi']

    # Compute R^2
    def R2(df1_wrf,df2_other):
        if (len(df1_wrf) > 0) and (len(df2_other) > 0):
            dict_out = {}
            cols = df2_other.drop(columns=['name','timestamp','time'], errors = 'ignore').columns

            for var in cols:
                x = df1_wrf[df1_wrf[var].notnull() & df2_other[var].notnull()][var]
                y = df2_other[df1_wrf[var].notnull() & df2_other[var].notnull()][var]

                # have at least 25 non-nan samples
                if (len(x) >= 25) and (len(y >= 25)):
                    r2, _ = pearsonr(x,y)
                    dict_out[var] = [r2**2]

            return pd.DataFrame(dict_out)

    # Initialize metrics data table for all stations
    metrics_cols = ['name', 'rain_me' , 'temp_me', 'rh_me', 'hi_me', 'rain_mae', 
                    'temp_mae', 'rh_mae', 'hi_mae', 'rain_rmse', 'temp_rmse',
                    'rh_rmse', 'hi_rmse', 'rain_r2mean', 'temp_r2mean', 'rh_r2mean', 'hi_r2mean']
    df_wrf_aws_metrics_allstns = pd.DataFrame(columns = metrics_cols)
    metrics_cols = ['name', 'rain_me' , 'rain_mae', 'rain_rmse', 'rain_r2mean']
    df_wrf_gsmap_metrics_allstns = pd.DataFrame(columns = metrics_cols)

    # Loop through stations
    for _, stn in station_list.iterrows():

        # Intialize wrf, aws, and gsmap data
        df_wrf_aws_diff = pd.DataFrame({'rain': [], 'temp': [], 'rh': [], 'hi': []})
        df_wrf_aws_r2 = pd.DataFrame({'rain': [], 'temp': [], 'rh': [], 'hi': []})
        df_wrf_gsmap_diff = pd.DataFrame({'rain': []})
        df_wrf_gsmap_r2 = pd.DataFrame({'rain': []})


        # Loop through days in month
        for single_date in (first_of_lastMonth + dt.timedelta(n) for n in range(day_count)):

            print(single_date.strftime("%Y%m%d"))
            df_wrf, df_aws, df_gsmap, _ = get_5day_gsmap_aws_wrf(single_date,stn)
            
            df_wrf = pd.DataFrame(df_wrf)

            # rename aws column to match wrf
            df_aws.rename(columns = {'rr':'rain'}, inplace=True)
            df_gsmap.rename(columns = {'precip':'rain'}, inplace=True)

            # Compute difference
            compare_cols = ['rain','temp','rh','hi']
            df_wrf_aws_diff_temp = df_wrf[compare_cols] - df_aws[compare_cols]
            compare_cols = ['rain']
            df_wrf_gsmap_diff_temp = df_wrf[compare_cols] - df_gsmap[compare_cols]

            # Compute R2 for each 5-day forecast
            df_r2_wrf_aws = R2(df_wrf,df_aws)
            df_r2_wrf_gsmap = R2(df_wrf,df_gsmap)

            df_wrf_aws_diff = pd.concat([df_wrf_aws_diff, df_wrf_aws_diff_temp])
            df_wrf_gsmap_diff = pd.concat([df_wrf_gsmap_diff, df_wrf_gsmap_diff_temp])
            df_wrf_aws_r2 = pd.concat([df_wrf_aws_r2,df_r2_wrf_aws])
            df_wrf_gsmap_r2 = pd.concat([df_wrf_gsmap_r2,df_r2_wrf_gsmap])

        rename_cols_wrf_aws = {'rain': 'rain_me', 'temp': 'temp_me', 'rh':'rh_me', 'hi': 'hi_me'}
        rename_cols_wrf_gsmap = {'rain': 'rain_me'}

        # Mean Error
        df_wrf_aws_metrics = df_wrf_aws_diff.mean()
        df_wrf_gsmap_metrics  = df_wrf_gsmap_diff.mean()
        rename_cols = {'rain': 'rain_me', 'temp': 'temp_me', 'rh':'rh_me', 'hi': 'hi_me'}
        df_wrf_aws_metrics.rename(index = rename_cols, inplace=True)
        rename_cols = {'rain': 'rain_me'}
        df_wrf_gsmap_metrics.rename(index = rename_cols_wrf_gsmap, inplace=True)

        # Mean Absolute Error
        df_wrf_aws_metrics_temp = df_wrf_aws_diff.abs().mean()
        df_wrf_gsmap_metrics_temp = df_wrf_gsmap_diff.abs().mean()
        df_wrf_aws_metrics = pd.concat([df_wrf_aws_metrics,df_wrf_aws_metrics_temp])
        df_wrf_gsmap_metrics = pd.concat([df_wrf_gsmap_metrics,df_wrf_gsmap_metrics_temp])
        rename_cols = {'rain': 'rain_mae', 'temp': 'temp_mae', 'rh':'rh_mae', 'hi': 'hi_mae'}
        df_wrf_aws_metrics.rename(index = rename_cols, inplace=True)
        rename_cols = {'rain': 'rain_mae'}
        df_wrf_gsmap_metrics.rename(index = rename_cols, inplace=True)

        # Root Mean Square Error
        df_wrf_aws_metrics_temp = (df_wrf_aws_diff**2).mean()**(1/2)
        df_wrf_gsmap_metrics_temp =  (df_wrf_gsmap_diff**2).mean()**(1/2)
        df_wrf_aws_metrics = pd.concat([df_wrf_aws_metrics,df_wrf_aws_metrics_temp])
        df_wrf_gsmap_metrics = pd.concat([df_wrf_gsmap_metrics,df_wrf_gsmap_metrics_temp])
        rename_cols = {'rain': 'rain_rmse', 'temp': 'temp_rmse', 'rh':'rh_rmse', 'hi': 'hi_rmse'}
        df_wrf_aws_metrics.rename(index = rename_cols, inplace=True)
        rename_cols = {'rain': 'rain_rmse'}
        df_wrf_gsmap_metrics.rename(index = rename_cols, inplace=True)

        # R^2
        df_wrf_aws_metrics_temp = df_wrf_aws_r2.mean()
        df_wrf_gsmap_metrics_temp = df_wrf_gsmap_r2.mean()
        df_wrf_aws_metrics = pd.concat([df_wrf_aws_metrics,df_wrf_aws_metrics_temp])
        df_wrf_gsmap_metrics = pd.concat([df_wrf_gsmap_metrics,df_wrf_gsmap_metrics_temp])
        rename_cols = {'rain': 'rain_r2mean', 'temp': 'temp_r2mean', 'rh':'rh_r2mean', 'hi': 'hi_r2mean'}
        df_wrf_aws_metrics.rename(index = rename_cols, inplace=True)
        rename_cols = {'rain': 'rain_r2mean'}
        df_wrf_gsmap_metrics.rename(index = rename_cols, inplace=True)

        df_wrf_aws_metrics = df_wrf_aws_metrics.to_frame().T
        df_wrf_gsmap_metrics = df_wrf_gsmap_metrics.to_frame().T

        # Insert station name column
        df_wrf_aws_metrics.insert(loc = 0, column = 'name', value = stn['name'])
        df_wrf_gsmap_metrics.insert(loc = 0, column = 'name', value = stn['name'])

        df_wrf_aws_metrics_allstns = pd.concat([df_wrf_aws_metrics_allstns, df_wrf_aws_metrics])
        df_wrf_gsmap_metrics_allstns = pd.concat([df_wrf_gsmap_metrics_allstns, df_wrf_gsmap_metrics])

    df_wrf_aws_metrics_allstns = df_wrf_aws_metrics_allstns.median()
    df_wrf_gsmap_metrics_allstns = df_wrf_gsmap_metrics_allstns.median()

    x = df_wrf_aws_metrics_allstns.round(2)
    y = df_wrf_gsmap_metrics_allstns.round(2)

    # Prepare data table
    data =  [
            [                        'rain aws',        'rain gsmap',         'temp',          'rh',            'hi'],
            [ 'ME'  ,                   x['rain_me']     , y['rain_me']     , x['temp_me']     , x['rh_me']     , x['hi_me']    ],
            [ 'MAE'   ,                 x['rain_mae']    , y['rain_mae']    , x['temp_mae']    , x['rh_mae']    , x['hi_mae']   ],
            [ 'RMSE',                   x['rain_rmse']   , y['rain_rmse']   , x['temp_rmse']   , x['rh_rmse']   , x['hi_rmse']  ],
            [ '$\mathregular{R^{2}}$',  x['rain_r2mean'] , y['rain_r2mean'] , x['temp_r2mean'] , x['rh_r2mean'] , x['hi_r2mean']],
            ]
    column_headers = data.pop(0)
    row_headers = [x.pop(0) for x in data]
    cell_text = []
    for row in data:
        cell_text.append([f'{x}' for x in row])
    rcolors = plt.cm.BuPu(np.full(len(row_headers), 0.1))
    ccolors = plt.cm.BuPu(np.full(len(column_headers), 0.1))

    title_text = f'Statistical Error Metrics (Daily 5-day forecasts)\n median across all stations {lastMonth.strftime("%B %Y")}'
    footer_text = 'ME: Mean Error, MAE: Mean Absolute Error, \nRMSE: Root Mean Square Error, $\mathregular{R^{2}}$: Coefficient of Determination'

    # figure plot settings
    plt.figure(linewidth=1,
            edgecolor='black',
            facecolor='white',
            dpi=300,
            figsize=(6,1.5))

    ax = plt.subplot()

    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
    ax.set_frame_on(False)
    ax.table(cellText=cell_text,
                        rowLabels=row_headers,
                        rowColours=rcolors,
                        colColours=ccolors,
                        colLabels=column_headers,
                        loc='upper center'
                        )
    ax.set_title(title_text+'\n', size = 10)

    # Add footer
    ax.text(0, 0.025, footer_text, horizontalalignment='left', size=6, weight='normal')

    out_file = Path(outdir) / f'error_metrics_{lastMonth.strftime("%b_%Y")}.png'
    out_file.parent.mkdir(parents=True,exist_ok=True)
    plt.savefig(str(out_file), dpi=300,bbox_inches='tight')
    print(f'Finished monthly statisitcal error measures!\n{out_file}')
