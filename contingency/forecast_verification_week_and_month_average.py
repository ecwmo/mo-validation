# Title: Produce weekly average of daily contigency tables
# Author: Kevin Henson
# Last edited: May 12, 2022

#!/usr/bin/env python
# coding: utf-8

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patch
import datetime as dt
import calendar
from datetime import date,timedelta
from netCDF4 import Dataset
from contingency_functions import *
import os.path
#import cartopy.crs as ccrs

# initialize dataframe
def init_df():
    df =pd.DataFrame(0, index=['total', 'dry', 'low', 'mod', 'heavy', 'ext'], 
                    columns=['hit','f_alarm','miss','c_neg','fcst_yes','fcst_no',
                    'obs_yes','obs_no','total_obs','total_fcst','pod','far','sr',
                    'pod_ave_offset','far_sr_ave_offset'])
    return df

def weekAverage(date_today):

    df = init_df()

    # initialize functions for loop
    funcs = [calc_cont_total, calc_cont_dry, calc_cont_low, 
            calc_cont_mod, calc_cont_heavy,calc_cont_ext]

    today_str = str(date_today).replace('-','')
    init = '08'
    EXTRACT_DIR = '/home/modelman/forecast/validation/grads/nc'
    outdir = '/home/modelman/forecast/output/validation/'+today_str+'/00'

    print("Computing week average contingency tables ...")

    # days counter to account for missing data
    c = 0

    # for logging categories of values that need offsetting
    offset_pod = []
    offset_far_sr = []

    # Loop through last 7 days
    for i in range(0,7):
        yyyymmdd = str(date_today - timedelta(days=i))
        
        # open netCDF files and extract variables

        fname_wrf = Path(EXTRACT_DIR) / f'./wrf_24hr_rain_day1_{yyyymmdd}_{init}PHT.nc'

        fname_gsmap = Path(EXTRACT_DIR) / f'./gsmap_24hr_rain_day1_{yyyymmdd}_{init}PHT_re.nc'


        # Check if file exists
        if not(Path(fname_wrf).is_file()):
            print("File " + str(fname_wrf) +" does not exist")
            continue
        elif not(Path(fname_gsmap).is_file()):
            print("File " + str(fname_gsmap) +" does not exist")
            continue
        else:

            c += 1
            d1 = Dataset(fname_wrf)
            wrf = d1.variables['p24'][:, :]
            lats = d1.variables['lat'][:]
            lons = d1.variables['lon'][:]


            d2 = Dataset(fname_gsmap)
            gsmap = d2.variables['rsum'][:, :]
            lats = d2.variables['lat'][:]
            lons = d2.variables['lon'][:]

            for j,cat in enumerate(df.index):

                CONT=funcs[j](wrf[:,:],gsmap[:,:])

                # Contingency table values

                hit = np.count_nonzero(CONT == 4)
                f_alarm = np.count_nonzero(CONT == 3)
                miss = np.count_nonzero(CONT == 2)
                c_neg = np.count_nonzero(CONT == 1)

                df.at[cat, 'hit'] += hit
                df.at[cat, 'f_alarm'] +=  f_alarm
                df.at[cat, 'miss'] += miss
                df.at[cat, 'c_neg'] += c_neg

                df.at[cat, 'fcst_yes'] += hit + f_alarm
                df.at[cat, 'fcst_no'] += miss + c_neg
                df.at[cat, 'obs_yes'] += hit + miss
                df.at[cat, 'obs_no'] += f_alarm + c_neg
                df.at[cat, 'total_obs'] += df.at['total', 'obs_yes']+df.at['total', 'obs_no']
                df.at[cat, 'total_fcst'] += df.at['total', 'fcst_yes']+df.at['total', 'fcst_no']

                # Forecast metrics 
                # Check for division by zero
                if (hit + miss) != 0 and (hit + f_alarm) !=0:
                    
                    df.at[cat, 'pod'] += (hit / (hit + miss)        )*100
                    df.at[cat, 'far'] += (f_alarm / (hit + f_alarm) )*100
                    df.at[cat, 'sr']  += (hit / (hit + f_alarm)     )*100

                # log offset for weekly averaging if there is division by zero
                elif (hit + miss) == 0:
                    df.at[cat, 'pod_ave_offset'] += 1
                    offset_pod.append(cat)
                elif (hit + f_alarm) == 0:
                    df.at[cat, 'far_sr_ave_offset'] += 1
                    offset_far_sr.append(cat)

    # Save offsets
    df_offsets = df[df.columns[13:15]]

    # Compute week average except offset columns
    df=df[df.columns[:13]]/c
    df=pd.concat([df,df_offsets],axis=1)

    # Divide pod,far, or sr by c-offset to account for days with division by 0 for pod, far, and sr
    for cat_offset in offset_pod:
        df.at[cat_offset, 'pod'] *= c / (c-df.at[cat_offset, 'pod_ave_offset'])
        # print('offset averaging of pod '+ cat_offset + ' by '
        #  + str(df.at[cat_offset, 'pod_ave_offset']))

    for cat_offset in offset_far_sr:
        df.at[cat_offset, 'far'] *= c / (c-df.at[cat_offset, 'far_sr_ave_offset'])
        df.at[cat_offset, 'sr'] *= c / (c-df.at[cat_offset, 'far_sr_ave_offset'])
        # print('offset averaging of far and sar '+ cat_offset + ' by '
        #  + str(df.at[cat_offset, 'far_sr_ave_offset']))

    return outdir, today, init, df[df.columns[:13]]

def plot_cont(outdir, date, init_var, df_var, duration):

    date_var = str(date)

    # figure plot settings

    plt.figure(linewidth=2,
            edgecolor='black',
            facecolor='white',
    #           tight_layout={'pad':1},
            dpi=300)
    plt.rcParams["figure.figsize"] = (20,6)
    fig, ((ax1,ax2,ax3),(ax4,ax5,ax6)) = plt.subplots(ncols=3,nrows=2)
    ax_list = [ax1, ax2, ax3, ax4, ax5, ax6]

    # plotting variable settings
    fig_background_color = 'white'
    fig_border = 'black'
    obs_title = 'Observation (GSMaP)'
    fcst_title = 'Forecast (WRF)'

    # loop through rainfall categories to produce contigency tables
    for i,cat in enumerate(df_var.index):

        hit = round(df_var.at[cat,'hit'])
        miss = round(df_var.at[cat,'miss'])
        f_alarm = round(df_var.at[cat,'f_alarm'])
        c_neg = round(df_var.at[cat,'c_neg'])
        obs_yes = round(df_var.at[cat,'obs_yes'])
        obs_no = round(df_var.at[cat,'obs_no'])
        fcst_yes = round(df_var.at[cat,'fcst_yes'])
        fcst_no = round(df_var.at[cat,'fcst_no'])
        totalobs = obs_yes + obs_no

        # Format to whole number
        pod = '{:0.2f} %'.format(df_var.at[cat,'pod'])
        far = '{:0.2f} %'.format(df_var.at[cat,'far'])
        sr = '{:0.2f} %'.format(df_var.at[cat,'sr'])

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

        # Adjust date for label
        plot_label = str(date - timedelta(days=6))

        if duration == 'Week':
            x_range = pd.date_range(f'{plot_label}-{init_var}',periods=169, freq='H').strftime('%Y-%m-%d %H:00')
            label = f'from {plot_label} {init_var}:00 to {x_range[168]} PHT'
            label_dir = f'{date_var}_{init_var}PHT.png'
        elif duration == 'Month':
            label = f'{plot_label[0:7]}'
            label_dir = f'{plot_label[0:7]}.png'


        title_text = f'{duration} Average Contingency Table ({cat} rainfall)\n{label}'
        footer_text = f'Probability of Detection = {pod}\nFalse Alarm Ratio = {far}\nSuccess Ratio = {sr}'

        ax = ax_list[i]

        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
        ax.set_frame_on(False)
        ax.table(cellText=cell_text,
                            rowLabels=row_headers,
                            rowColours=rcolors,
                            rowLoc='center',
                            colColours=ccolors,
                            colLabels=column_headers,
                            loc='upper center')
        ax.set_title(title_text + '\n')
        # Add footer
        ax.text(0.5, 0.35, footer_text, horizontalalignment='center', size=12, weight='normal')
        ax.text(0.35, 1., obs_title, horizontalalignment='center',size=10, weight='normal')
        ax.text(-0.11, 0.65, fcst_title, horizontalalignment='center',size=10, weight='normal',rotation='vertical')

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

    out_file = Path(outdir) / f'contingency_{duration}Average_{label_dir}'
    out_file.parent.mkdir(parents=True,exist_ok=True)
    out_file = str(out_file)
    plt.savefig(out_file, dpi=300,bbox_inches='tight')
    print ('Saved ' + out_file)
    
# Get sundays of month

def allsundays_compute_month_average(date_var):
    last_day_of_prev_month = date_var.replace(day=1) - timedelta(days=1)
    date_var = date_var.replace(day=1) - timedelta(days=last_day_of_prev_month.day)
    
    d = date_var                   
    d += timedelta(days = 6 - d.weekday())

    # Counter for averaging
    c = 0

    # intialize dataframe
    df = init_df()
    df = df[df.columns[:13]]

    print("Computing month average contingency tables ...")

    # Set allowance for weeks that overlap between months
    if d.day > 4:
        df += weekAverage(d)[-1]
        c += 1
    
    while d.month == date_var.month:
        d += timedelta(days = 7)

        # Set allowance for weeks that overlap between months
        if d.month == date_var.month or d.day < 3:
            outdir, today, init, df_var = weekAverage(d)
            df += df_var
            c += 1

    return outdir, today, init, (df / c)
    
today = dt.date.today()
# today = dt.date(2022, 4, 5) # for testing
day_name = calendar.day_name[today.weekday()]

# Run 7 day average
if day_name == "Sunday":

    print("Computing week average of daily contingency tables")
    
    outdir, today_var, init_var, df_var = weekAverage(today)
    plot_cont(outdir, today_var, init_var, df_var,'Week')

    print("Done with week average!")

# set monthly averaging to occur every 5th of month 
# to give allowance for weeks that overlap into first 
# few days of month
if today.day == 5:
    print("Getting month average contingency table from weekly averages")
    _, today_var, init_var, df_var = allsundays_compute_month_average(today)

    today_str = str(today).replace('-','')
    outdir = '/home/modelman/forecast/output/validation/'+today_str+'/00'
    
    plot_cont(outdir, today_var, init_var, df_var,'Month',)
    
    print("Done with month average!")