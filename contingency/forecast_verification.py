import os
import sys
import getopt
import pytz
from datetime import timedelta
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import salem
import xesmf as xe

from helpers import (
    calculate_contingency,
    calculate_cont_dry,
    calculate_cont_low,
    calculate_cont_moderate,
    calculate_cont_heavy,
    calculate_cont_extreme,
    cont_table,
)

XLIM = (116, 128)
YLIM = (5, 20)

tz = pytz.timezone("Asia/Manila")

# open netCDF files and extract variables

gsmap_nc_dir = Path(os.getenv("GSMAP_NC_DIR"))
wrf_nc_dir = Path(os.getenv("PYWRF_NC_DIR"))


def plot_panel(conts, init_dt):
    fig_background_color = "white"
    fig_border = "black"
    obs_title = "Observation (GSMaP)"
    fcst_title = "Forecast (WRF)"

    print("Plotting contingency tables...")

    fig, axs = plt.subplots(ncols=3, nrows=2, figsize=(20, 6))
    dt_str1 = init_dt.strftime("%Y-%m-%d %H:00")
    dt_str2 = (init_dt + timedelta(days=1)).strftime("%Y-%m-%d %H:00")
    plt_title = f"Contingency Table from {dt_str1} to {dt_str2} PHT"
    fig.suptitle(plt_title, fontsize=14)

    tab_headers = ["Yes", "No", "Total"]
    tab_header_cols = plt.cm.BuPu(np.full(len(tab_headers), 0.1))
    for ir in range(2):
        for ic in range(3):
            pod, far, sr, cell_text = cont_table(conts[ir][ic]["dat"])
            title_text = f"24-hr {conts[ir][ic]['title']} Rainfall\n"
            footer_text = f"Probability of Detection = {pod}\nFalse Alarm Ratio = {far}\nSuccess Ratio = {sr}"
            axs[ir][ic].get_xaxis().set_visible(False)
            axs[ir][ic].get_yaxis().set_visible(False)
            axs[ir][ic].set_frame_on(False)
            axs[ir][ic].table(
                cellText=cell_text,
                rowLabels=tab_headers,
                rowColours=tab_header_cols,
                rowLoc="center",
                colColours=tab_header_cols,
                colLabels=tab_headers,
                loc="upper center",
            )
            axs[ir][ic].set_title(title_text)
            # Add footer
            axs[ir][ic].text(
                0.5,
                0.35,
                footer_text,
                horizontalalignment="center",
                size=12,
                weight="normal",
            )
            axs[ir][ic].text(
                0.35,
                1.0,
                obs_title,
                horizontalalignment="center",
                size=10,
                weight="normal",
            )
            axs[ir][ic].text(
                -0.11,
                0.65,
                fcst_title,
                horizontalalignment="center",
                size=10,
                weight="normal",
                rotation="vertical",
            )

    # Contingency table legend
    axs[1][1].text(
        0.5,
        0.2,
        "Guide for contingency table",
        horizontalalignment="center",
        size=10,
        weight="normal",
    )
    axs[1][1].text(
        0.4, 0.1, "Observation", horizontalalignment="center", size=8, weight="normal"
    )
    axs[1][1].text(
        0.06,
        -0.18,
        "Forecast",
        horizontalalignment="center",
        size=8,
        weight="normal",
        rotation="vertical",
    )

    axs[1][1].text(
        0.1, -0.05, "Yes", horizontalalignment="center", size=8, weight="normal"
    )
    axs[1][1].text(
        0.1, -0.15, "No", horizontalalignment="center", size=8, weight="normal"
    )
    axs[1][1].text(
        0.1, -0.25, "Total", horizontalalignment="center", size=8, weight="normal"
    )

    axs[1][1].text(
        0.25, 0.05, "Yes", horizontalalignment="center", size=8, weight="normal"
    )
    axs[1][1].text(
        0.51, 0.05, "No", horizontalalignment="center", size=8, weight="normal"
    )
    axs[1][1].text(
        0.78, 0.05, "Total", horizontalalignment="center", size=8, weight="normal"
    )

    axs[1][1].text(
        0.25, -0.05, "HIT", horizontalalignment="center", size=8, weight="heavy"
    )
    axs[1][1].text(
        0.51, -0.05, "FALSE ALARM", horizontalalignment="center", size=8, weight="heavy"
    )
    axs[1][1].text(
        0.78,
        -0.05,
        "FORECAST YES",
        horizontalalignment="center",
        size=8,
        weight="heavy",
    )
    axs[1][1].text(
        0.25, -0.15, "MISS", horizontalalignment="center", size=8, weight="heavy"
    )
    axs[1][1].text(
        0.51,
        -0.15,
        "CORRECT NEGATIVE",
        horizontalalignment="center",
        size=8,
        weight="heavy",
    )
    axs[1][1].text(
        0.78, -0.15, "FORECAST NO", horizontalalignment="center", size=8, weight="heavy"
    )
    axs[1][1].text(
        0.25,
        -0.25,
        "OBSERVED YES",
        horizontalalignment="center",
        size=8,
        weight="heavy",
    )
    axs[1][1].text(
        0.51, -0.25, "OBSERVED NO", horizontalalignment="center", size=8, weight="heavy"
    )
    axs[1][1].text(
        0.78,
        -0.25,
        "TOTAL GRIDPTS",
        horizontalalignment="center",
        size=8,
        weight="heavy",
    )
    # axs[1][1].add_patch(patch.Rectangle((0,0), 3, 3, edgecolor='black', facecolor='none',zorder=300))
    return fig


def proc(out_dir):
    yyyymmdd = out_dir.parent.name
    zz = out_dir.name

    init_dt_utc = pd.to_datetime(f"{yyyymmdd}_{zz}", format="%Y%m%d_%H", utc=True)
    init_dt_utc_str = init_dt_utc.strftime("%Y-%m-%d_%H")
    init_dt = init_dt_utc.astimezone(tz)
    init_dt_str = init_dt.strftime("%Y-%m-%d_%H")

    gsmap_file = gsmap_nc_dir / f"gsmap_gauge_{init_dt_utc:%Y-%m-%d_%H}_day.nc"
    gsmap = salem.open_xr_dataset(gsmap_file)["precip"]

    wrf_nc_file = wrf_nc_dir / f"wrf_{init_dt_utc:%Y-%m-%d_%H}.nc"
    if not wrf_nc_file.is_file():
        print("WRF out file not found")
        return
    wrf_ds = salem.open_xr_dataset(wrf_nc_file)

    wrf_rain = wrf_ds["rain"].isel(time=(wrf_ds.time.dt.day == init_dt_utc.day))
    wrf_rain = wrf_rain.sel(lat=slice(*YLIM), lon=slice(*XLIM))
    wrf_rain = wrf_rain.mean("ens").sum("time")

    regridder = xe.Regridder(gsmap, wrf_rain, "bilinear")
    gsmap_re = regridder(gsmap)

    print("Getting contingency function for total rainfall ...")
    cont = calculate_contingency(wrf_rain, gsmap_re)
    # save contingency table plot as netCDF file
    print("Saving contingency table to netCDF file...")
    da_out = wrf_rain.copy()
    da_out.values = cont
    da_out.name = "cont"
    da_out.attrs["long_name"] = "Contingency Table (WRF VERSUS GSMaP)"
    da_out.attrs["units"] = "1"
    da_out.attrs["level_desc"] = "Surface"
    da_out.attrs["var_desc"] = "Contingency Table"
    out_file = out_dir / f"contingency_{init_dt_str}PHT.nc"
    da_out.to_netcdf(out_file)

    print("Getting contingency function for dry rainfall category...")
    cont_dry = calculate_cont_dry(wrf_rain, gsmap_re)

    print("Getting contingency function for low rainfall category...")
    cont_low = calculate_cont_low(wrf_rain, gsmap_re)

    print("Getting contingency function for moderate rainfall category...")
    cont_mod = calculate_cont_moderate(wrf_rain, gsmap_re)

    print("Getting contingency function for heavy rainfall category...")
    cont_heavy = calculate_cont_heavy(wrf_rain, gsmap_re)

    print("Getting contingency function for extreme rainfall category...")
    cont_ext = calculate_cont_extreme(wrf_rain, gsmap_re)

    conts = [
        [
            {"dat": cont_dry, "title": "Dry"},
            {"dat": cont_low, "title": "Low"},
            {"dat": cont_mod, "title": "Moderate"},
        ],
        [
            {"dat": cont_heavy, "title": "Heavy"},
            {"dat": cont_ext, "title": "Extreme"},
            {"dat": cont, "title": "Total"},
        ],
    ]
    fig = plot_panel(conts, init_dt)

    out_file = out_dir / f"contingency_{init_dt_str}PHT.png"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_file, dpi=300, bbox_inches="tight")
    plt.close("all")
    print("Done!")


if __name__ == "__main__":
    out_dir = Path("")
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ho:", ["odir="])
    except getopt.GetoptError:
        print("forecast_verification.py -o <output dir>")
        sys.exit(2)
    for opt, arg in opts:
        if opt == "-h":
            print("forecast_verification.py -o <output dir>")
            sys.exit()
        elif opt in ("-o", "--odir"):
            out_dir = Path(arg)
            out_dir.mkdir(parents=True, exist_ok=True)
    proc(out_dir)
