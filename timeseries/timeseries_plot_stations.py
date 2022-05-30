# Description: 5-day time series comparison 
# Author: Angela Magnaye & Kevin Henson
# Last edit: May 30, 2022

from pathlib import Path
import pandas as pd
import numpy as np
import xarray as xr
from datetime import date,timedelta
import matplotlib.pyplot as plt
from matplotlib.legend import Legend
# import sys

# Define function for plotting
def plot_comparison(dt, ax, var, label, data_aws, data_wrf, ymin, data_gsmap=None):
    print("plotting "+var+" time series plots...")

    data_aws = np.array(data_aws, dtype=float)
    data_gsmap = np.array(data_gsmap, dtype=float)

    indices = range(len(data_wrf))
    width = np.min(np.diff(indices)) / 3.0
    
    # plot time series
    ax.axvline(x=0, ymin=-0.1, ymax=5, linestyle="dotted", color="gray")
    ax.axvline(x=24, ymin=-0.1, ymax=5, linestyle="dotted", color="gray")
    ax.axvline(x=48, ymin=-0.1, ymax=5, linestyle="dotted", color="gray")

    labels1 = []
    labels2 = []
    leg_items = []
    leg_items2 = []
  
    date_var_str = str(dt - timedelta(5))
    x_range_for_shading = pd.date_range(date_var_str + '-08', periods=121, freq="H").strftime("%a %H")

    if var=='rain':
        w = 0.2        
        leg_items.append( ax.bar(
            indices - width,
            data_aws,
            edgecolor="red",
            facecolor="red",
            width=w,
            zorder=2,
        ))
        
        labels1.append("AWS")

        leg_items.append(ax.bar(
            indices,
            data_wrf,
            edgecolor="C0",
            facecolor="C0",
            width=w,
            zorder=2,
        ))

        labels1.append("WRF")
        
        leg_items.append(ax.bar(
            indices + width,
            data_gsmap,
            edgecolor="black",
            facecolor="black",
            width=w,
            zorder=2,
        ))

        labels1.append("GSMAP")
        
        ax.legend( leg_items, labels1, framealpha=0.5, frameon=True, loc="upper right", prop={"size": 24})

    else:
        ax.plot(
        indices,
        data_aws,
        c = 'r',
        marker = 'o',
        label = 'AWS'
        )

        ax.plot(
            indices,
            data_wrf,
            c = 'C0',
            marker = 'o',
            label = 'WRF'
        )

        ax.legend(framealpha=0.5, frameon=True, loc="upper right", prop={"size": 24})

    xmin1, xmax1 = ax.get_xlim()
    ymin1, ymax1 = ax.get_ylim()
    yrange = ymax1-ymin1

    # Define function for plot shading
    def plot_shading(shading):
        labels=list(shading.keys())
        for cat in labels:
            leg_items2.append(ax.fill_between(
                x_range_for_shading,
                shading[cat][1],
                shading[cat][2],
                color=shading[cat][0],
                alpha=0.5,
                zorder=1
            ))
            labels2.append(cat)

    #Rain-specific plotting parameters
    if var=='rain':
        shading = {
            'Heavy': ['yellow',7.5, 15,'(7.5-15 mm/hr)'],
            'Intense': ['orange',15,30,'(15-30 mm/hr)'],
            'Torrential': ['red',30,ymax1+yrange*0.1,'(> 30 mm/hr)']
            }
    
        plot_shading(shading)

    #Heat index-specific plotting parameters
    if var=='hi':
        shading = {
            'Caution': ['#EFE685',27,32,'(27-32 \N{DEGREE SIGN}C)'],
            'Extreme Caution': ['#FF8C00',32,41,'(32-41 \N{DEGREE SIGN}C)'],
            'Danger': ['#B3211A',41,54,'(41-54 \N{DEGREE SIGN}C)'],
            'Extreme Danger': ['#9A27CF',54,ymax1+yrange*0.1,'(> 54 \N{DEGREE SIGN}C)']
            }
        plot_shading(shading)

    # get dates for x-axis labels
    x_range = pd.date_range(date_var_str + '-08', periods=121, freq="H").strftime("%H")
    x_range2 = pd.date_range(date_var_str + '-08', periods=121, freq="H").strftime("%a ")

    x_tick_labels = []
    for i, t in enumerate(x_range):
        if t == '02' or i ==0:
            x_tick_labels.append(x_range[i]+'\n'+x_range2[i])
        else:
            x_tick_labels.append(x_range[i])
    x_tick_labels = np.array(x_tick_labels)

    ax.set_xticks(np.arange(0, len(x_range) + 1, 3))
    
    plot_range = yrange*1.2
    if plot_range <30:
        increment = 2.5
    elif plot_range >60:
        increment = 10
    else:
        increment = 5

    for i, _ in enumerate(np.arange(ymin,ymax1,increment)):
        ax.axhline(
        y=ymin+increment*i, xmin=xmin1, xmax=xmax1, linestyle="dotted", color="gray", zorder=0
        )

    def round_down(num, divisor):
        return num - (num%divisor)

    if var == 'rain':
        ax.set_ylim([0, ymax1+yrange*0.1])
    else:
        ax.set_ylim([round_down(ymin1-yrange*0.1,5), ymax1+yrange*0.1])
    ax.set_xlim([-1, 121])
    ax.tick_params(axis="y", labelsize=24)
    ax.set_xticklabels(x_tick_labels[np.arange(0, len(x_range) + 1, 3)])

    ax.tick_params(axis="x", labelsize=20)

    for tick_label in ax.xaxis.get_ticklabels()[1::2]:
        tick_label.set_visible(False)
        
    ax.set_ylabel(label, size=24, color="black")

    if var=='rain':
        leg = Legend(ax, leg_items2, labels2, framealpha=0.5, frameon=False, 
                    loc=[0.7,-0.22], title='Shading', prop={"size": 16}, ncol=len(labels2))
        ax.add_artist(leg)
        plt.setp(leg.get_title(),fontsize='16')

    if var=='hi':
        leg = Legend(ax, leg_items2, labels2, framealpha=0.5, frameon=False, 
                    loc=[0.5,-0.305], title='Shading', prop={"size": 16}, ncol=len(labels2))
        ax.add_artist(leg)
        plt.setp(leg.get_title(),fontsize='16')

# For testing
# dt = date(2022,3,11)

dt = date.today()

date_str = str(dt)
date_str_nohyphen = date_str.replace('-','')

wrf_dir = '/home/modelman/forecast/output/stations_fcst_for_validation/json/'
gsmap_dir = "/home/modelman/forecast/validation/gsmap/nc/"
aws_dir = "/home/modelman/forecast/input/aws_files/"
outdir = "/home/modelman/forecast/output/validation/" + date_str_nohyphen + "/00/"
station_list = pd.read_csv('stations_lufft.csv')

# Initialize gsmap and aws dataframe
df_all_stns_gsmap = pd.DataFrame(columns=['name', 'time', 'precip'])
aws_cols = ['name', 'timestamp', 'rr','temp','rh','hi']
df_all_stns_aws = pd.DataFrame(columns=aws_cols)

# Loop through stations
for i, stn in station_list.iterrows():

    # Intialize dataframe for each station
    df_gsmap = pd.DataFrame(columns=['time','precip',])
    df_aws = pd.DataFrame(columns = aws_cols)
    
    # Loop through past 5 days
    for day in reversed(np.arange(1, 6)):

        # Set date variable
        dt_var = dt - timedelta(int(day))

        # Access gsmap file and data
        gsmap_df = xr.open_dataset(gsmap_dir + "gsmap_gauge_" + str(dt_var) + "_00_ph.nc")
        aws_df = pd.read_csv(aws_dir + 'stn_obs_24hr_' + str(dt_var) +'_08PHT.csv',
                             usecols=aws_cols, na_values="-999.000000")
        aws_df = aws_df[aws_df['name'] == stn['name']]
        df_temp_gsmap = gsmap_df.sel(lon=stn['lon'], lat=stn['lat'], method="nearest").to_dataframe()
        df_temp_gsmap = df_temp_gsmap['precip'].reset_index(level='time')
        
        # Append daily data
        df_gsmap = pd.concat([df_gsmap,df_temp_gsmap])
        df_aws = pd.concat([df_aws,aws_df])

    df_gsmap = df_gsmap.reset_index(drop=True)
    df_aws = df_aws.reset_index(drop=True)

    # Fill-in missing timesteps
    df_aws['timestamp'] = pd.to_datetime(df_aws['timestamp'])
    dt_var = dt - timedelta(5)
    dt_var_str = str(dt_var)
    start = pd.to_datetime(dt_var_str + ' 09:00:00+08:00')
    end = pd.to_datetime(date_str + ' 08:00:00+08:00')
    dates = pd.date_range(start=start, end=end, freq='1H')

    df_aws = df_aws.set_index('timestamp').reindex(dates).reset_index().reindex(columns=df_aws.columns)
    cols = df_aws.columns.difference(['rr','temp','rh','hi'])
    df_aws[cols] = df_aws[cols].ffill()
    df_aws['timestamp'] = dates

    # # Append 5-day station data
    # df_all_stns_gsmap = pd.concat([df_all_stns_gsmap, df_gsmap]).reset_index(drop=True)
    # df_all_stns_aws = pd.concat([df_all_stns_aws, df_aws]).reset_index(drop=True)

    # Add station name column
    df_gsmap.insert(loc = 0, column = 'name', value = stn['name'])
    
    print('Saved ' + stn['name'] + ' data')

    # Access wrf fcst from 5 days ago
    df_wrf = pd.read_json(wrf_dir + 'forecast_lufft_stations_' + dt_var_str + '_08PHT.json', orient='index')

    # Get 5-day data from wrf fcst json file

    wrf_vars = {'rain': [], 'temp': [], 'rh': [], 'hi': []}

    for i in np.arange(0,120,1):
        for key in wrf_vars.keys():
            wrf_vars[key].append(df_wrf['forecast'][stn['name']]['hr'][i][key])

            # Set missing values to NaN
            wrf_vars[key] = [np.nan if v is None else v for v in wrf_vars[key]]

    # Plotting for each station
    plt.figure(dpi=300)
    plt.rcParams["figure.figsize"] = (20, 24)

    fig, (ax1,ax2,ax3,ax4) = plt.subplots(ncols=1, nrows=4)

    plot_comparison(dt, ax1, 'rain', 'Rainfall (mm/hr)', df_aws['rr'], wrf_vars['rain'], 0, df_gsmap['precip'])
    plot_comparison(dt, ax2, 'temp', 'Temperature (C\N{DEGREE SIGN})', df_aws['temp'], wrf_vars['temp'], 15)
    plot_comparison(dt, ax3, 'rh', 'Relative Humidity (%)', df_aws['rh'], wrf_vars['rh'], 10)
    plot_comparison(dt, ax4, 'hi', 'Heat Index (C\N{DEGREE SIGN})', df_aws['hi'], wrf_vars['hi'], 15)

    ax1.set_title(
        f"Forecast ({stn['name']})\nInitialized at {dt_var_str} 08:00 PHT",
        pad=28,
        fontsize=28,
    )

    ax4.set_xlabel("Day and Time (PHT)", size=24)


    out_file = Path(outdir) / f"validation_aws_combined_{stn['name']}_{date_str}_08PHT.png"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(pad=2.0)
    plt.savefig(str(out_file), dpi=300)
    print("Saved figure " + str(out_file))
    # sys.exit()

# For outputting to csv

# Rename header
# df_all_stns.rename(columns = {'precip':'precip(mm)'}, inplace = True)

# outfile = outdir + 'gsmap_5days_' + str(dt) + "UTC_lufft_stations"
# df_all_stns.to_csv(outfile, index = False)

