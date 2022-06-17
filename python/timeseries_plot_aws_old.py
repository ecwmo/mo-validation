#Title: 24-hour time series comparison 
#Author: Angela Magnaye & Kevin Henson
#Last edited: May 26, 2022

#!/usr/bin/env python
# coding: utf-8
# how to run in terminal: $ export MPLBACKEND="agg"; python timeseries

# change initialization and variables for automation
# yyyymmdd and init are in local time (PHT)
yyyymmdd = '2021-08-18'
init = '08'
FCST_DIR = '/home/modelman/forecast/output/web/json'
CSV_DIR = '/home/modelman/forecast/output/validation/20210818/00'
AWS_DIR = '/home/modelman/forecast/validation/aws/csv'
OUT_DIR = '/home/modelman/forecast/output/validation/20210818/00'
CLIM_DIR = '/home/modelman/forecast/validation/aws/csv'
month = '08'
stn = 'MOIP'
station = 'Manila Observatory'
city_stn = 'NCR'

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.legend import Legend

print(f"Reading forecast data at {yyyymmdd}_{init}PHT...")
df = pd.read_json(
    Path(FCST_DIR) / f"forecast_{yyyymmdd}_{init}PHT.json", orient='index'
)
   
# get data from json
rain_wrf = []
temp_wrf = []
rh_wrf = []
hi_wrf = []
for i in np.arange(0,25,1):
    rain_wrf.append(df['forecast'][f'{city_stn}']['hr'][i]['rain'])
    temp_wrf.append(df['forecast'][f'{city_stn}']['hr'][i]['temp'])
    rh_wrf.append(df['forecast'][f'{city_stn}']['hr'][i]['rh'])
    hi_wrf.append(df['forecast'][f'{city_stn}']['hr'][i]['hi'])

hi_wrf = [np.nan if v is None else v for v in hi_wrf]

# --------------------------#
# Read GSMaP and AWS Data
# --------------------------#

print(f"Reading GSMaP and AWS data at {yyyymmdd}_{init}PHT...")
da = pd.read_csv(
    Path(CSV_DIR) / f"{stn}_gfs_gsmap_{yyyymmdd}_{init}PHT.csv", na_values="-999000000"
)

# get data from csv
rain_gsmap = np.array(da["gsmap"], dtype=float)
#PR_gfs = np.array(da["gfs"], dtype=float)

daws = pd.read_csv(
    Path(AWS_DIR) / f"{stn}_aws_{yyyymmdd}_{init}PHT.csv", na_values="-999000000"
)

# get data from csv
rain_aws = np.array(daws["RainRate"], dtype=float)
temp_aws = np.array(daws["TempOut"], dtype=float)
rh_aws = np.array(daws["OutHum"], dtype=float)
hi_aws = np.array(daws["HeatIndex"], dtype=float)

# --------------------------#
# Read AWS Clim Data
# --------------------------#
print(f"Reading Climatology data for month {month}...")
dc = pd.read_csv(
    Path(CLIM_DIR) / f"03_multyear_monthlymean_{stn}_2012-2019.csv")

clim = dc['mean_mm.day'][int(month)]

# get dates for x-axis labels
x_range = pd.date_range(f"{yyyymmdd}-{init}", periods=25, freq="H").strftime("%a %H:00")
y_range = np.array([10 for x in range(25)])
x_range2 = pd.date_range(f"{yyyymmdd}-{init}", periods=25, freq="H").strftime(
    "%A %b %-d"
)

# Define function for plotting
def plot_comparison(ax, var, label, data_aws, data_wrf, ymin):
    print("plotting "+var+" time series plots...")

    indices = range(len(rain_gsmap))
    width = np.min(np.diff(indices)) / 4.0
    
    # plot time series
    ax.axvline(x=0, ymin=-0.1, ymax=5, linestyle="dotted", color="gray")
    ax.axvline(x=24, ymin=-0.1, ymax=5, linestyle="dotted", color="gray")
    ax.axvline(x=48, ymin=-0.1, ymax=5, linestyle="dotted", color="gray")

    labels1 = []
    labels2 = []
    leg_items = []
    leg_items2 = []

    if var=='rain':
        
        leg_items.append( ax.bar(
            indices - width,
            data_aws,
            edgecolor="red",
            facecolor="red",
            width=0.3,
            zorder=1,
        ))
        
        labels1.append("AWS")

        print(len(indices))
        print(len(data_wrf))

        leg_items.append(ax.bar(
            indices,
            data_wrf,
            edgecolor="C0",
            facecolor="C0",
            width=0.3,
            zorder=1,
        ))

        labels1.append("WRF")
        
        leg_items.append(ax.bar(
            indices + width,
            rain_gsmap,
            edgecolor="black",
            facecolor="black",
            width=0.3,
            zorder=1,
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
        
    ax.set_xticks(np.arange(0, len(x_range) + 1, 3))
    xmin1, xmax1 = ax.get_xlim()
    ymin1, ymax1 = ax.get_ylim()

    # Define function for plot shading
    def plot_shading(dict):
        labels=list(shading.keys())
        for cat in labels:
            leg_items2.append(ax.fill_between(
                x_range,
                shading[cat][1],
                shading[cat][2],
                color=shading[cat][0],
                alpha=0.5,
            ))
            labels2.append(cat)

    yrange = ymax1-ymin

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

    if yrange+yrange*0.1 <30:
        increment = 2.5
    else:
        increment = 5

    for i, step in enumerate(np.arange(ymin,ymax1,increment)):
        ax.axhline(
        y=ymin+increment*i, xmin=xmin1, xmax=xmax1, linestyle="dotted", color="gray", zorder=0
        )

    ax.set_ylim([ymin-0.1, ymax1+yrange*0.1])
    ax.set_xlim([-1, 25])
    ax.tick_params(axis="y", labelsize=24)
    ax.set_xticklabels(x_range[np.arange(0, len(x_range) + 1, 3)])
    ax.tick_params(axis="x", labelbottom = True, labelsize=20)
    ax.set_xlabel("Day and Time (PHT)", size=24)

    ax.set_ylabel(label, size=24, color="black")

    if var=='rain':
        leg = Legend(ax, leg_items2, labels2, framealpha=0.5, frameon=False, 
                    loc=[0.6,-0.24], title='Shading', prop={"size": 16}, ncol=len(labels2))
        ax.add_artist(leg)
        plt.setp(leg.get_title(),fontsize='16')

    if var=='hi':
        leg = Legend(ax, leg_items2, labels2, framealpha=0.5, frameon=False, 
                    loc=[0.5,-0.24], title='Shading', prop={"size": 16}, ncol=len(labels2))
        ax.add_artist(leg)
        plt.setp(leg.get_title(),fontsize='16')

    return leg_items, labels1

plt.figure(dpi=300)
plt.rcParams["figure.figsize"] = (20, 24)

fig, (ax1,ax2,ax3,ax4) = plt.subplots(ncols=1, nrows=4)

plot_comparison(ax1, 'rain', 'Rainfall (mm/hr)', rain_aws, rain_wrf, 0)
plot_comparison(ax2, 'temp', 'Temperature (C\N{DEGREE SIGN})', temp_aws, temp_wrf, 15)
plot_comparison(ax3, 'rh', 'Relative Humidity (%)', rh_aws, rh_wrf, 10)
plot_comparison(ax4, 'hi', 'Heat Index (C\N{DEGREE SIGN})', hi_aws, hi_wrf, 15)

if init == "20":
    day_label = x_range2[12]
else:
    day_label = x_range2[0] 

ax1.set_title(
    f"Forecast ({station})\nInitialized at {yyyymmdd} {init}:00 PHT\n" + day_label,
    pad=28,
    fontsize=28,
)

print("Saving figure...")

out_file = Path(OUT_DIR) / f"validation_aws_combined_{stn}_{yyyymmdd}_{init}PHT.png"
out_file.parent.mkdir(parents=True, exist_ok=True)
fig.tight_layout(pad=2.0)
plt.savefig(str(out_file), dpi=300)
print("done!")