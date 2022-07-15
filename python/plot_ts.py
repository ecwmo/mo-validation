import os
import sys
import getopt
from pathlib import Path
import pytz
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

tz = pytz.timezone("Asia/Manila")

stn = os.getenv("STATION_ID")
stn_name = os.getenv("STATION_NAME")
city_stn = os.getenv("CITY_ID")

fcst_dir = Path(os.getenv("FCST_DIR"))
stn_clim_dir = Path(os.getenv("STN_CLIM_DIR"))


def proc(in_dir, out_dir):
    yyyymmdd = in_dir.parent.name
    zz = in_dir.name
    init_dt = pd.to_datetime(
        f"{yyyymmdd}_{zz}", format="%Y%m%d_%H", utc=True
    ).astimezone(tz)
    init_dt_str = init_dt.strftime("%Y-%m-%d_%H")
    month_str = init_dt.strftime("%m")
    hh_str = init_dt.strftime("%H")

    print(f"Reading forecast data at {init_dt_str}PHT...")
    df = pd.read_json(fcst_dir / f"forecast_{init_dt_str}PHT.json", orient="index")

    # get data from json
    PR_wrf = []
    for i in np.arange(0, 25, 1):
        PR_wrf.append(df["forecast"][f"{city_stn}"]["hr"][i]["rain"])
    # --------------------------#
    # Read GSMaP and GFS Data
    # --------------------------#

    print(f"Reading GSMaP and GFS data at {init_dt_str}PHT...")
    da = pd.read_csv(
        in_dir / f"{stn}_gfs_gsmap_{init_dt_str}PHT.csv",
        na_values="-999000000",
    )

    # get data from csv
    PR_gsmap = np.array(da["gsmap"], dtype=float)
    PR_gfs = np.array(da["gfs"], dtype=float)

    # --------------------------#
    # Read AWS Clim Data
    # --------------------------#
    print(f"Reading Climatology data for month {month_str}...")
    dc = pd.read_csv(stn_clim_dir / f"03_multyear_monthlymean_{stn}_2012-2019.csv")

    clim = dc["mean_mm.day"][int(month_str)]

    # get dates for x-axis labels
    x_range = pd.date_range(f"{init_dt}", periods=25, freq="H").strftime("%a %H:00")
    # y_range = np.array([10 for x in range(25)])
    x_range2 = pd.date_range(f"{init_dt}", periods=25, freq="H").strftime("%A %b %-d")

    print("plotting time series plots...")
    fig, ax = plt.subplots(figsize=(20, 6))
    indices = range(len(PR_gfs))
    width = np.min(np.diff(indices)) / 4.0

    # plot time series
    ax.axvline(x=0, ymin=-0.1, ymax=5, linestyle="dotted", color="gray")
    ax.axvline(x=24, ymin=-0.1, ymax=5, linestyle="dotted", color="gray")
    ax.axvline(x=48, ymin=-0.1, ymax=5, linestyle="dotted", color="gray")
    ax.bar(
        indices - width,
        PR_gfs,
        edgecolor="red",
        facecolor="red",
        width=0.3,
        label="GFS",
        zorder=1,
    )
    ax.bar(
        indices,
        PR_wrf,
        edgecolor="blue",
        facecolor="blue",
        width=0.3,
        label="WRF",
        zorder=1,
    )
    ax.bar(
        indices + width,
        PR_gsmap,
        edgecolor="black",
        facecolor="black",
        width=0.3,
        label="GSMaP",
        zorder=1,
    )
    # ax.set_xticklabels(x_range)
    ax.set_xticks(np.arange(0, len(x_range) + 1, 3))
    ax.set_xticklabels(x_range[np.arange(0, len(x_range) + 1, 3)])
    xmin1, xmax1 = ax.get_xlim()
    ymin1, ymax1 = ax.get_ylim()
    if ymax1 <= 5:
        ax.axhline(
            y=1, xmin=xmin1, xmax=xmax1, linestyle="dotted", color="gray", zorder=0
        )
        ax.axhline(
            y=2, xmin=xmin1, xmax=xmax1, linestyle="dotted", color="gray", zorder=0
        )
        ax.axhline(
            y=3, xmin=xmin1, xmax=xmax1, linestyle="dotted", color="gray", zorder=0
        )
        ax.axhline(
            y=4, xmin=xmin1, xmax=xmax1, linestyle="dotted", color="gray", zorder=0
        )
        ax.axhline(
            y=5, xmin=xmin1, xmax=xmax1, linestyle="dotted", color="gray", zorder=0
        )
    else:
        ax.axhline(
            y=5, xmin=xmin1, xmax=xmax1, linestyle="dotted", color="gray", zorder=0
        )
        ax.axhline(
            y=10, xmin=xmin1, xmax=xmax1, linestyle="dotted", color="gray", zorder=0
        )
        ax.axhline(
            y=15, xmin=xmin1, xmax=xmax1, linestyle="dotted", color="gray", zorder=0
        )
        ax.axhline(
            y=20, xmin=xmin1, xmax=xmax1, linestyle="dotted", color="gray", zorder=0
        )
        ax.axhline(
            y=25, xmin=xmin1, xmax=xmax1, linestyle="dotted", color="gray", zorder=0
        )
        ax.axhline(
            y=30, xmin=xmin1, xmax=xmax1, linestyle="dotted", color="gray", zorder=0
        )

        ax.fill_between(
            x_range,
            7.5,
            15,
            color="yellow",
            alpha=0.5,
            # label="Heavy (7.5-15 mm/hr)"
        )
        ax.fill_between(
            x_range,
            15,
            30,
            color="orange",
            alpha=0.5,
            # label="Intense (15-30 mm/hr)"
        )
        ax.fill_between(
            x_range,
            30,
            50,
            color="red",
            alpha=0.5,
            # label="Torrential (> 30 mm/hr)"
        )
    # Horizontal line of the climatological 1-day mean
    ax.axhline(
        y=clim,
        xmin=xmin1,
        xmax=xmax1,
        linestyle="dashed",
        color="black",
        zorder=0,
        label=f"{stn} daily mean",
    )
    if ymax1 <= 5:
        ymax12 = 5
    else:
        ymax12 = ymax1
    ax.set_ylim([-0.1, ymax12])
    ax.set_xlim([-1, 25])
    ax.tick_params(axis="x", labelsize=20)
    ax.tick_params(axis="y", labelsize=24)
    ax.set_title(
        f"Forecast ({stn_name})\nInitialized at {init_dt_str}:00 PHT",
        pad=38,
        fontsize=28,
    )
    ax.set_ylabel("Rainfall (mm/hr)", size=24, color="black")
    ax.set_xlabel("Day and Time (PHT)", size=24)
    ax.legend(framealpha=1, frameon=True, loc="upper right", prop={"size": 24})

    ymin1, ymax1 = ax.get_ylim()
    if ymax1 <= 5:
        ymax11 = 5
    else:
        ymax11 = ymax1
    if hh_str == "20":
        ax.text(12, ymax11 + (ymax11 * 0.01), x_range2[12], fontsize=26, ha="center")
        # ax.text(36, ymax11+(ymax11*0.05), x_range2[36], fontsize=16,ha='center')
        # ax.text(60, ymax11+(ymax11*0.05), x_range2[60], fontsize=16,ha='center')
    else:
        ax.text(12, ymax11 + (ymax11 * 0.01), x_range2[0], fontsize=26, ha="center")
        # ax.text(36, ymax11+(ymax11*0.05), x_range2[24], fontsize=16,ha='center')
        # ax.text(60, ymax11+(ymax11*0.05), x_range2[48], fontsize=16,ha='center')

    print("done!")
    print("Saving figure...")
    out_file = out_dir / f"validation_{stn}_{init_dt_str}PHT.png"
    fig.savefig(out_file, bbox_inches="tight", dpi=300)
    plt.close("all")
    print("done!")


if __name__ == "__main__":
    in_dir = Path("dat")
    out_dir = Path("")
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hi:o:", ["idir=", "odir="])
    except getopt.GetoptError:
        print("plot_ts.py -i <input file> -o <output dir>")
        sys.exit(2)
    for opt, arg in opts:
        if opt == "-h":
            print("plot_ts.py -i <input file> -o <output dir>")
            sys.exit()
        elif opt in ("-i", "--idir"):
            in_dir = Path(arg)
        elif opt in ("-o", "--odir"):
            out_dir = Path(arg)
            out_dir.mkdir(parents=True, exist_ok=True)
    proc(in_dir, out_dir)
