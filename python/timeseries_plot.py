#!/usr/bin/env python
# coding: utf-8
# how to run in terminal: $ export MPLBACKEND="agg"; python timeseries

# change initialization and variables for automation
# yyyymmdd and init are in local time (PHT)
yyyymmdd = '2022-03-09'
init = '08'
FCST_DIR = '/home/modelman/forecast/output/web/json'
CSV_DIR = '/home/modelman/forecast/output/validation/20220309/00'
OUT_DIR = '/home/modelman/forecast/output/validation/20220309/00'
CLIM_DIR = '/home/modelman/forecast/validation/aws/csv'
month = '03'
stn = 'MOIP'
station = 'Manila Observatory'
city_stn = 'NCR'

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

print(f"Reading forecast data at {yyyymmdd}_{init}PHT...")
df = pd.read_json(
    Path(FCST_DIR) / f"forecast_{yyyymmdd}_{init}PHT.json", orient='index'
)

# get data from json
PR_wrf = []
for i in np.arange(0,25,1):
    PR_wrf.append(df['forecast'][f'{city_stn}']['hr'][i]['rain'])
# --------------------------#
# Read GSMaP and GFS Data
# --------------------------#

print(f"Reading GSMaP and GFS data at {yyyymmdd}_{init}PHT...")
da = pd.read_csv(
    Path(CSV_DIR) / f"{stn}_gfs_gsmap_{yyyymmdd}_{init}PHT.csv", na_values="-999000000"
)

# get data from csv
PR_gsmap = np.array(da["gsmap"], dtype=float)
PR_gfs = np.array(da["gfs"], dtype=float)

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

print("plotting time series plots...")
# plot into 1 panel 1 column
plt.figure(dpi=300)
plt.rcParams["figure.figsize"] = (20, 6)

fig, (ax1) = plt.subplots(ncols=1, nrows=1)
indices = range(len(PR_gfs))
width = np.min(np.diff(indices)) / 4.0

# plot time series
ax1.axvline(x=0, ymin=-0.1, ymax=5, linestyle="dotted", color="gray")
ax1.axvline(x=24, ymin=-0.1, ymax=5, linestyle="dotted", color="gray")
ax1.axvline(x=48, ymin=-0.1, ymax=5, linestyle="dotted", color="gray")
ax1.bar(
    indices - width,
    PR_gfs,
    edgecolor="red",
    facecolor="red",
    width=0.3,
    label="GFS",
    zorder=1,
)
ax1.bar(
    indices,
    PR_wrf,
    edgecolor="blue",
    facecolor="blue",
    width=0.3,
    label="WRF",
    zorder=1,
)
ax1.bar(
    indices + width,
    PR_gsmap,
    edgecolor="black",
    facecolor="black",
    width=0.3,
    label="GSMaP",
    zorder=1,
)
# ax1.set_xticklabels(x_range)
ax1.set_xticks(np.arange(0, len(x_range) + 1, 3))
ax1.set_xticklabels(x_range[np.arange(0, len(x_range) + 1, 3)])
xmin1, xmax1 = ax1.get_xlim()
ymin1, ymax1 = ax1.get_ylim()
if ymax1 <= 5:
    ax1.axhline(y=1, xmin=xmin1, xmax=xmax1, linestyle="dotted", color="gray", zorder=0)
    ax1.axhline(y=2, xmin=xmin1, xmax=xmax1, linestyle="dotted", color="gray", zorder=0)
    ax1.axhline(y=3, xmin=xmin1, xmax=xmax1, linestyle="dotted", color="gray", zorder=0)
    ax1.axhline(y=4, xmin=xmin1, xmax=xmax1, linestyle="dotted", color="gray", zorder=0)
    ax1.axhline(y=5, xmin=xmin1, xmax=xmax1, linestyle="dotted", color="gray", zorder=0)
else:
    ax1.axhline(y=5, xmin=xmin1, xmax=xmax1, linestyle="dotted", color="gray", zorder=0)
    ax1.axhline(
        y=10, xmin=xmin1, xmax=xmax1, linestyle="dotted", color="gray", zorder=0
    )
    ax1.axhline(
        y=15, xmin=xmin1, xmax=xmax1, linestyle="dotted", color="gray", zorder=0
    )
    ax1.axhline(
        y=20, xmin=xmin1, xmax=xmax1, linestyle="dotted", color="gray", zorder=0
    )
    ax1.axhline(
        y=25, xmin=xmin1, xmax=xmax1, linestyle="dotted", color="gray", zorder=0
    )
    ax1.axhline(
        y=30, xmin=xmin1, xmax=xmax1, linestyle="dotted", color="gray", zorder=0
    )

    ax1.fill_between(
        x_range,
        7.5,
        15,
        color="yellow",
        alpha=0.5,
        # label="Heavy (7.5-15 mm/hr)"
    )
    ax1.fill_between(
        x_range,
        15,
        30,
        color="orange",
        alpha=0.5,
        # label="Intense (15-30 mm/hr)"
    )
    ax1.fill_between(
        x_range,
        30,
        50,
        color="red",
        alpha=0.5,
        # label="Torrential (> 30 mm/hr)"
    )
# Horizontal line of the climatological 1-day mean
ax1.axhline(y=clim, xmin=xmin1,xmax=xmax1, linestyle="dashed", color="black", zorder=0,label=f"{stn} daily mean")
if ymax1 <= 5:
    ymax12 = 5
else:
    ymax12 = ymax1
ax1.set_ylim([-0.1, ymax12])
ax1.set_xlim([-1, 25])
ax1.tick_params(axis="x", labelsize=20)
ax1.tick_params(axis="y", labelsize=24)
ax1.set_title(
    f"Forecast ({station})\nInitialized at {yyyymmdd} {init}:00 PHT",
    pad=38,
    fontsize=28,
)
ax1.set_ylabel("Rainfall (mm/hr)", size=24, color="black")
ax1.set_xlabel("Day and Time (PHT)", size=24)
ax1.legend(framealpha=1, frameon=True, loc="upper right", prop={"size": 24})

ymin1, ymax1 = ax1.get_ylim()
if ymax1 <= 5:
    ymax11 = 5
else:
    ymax11 = ymax1
if init == "20":
    ax1.text(12, ymax11 + (ymax11 * 0.01), x_range2[12], fontsize=26, ha="center")
    # ax1.text(36, ymax11+(ymax11*0.05), x_range2[36], fontsize=16,ha='center')
    # ax1.text(60, ymax11+(ymax11*0.05), x_range2[60], fontsize=16,ha='center')
else:
    ax1.text(12, ymax11 + (ymax11 * 0.01), x_range2[0], fontsize=26, ha="center")
    # ax1.text(36, ymax11+(ymax11*0.05), x_range2[24], fontsize=16,ha='center')
    # ax1.text(60, ymax11+(ymax11*0.05), x_range2[48], fontsize=16,ha='center')


print("done!")
print("Saving figure...")

out_file = Path(OUT_DIR) / f"validation_{stn}_{yyyymmdd}_{init}PHT.png"
out_file.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(str(out_file), dpi=300, bbox_inches="tight")
print("done!")
