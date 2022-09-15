# Description: Plot daily difference maps for WRF and GFS vs GSMAP
# Author: Emilio Gozo and Kevin Henson
# Last edited: Sept. 15, 2022

from mimetypes import init
import os
import sys
import getopt
import pytz
from pathlib import Path
import pandas as pd
import salem
import xesmf as xe

import matplotlib.pyplot as plt
import seaborn as sns

from helpers.plot import plot_map, XLIM, YLIM

# Access environment variables for directories
wrf_nc_dir = Path(os.getenv("PYWRF_NC_DIR"))
gfs_nc_dir = Path(os.getenv("GFS_NC_DIR"))

tz = pytz.timezone("Asia/Manila")

# Set difference map names
names = [
    "wrf_ensmean-gsmap",
    "wrf_run1-gsmap",
    "wrf_run2-gsmap",
    "wrf_run3-gsmap",
    "gfs-gsmap",
]

# Set titles
post_title = " - GSMaP 24-hr Total Rainfall (mm)"
titles = ["WRF ensemble mean", "WRF run 1", "WRF run 2", "WRF run 3", "GFS"]


def main(in_file, out_dir):

    # Access GSMAP file
    gsmap = salem.open_xr_dataset(in_file)["precip"]

    # Set date to be validated
    init_dt_utc_start = pd.to_datetime(
        "_".join(in_file.name.split("_")[2:4]), format="%Y-%m-%d_%H", utc=True
    )
    init_dt_start = init_dt_utc_start.astimezone(tz)
    init_dt_str_start = init_dt_start.strftime("%Y-%m-%d %H")

    # Loop through previous 5 days model initialization
    for day in range(5):

        # Set plot format variables
        var_opts = []
        for i, name in enumerate(names):

            var_opts.append(
                {
                    "name": name,
                    "title": f"{titles[i]}{post_title}",
                    "units": "mm",
                    "levels": range(-50, 51, 10),
                    "colors": sns.blend_palette(
                        [
                            "#8b4513",
                            "#f0e68c",
                            "#ffffff",
                            "#48d1cc",
                            "#000080",
                        ],
                        n_colors=12,
                    ),
                },
            )

        # Set adjusted date
        init_dt_utc = init_dt_utc_start - pd.Timedelta(day, "d")
        init_dt = init_dt_utc.astimezone(tz)
        init_dt_str = init_dt.strftime("%Y-%m-%d %H")
        init_dt_str2 = init_dt.strftime("%Y-%m-%d_%H")

        # Open wrf file
        wrf_nc_file = wrf_nc_dir / f"wrf_{init_dt_utc:%Y-%m-%d_%H}.nc"
        if not wrf_nc_file.is_file():
            print(wrf_nc_file)
            print("WRF out file not found")
            return
        wrf_ds = salem.open_xr_dataset(wrf_nc_file)

        wrf_rain = wrf_ds["rain"].isel(
            time=(wrf_ds.time.dt.day == init_dt_utc_start.day)
        )
        wrf_rain = wrf_rain.sel(lat=slice(*YLIM), lon=slice(*XLIM))

        # Compute ensemble mean and member daily totals
        wrf_rain_ens = wrf_rain.mean("ens").sum("time")
        wrf_rain_run1 = wrf_rain.sel(ens=0).sum("time")
        wrf_rain_run2 = wrf_rain.sel(ens=1).sum("time")
        wrf_rain_run3 = wrf_rain.sel(ens=2).sum("time")

        # Access GFS file
        gfs_nc_file = gfs_nc_dir / f"gfs_{init_dt_utc:%Y-%m-%d_%H}_day.nc"
        print(gfs_nc_file)
        if not gfs_nc_file.is_file():
            print("GFS file not found")
            return

        gfs_rain = salem.open_xr_dataset(gfs_nc_file)["precip"].isel(time=day)

        # Compute difference
        wrfout_list = [wrf_rain_ens, wrf_rain_run1, wrf_rain_run2, wrf_rain_run3]
        diff_das = []
        for wrfout in wrfout_list:
            regridder = xe.Regridder(wrfout, gsmap, "bilinear")
            wrfout_temp = regridder(wrfout)
            diff_das.append(wrfout_temp - gsmap)

        regridder = xe.Regridder(gsmap, gfs_rain, "bilinear")
        gsmap_re_gfs = regridder(gsmap)

        diff_das.append(gfs_rain - gsmap_re_gfs)

        # Plot
        for ida, da in enumerate(diff_das):
            plt_opts = var_opts[ida]
            plt_opts[
                "title"
            ] = f"{plt_opts['title']}\n initalized {init_dt_str} PHT\n valid from {init_dt_str_start} PHT"
            # plt_opts["annotation"] = f"GSMaP (gauge calibrated) at {init_dt_str} PHT."
            fig = plot_map(da, var_opts[ida])

            out_file_pref = var_opts[ida]["name"]
            out_file = (
                out_dir / f"{out_file_pref}-24hr_rain_day{day+1}_{init_dt_str2}PHT.png"
            )
            fig.savefig(out_file, bbox_inches="tight", dpi=300)
            plt.close("all")


if __name__ == "__main__":
    in_file = Path("dat")
    out_dir = Path("img")
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hi:o:", ["ifile=", "odir="])
    except getopt.GetoptError:
        print("plot_24hr_rain_diff.py -i <input file> -o <output dir>")
        sys.exit(2)
    for opt, arg in opts:
        if opt == "-h":
            print("plot_24hr_rain_diff.py -i <input file> -o <output dir>")
            sys.exit()
        elif opt in ("-i", "--ifile"):
            in_file = Path(arg)
        elif opt in ("-o", "--odir"):
            out_dir = Path(arg)
            out_dir.mkdir(parents=True, exist_ok=True)
    main(in_file, out_dir)
