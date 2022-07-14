import os
import sys
import getopt
import pytz
from pathlib import Path
import pandas as pd
import salem
import xesmf as xe

from cartopy import crs as ccrs
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter

import matplotlib.pyplot as plt
import seaborn as sns

wrf_nc_dir = Path(os.getenv("PYWRF_NC_DIR"))
gfs_nc_dir = Path(os.getenv("GFS_NC_DIR"))

tz = pytz.timezone("Asia/Manila")
plot_proj = ccrs.PlateCarree()

lon_formatter = LongitudeFormatter(zero_direction_label=True, degree_symbol="")
lat_formatter = LatitudeFormatter(degree_symbol="")

lon_labels = range(120, 130, 5)
lat_labels = range(5, 25, 5)
xlim = (116, 128)
ylim = (5, 20)

var_name = "precip"
var_opts = [
    {
        "name": "wrf-gsmap",
        "title": "WRF-GSMaP 24-hr Total Rainfall (mm)",
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
    {
        "name": "gfs-gsmap",
        "title": "GFS-GSMaP 24-hr Total Rainfall (mm)",
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
]


def plot_map(in_file, out_dir):
    gsmap = salem.open_xr_dataset(in_file)["precip"]
    init_dt_utc = pd.to_datetime(
        "_".join(in_file.name.split("_")[2:4]), format="%Y-%m-%d_%H", utc=True
    )
    init_dt = init_dt_utc.astimezone(tz)
    init_dt_str = init_dt.strftime("%Y-%m-%d %H")
    init_dt_str2 = init_dt.strftime("%Y-%m-%d_%H")

    wrf_nc_file = wrf_nc_dir / f"wrf_{init_dt_utc:%Y-%m-%d_%H}.nc"
    if not wrf_nc_file.is_file():
        print("WRF out file not found")
        return
    wrf_ds = salem.open_xr_dataset(wrf_nc_file)

    wrf_rain = wrf_ds["rain"].isel(time=(wrf_ds.time.dt.day == init_dt_utc.day))
    wrf_rain = wrf_rain.mean("ens").sum("time")
    wrf_rain = wrf_rain.sel(lat=slice(*ylim), lon=slice(*xlim))

    gfs_nc_file = gfs_nc_dir / f"gfs_{init_dt_utc:%Y-%m-%d_%H}_day.nc"
    if not gfs_nc_file.is_file():
        print("GFS file not found")
        return
    gfs_rain = salem.open_xr_dataset(gfs_nc_file)["precip"].isel(time=0)

    regridder = xe.Regridder(gsmap, wrf_rain, "bilinear")
    gsmap_re = regridder(gsmap)
    regridder = xe.Regridder(gfs_rain, wrf_rain, "bilinear")
    gfs_rain_re = regridder(gfs_rain)

    diff_das = [wrf_rain - gsmap_re, gfs_rain_re - gsmap_re]

    for ida, da in enumerate(diff_das):
        levels = var_opts[ida]["levels"]
        colors = var_opts[ida]["colors"]

        fig = plt.figure(figsize=(8, 9), constrained_layout=True)
        ax = plt.axes(projection=plot_proj)
        ax.xaxis.set_major_formatter(lon_formatter)
        ax.yaxis.set_major_formatter(lat_formatter)
        ax.set_xticks(lon_labels, crs=plot_proj)
        ax.set_yticks(lat_labels, crs=plot_proj)

        plt_title = f"{var_opts[ida]['title']}\nfrom {init_dt_str} PHT"
        # plt_annotation = f"GSMaP (gauge calibrated) at {init_dt_str} PHT."

        fig.suptitle(plt_title, fontsize=14)

        p = da.plot.contourf(
            ax=ax,
            transform=plot_proj,
            levels=levels,
            colors=colors,
            add_labels=False,
            extend="both",
            cbar_kwargs=dict(shrink=0.5),
        )

        p.colorbar.ax.set_title(f"[{var_opts[ida]['units']}]", pad=20, fontsize=10)
        ax.coastlines()
        ax.set_extent((*xlim, *ylim))

        # ax.annotate(plt_annotation, xy=(5, -30), xycoords="axes points", fontsize=8)
        ax.annotate(
            "observatory.ph",
            xy=(10, 10),
            xycoords="axes points",
            fontsize=10,
            bbox=dict(boxstyle="square,pad=0.3", alpha=0.5),
            alpha=0.5,
        )

        out_file_pref = var_opts[ida]["name"]
        out_file = out_dir / f"{out_file_pref}-24hr_rain_day0_{init_dt_str2}PHT.png"
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
    plot_map(in_file, out_dir)
