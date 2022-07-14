import sys
import getopt
import pytz
from datetime import timedelta
from pathlib import Path
import pandas as pd
import salem

from cartopy import crs as ccrs
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter

import matplotlib.pyplot as plt

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
        "title": "GFS 24-hr Total Rainfall (mm/day)",
        "units": "mm/dy",
        "levels": [5, 10, 20, 30, 50, 100, 150, 200, 250],
        "colors": [
            "#ffffff",
            "#0064ff",
            "#01b4ff",
            "#32db80",
            "#9beb4a",
            "#ffeb00",
            "#ffb302",
            "#ff6400",
            "#eb1e00",
            "#af0000",
        ],
    },
    {
        "title": "GFS 48-hr Total Rainfall (mm/2 days)",
        "units": "mm/2dy",
        "levels": [5, 10, 20, 30, 50, 100, 150, 200, 250],
        "colors": [
            "#ffffff",
            "#0064ff",
            "#01b4ff",
            "#32db80",
            "#9beb4a",
            "#ffeb00",
            "#ffb302",
            "#ff6400",
            "#eb1e00",
            "#af0000",
        ],
    },
    {
        "title": "GFS 72-hr Total Rainfall (mm/3 days)",
        "units": "mm/3dy",
        "levels": [5, 10, 20, 30, 50, 100, 150, 200, 250],
        "colors": [
            "#ffffff",
            "#0064ff",
            "#01b4ff",
            "#32db80",
            "#9beb4a",
            "#ffeb00",
            "#ffb302",
            "#ff6400",
            "#eb1e00",
            "#af0000",
        ],
    },
]


def plot_map(in_file, out_dir):
    ds = salem.open_xr_dataset(in_file)

    init_dt = pd.to_datetime(ds.time.values[0], utc=True).astimezone(tz)
    init_dt_str = init_dt.strftime("%Y-%m-%d %H")
    init_dt_str2 = init_dt.strftime("%Y-%m-%d_%H")

    da = None
    for it in range(3):
        _da = ds[var_name].isel(time=it)
        if it == 0:
            da = _da.copy()
            continue
        else:
            da.values = da.values + _da.values

        levels = var_opts[it]["levels"]
        colors = var_opts[it]["colors"]

        fig = plt.figure(figsize=(8, 9), constrained_layout=True)
        ax = plt.axes(projection=plot_proj)
        ax.xaxis.set_major_formatter(lon_formatter)
        ax.yaxis.set_major_formatter(lat_formatter)
        ax.set_xticks(lon_labels, crs=plot_proj)
        ax.set_yticks(lat_labels, crs=plot_proj)

        dt1 = pd.to_datetime(_da.time.values, utc=True).astimezone(tz)
        # dt1_str = dt1.strftime("%Y-%m-%d %H")
        dt2 = dt1 + timedelta(days=1)
        dt2_str = dt2.strftime("%Y-%m-%d %H")
        plt_title = (
            f"{var_opts[it]['title']}\nValid from {init_dt_str} to {dt2_str} PHT"
        )
        plt_annotation = f"GFS initialized at {init_dt_str} PHT."

        fig.suptitle(plt_title, fontsize=14)

        p = da.plot(
            ax=ax,
            transform=plot_proj,
            levels=levels,
            colors=colors,
            add_labels=False,
            extend="both",
            cbar_kwargs=dict(shrink=0.5),
        )

        p.colorbar.ax.set_title(f"[{var_opts[it]['units']}]", pad=20, fontsize=10)
        ax.coastlines()
        ax.set_extent((*xlim, *ylim))

        ax.annotate(plt_annotation, xy=(5, -30), xycoords="axes points", fontsize=8)
        ax.annotate(
            "observatory.ph",
            xy=(10, 10),
            xycoords="axes points",
            fontsize=10,
            bbox=dict(boxstyle="square,pad=0.3", alpha=0.5),
            alpha=0.5,
        )

        out_file = out_dir / f"gfs-{24*(it+1)}hr_rain_day0_{init_dt_str2}PHT.png"
        fig.savefig(out_file, bbox_inches="tight", dpi=300)
        plt.close("all")


if __name__ == "__main__":
    in_file = Path("dat")
    out_dir = Path("img")
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hi:o:", ["ifile=", "odir="])
    except getopt.GetoptError:
        print("plot_gfs_24hr_rain.py -i <input file> -o <output dir>")
        sys.exit(2)
    for opt, arg in opts:
        if opt == "-h":
            print("plot_gfs_24hr_rain.py -i <input file> -o <output dir>")
            sys.exit()
        elif opt in ("-i", "--ifile"):
            in_file = Path(arg)
        elif opt in ("-o", "--odir"):
            out_dir = Path(arg)
            out_dir.mkdir(parents=True, exist_ok=True)
    plot_map(in_file, out_dir)
