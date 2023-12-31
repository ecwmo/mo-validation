# Title: Produce weekly average of daily contigency tables
# Author: Kevin Henson
# Last edited: July 27, 2022

# !/usr/bin/env python
# coding: utf-8

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# import datetime as dt
import calendar
from datetime import timedelta
from helpers import (
    calculate_contingency,
    calculate_cont_dry,
    calculate_cont_low,
    calculate_cont_moderate,
    calculate_cont_heavy,
    calculate_cont_extreme,
)
import os.path
import os
import salem
import xesmf as xe
import pytz
import sys
import getopt

# initialize dataframe


def init_df():

    df = pd.DataFrame(
        0,
        index=["total", "dry", "low", "mod", "heavy", "ext"],
        columns=[
            "hit",
            "f_alarm",
            "miss",
            "c_neg",
            "fcst_yes",
            "fcst_no",
            "obs_yes",
            "obs_no",
            "total_obs",
            "total_fcst",
            "pod",
            "far",
            "sr",
            "pod_ave_offset",
            "far_sr_ave_offset",
        ],
    )
    return df


def weekAverage(date_today, out_dir):

    df = init_df()

    XLIM = (116, 128)
    YLIM = (5, 20)

    # initialize functions for loop
    funcs = [
        calculate_contingency,
        calculate_cont_dry,
        calculate_cont_low,
        calculate_cont_moderate,
        calculate_cont_heavy,
        calculate_cont_extreme,
    ]

    print("Computing week average contingency tables ...")

    # days counter to account for missing data
    c = 0

    # for logging categories of values that need offsetting
    offset_pod = []
    offset_far_sr = []

    # Set dates

    yyyymmdd_orig = out_dir.parent.name
    zz = out_dir.name

    print(yyyymmdd_orig)
    # init_dt_utc = pd.to_datetime(f"{date_today}", format="%Y%m%d_%H", utc=True)
    init_dt_utc = date_today
    # init_dt_str = init_dt.strftime("%Y-%m-%d_%H")

    # Loop through last 7 days
    for i in range(0, 7):
        yyyymmdd = init_dt_utc - timedelta(days=i)

        # open netCDF files and extract variables

        wrf_nc_file = Path(os.getenv("PYWRF_NC_DIR")) / f"wrf_{yyyymmdd:%Y-%m-%d_%H}.nc"

        gsmap_file = (
            Path(os.getenv("GSMAP_NC_DIR"))
            / f"gsmap_gauge_{yyyymmdd:%Y-%m-%d_%H}_day.nc"
        )

        print(wrf_nc_file)

        # Check if file exists
        if not (Path(wrf_nc_file).is_file()):
            print("File " + str(wrf_nc_file) + " does not exist")
            continue
        elif not (Path(gsmap_file).is_file()):
            print("File " + str(gsmap_file) + " does not exist")
            continue
        else:

            wrf_ds = salem.open_xr_dataset(wrf_nc_file)
            gsmap = salem.open_xr_dataset(gsmap_file)["precip"]

            wrf_rain = wrf_ds["rain"].isel(time=(wrf_ds.time.dt.day == yyyymmdd.day))
            wrf_rain = wrf_rain.sel(lat=slice(*YLIM), lon=slice(*XLIM))
            print(wrf_rain)
            wrf_rain = wrf_rain.mean("ens").sum("time")

            regridder = xe.Regridder(wrf_rain, gsmap, "bilinear")
            wrf_rain_re = regridder(wrf_rain)

            c += 1
            wrf = wrf_rain_re
            # wrf = d1.variables["p24"][:, :]

            # gsmap = d2.variables["rsum"][:, :]

            for j, cat in enumerate(df.index):

                CONT = funcs[j](wrf[:, :], gsmap[:, :])

                # Contingency table values

                hit = np.count_nonzero(CONT == 4)
                f_alarm = np.count_nonzero(CONT == 3)
                miss = np.count_nonzero(CONT == 2)
                c_neg = np.count_nonzero(CONT == 1)

                df.at[cat, "hit"] += hit
                df.at[cat, "f_alarm"] += f_alarm
                df.at[cat, "miss"] += miss
                df.at[cat, "c_neg"] += c_neg

                df.at[cat, "fcst_yes"] += hit + f_alarm
                df.at[cat, "fcst_no"] += miss + c_neg
                df.at[cat, "obs_yes"] += hit + miss
                df.at[cat, "obs_no"] += f_alarm + c_neg
                df.at[cat, "total_obs"] += (
                    df.at["total", "obs_yes"] + df.at["total", "obs_no"]
                )
                df.at[cat, "total_fcst"] += (
                    df.at["total", "fcst_yes"] + df.at["total", "fcst_no"]
                )

                # Forecast metrics
                # Check for division by zero
                if (hit + miss) != 0 and (hit + f_alarm) != 0:

                    df.at[cat, "pod"] += (hit / (hit + miss)) * 100
                    df.at[cat, "far"] += (f_alarm / (hit + f_alarm)) * 100
                    df.at[cat, "sr"] += (hit / (hit + f_alarm)) * 100

                # log offset for weekly averaging if there is division by zero
                elif (hit + miss) == 0:
                    df.at[cat, "pod_ave_offset"] += 1
                    offset_pod.append(cat)
                elif (hit + f_alarm) == 0:
                    df.at[cat, "far_sr_ave_offset"] += 1
                    offset_far_sr.append(cat)

    # Save offsets
    df_offsets = df[df.columns[13:15]]

    # Compute week average except offset columns
    df = df[df.columns[:13]] / c
    df = pd.concat([df, df_offsets], axis=1)

    # Divide pod,far, or sr by c-offset to account for days with division by 0
    # for pod, far, and sr
    for cat_offset in offset_pod:
        df.at[cat_offset, "pod"] *= c / (c - df.at[cat_offset, "pod_ave_offset"])
        # print('offset averaging of pod '+ cat_offset + ' by '
        #  + str(df.at[cat_offset, 'pod_ave_offset']))

    for cat_offset in offset_far_sr:
        df.at[cat_offset, "far"] *= c / (c - df.at[cat_offset, "far_sr_ave_offset"])
        df.at[cat_offset, "sr"] *= c / (c - df.at[cat_offset, "far_sr_ave_offset"])
        # print('offset averaging of far and sar '+ cat_offset + ' by '
        #  + str(df.at[cat_offset, 'far_sr_ave_offset']))

    return out_dir, yyyymmdd, zz, df[df.columns[:13]]


def plot_cont(outdir, date, init_var, df_var, duration):

    date_var = str(date)

    # figure plot settings

    plt.figure(
        linewidth=2,
        edgecolor="black",
        facecolor="white",
        #           tight_layout={'pad':1},
        dpi=300,
    )
    plt.rcParams["figure.figsize"] = (20, 6)
    fig, ((ax1, ax2, ax3), (ax4, ax5, ax6)) = plt.subplots(ncols=3, nrows=2)
    ax_list = [ax1, ax2, ax3, ax4, ax5, ax6]

    # plotting variable settings
    obs_title = "Observation (GSMaP)"
    fcst_title = "Forecast (WRF)"

    # loop through rainfall categories to produce contigency tables
    for i, cat in enumerate(df_var.index):

        hit = round(df_var.at[cat, "hit"])
        miss = round(df_var.at[cat, "miss"])
        f_alarm = round(df_var.at[cat, "f_alarm"])
        c_neg = round(df_var.at[cat, "c_neg"])
        obs_yes = round(df_var.at[cat, "obs_yes"])
        obs_no = round(df_var.at[cat, "obs_no"])
        fcst_yes = round(df_var.at[cat, "fcst_yes"])
        fcst_no = round(df_var.at[cat, "fcst_no"])
        totalobs = obs_yes + obs_no

        # Format to whole number
        pod = "{:0.2f} %".format(df_var.at[cat, "pod"])
        far = "{:0.2f} %".format(df_var.at[cat, "far"])
        sr = "{:0.2f} %".format(df_var.at[cat, "sr"])

        # Prepare contingency table
        data = [
            ["Yes", "No", "Total"],
            ["Yes", int(f"{hit}"), int(f"{f_alarm}"), int(f"{fcst_yes}")],
            ["No", int(f"{miss}"), int(f"{c_neg}"), int(f"{fcst_no}")],
            ["Total", int(f"{obs_yes}"), int(f"{obs_no}"), int(f"{totalobs}")],
        ]
        column_headers = data.pop(0)
        row_headers = [x.pop(0) for x in data]
        cell_text = []
        for row in data:
            cell_text.append([f"{x}" for x in row])

        rcolors = plt.cm.BuPu(np.full(len(row_headers), 0.1))
        ccolors = plt.cm.BuPu(np.full(len(column_headers), 0.1))

        # Adjust date for label
        plot_label = str(date - timedelta(days=6))

        if duration == "Week":
            x_range = pd.date_range(
                f"{plot_label}-{init_var}", periods=169, freq="H"
            ).strftime("%Y-%m-%d %H:00")
            label = f"from {plot_label} {init_var}:00 to {x_range[168]} PHT"
            label_dir = f"{date_var}_{init_var}PHT.png"
        elif duration == "Month":
            label = f"{plot_label[0:7]}"
            label_dir = f"{plot_label[0:7]}.png"

        title_text = f"{duration} Average Contingency Table ({cat} rainfall)\n{label}"
        footer_text = (
            f"Probability of Detection = {pod}\nFalse Alarm Ratio = {far}"
            f"\n Success Ratio = {sr}"
        )

        ax = ax_list[i]

        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
        ax.set_frame_on(False)
        ax.table(
            cellText=cell_text,
            rowLabels=row_headers,
            rowColours=rcolors,
            rowLoc="center",
            colColours=ccolors,
            colLabels=column_headers,
            loc="upper center",
        )
        ax.set_title(title_text + "\n")
        # Add footer
        ax.text(
            0.5,
            0.35,
            footer_text,
            horizontalalignment="center",
            size=12,
            weight="normal",
        )
        ax.text(
            0.35, 1.0, obs_title, horizontalalignment="center", size=10, weight="normal"
        )
        ax.text(
            -0.11,
            0.65,
            fcst_title,
            horizontalalignment="center",
            size=10,
            weight="normal",
            rotation="vertical",
        )

    # Contingency table legend
    ax5.text(
        0.5,
        0.2,
        "Guide for contingency table",
        horizontalalignment="center",
        size=10,
        weight="normal",
    )
    ax5.text(
        0.4, 0.1, "Observation", horizontalalignment="center", size=8, weight="normal"
    )
    ax5.text(
        0.06,
        -0.18,
        "Forecast",
        horizontalalignment="center",
        size=8,
        weight="normal",
        rotation="vertical",
    )

    ax5.text(0.1, -0.05, "Yes", horizontalalignment="center", size=8, weight="normal")
    ax5.text(0.1, -0.15, "No", horizontalalignment="center", size=8, weight="normal")
    ax5.text(0.1, -0.25, "Total", horizontalalignment="center", size=8, weight="normal")

    ax5.text(0.25, 0.05, "Yes", horizontalalignment="center", size=8, weight="normal")
    ax5.text(0.51, 0.05, "No", horizontalalignment="center", size=8, weight="normal")
    ax5.text(0.78, 0.05, "Total", horizontalalignment="center", size=8, weight="normal")

    ax5.text(0.25, -0.05, "HIT", horizontalalignment="center", size=8, weight="heavy")
    ax5.text(
        0.51, -0.05, "FALSE ALARM", horizontalalignment="center", size=8, weight="heavy"
    )
    ax5.text(
        0.78,
        -0.05,
        "FORECAST YES",
        horizontalalignment="center",
        size=8,
        weight="heavy",
    )
    ax5.text(0.25, -0.15, "MISS", horizontalalignment="center", size=8, weight="heavy")
    ax5.text(
        0.51,
        -0.15,
        "CORRECT NEGATIVE",
        horizontalalignment="center",
        size=8,
        weight="heavy",
    )
    ax5.text(
        0.78, -0.15, "FORECAST NO", horizontalalignment="center", size=8, weight="heavy"
    )
    ax5.text(
        0.25,
        -0.25,
        "OBSERVED YES",
        horizontalalignment="center",
        size=8,
        weight="heavy",
    )
    ax5.text(
        0.51, -0.25, "OBSERVED NO", horizontalalignment="center", size=8, weight="heavy"
    )
    ax5.text(
        0.78,
        -0.25,
        "TOTAL GRIDPTS",
        horizontalalignment="center",
        size=8,
        weight="heavy",
    )

    out_file = Path(outdir) / f"contingency_{duration}Average_{label_dir}"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file = str(out_file)
    plt.savefig(out_file, dpi=300, bbox_inches="tight")
    print("Saved " + out_file)


# Get sundays of month


def allsundays_compute_month_average(date_var, outdir):
    last_day_of_prev_month = date_var.replace(day=1) - timedelta(days=1)
    date_var = date_var.replace(day=1) - timedelta(days=last_day_of_prev_month.day)

    d = date_var
    d += timedelta(days=6 - d.weekday())

    # Counter for averaging
    c = 0

    # intialize dataframe
    df = init_df()
    df = df[df.columns[:13]]

    print("Computing month average contingency tables ...")

    # Set allowance for weeks that overlap between months
    if d.day > 4:
        # print("yes")
        # print(d)
        d_str = d.strftime("%Y%m%d")
        df += weekAverage(d, outdir)[-1]
        c += 1

    while d.month == date_var.month:
        d += timedelta(days=7)

        # Set allowance for weeks that overlap between months
        if d.month == date_var.month or d.day < 3:
            print("yes")
            d_str = d.strftime("%Y%m%d")
            outdir, today, init, df_var = weekAverage(d, outdir)
            df += df_var
            c += 1

    return outdir, today, init, (df / c)


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

    yyyymmdd = out_dir.parent.name
    zz = out_dir.name

    print(yyyymmdd)
    print(zz)

    init_dt_utc = pd.to_datetime(f"{yyyymmdd}_{zz}", format="%Y%m%d_%H", utc=True)
    day_name = calendar.day_name[init_dt_utc.weekday()]

    print(init_dt_utc)
    print(day_name)
    # Run 7 day average
    if day_name == "Sunday":

        print("Computing week average of daily contingency tables")

        d_str = init_dt_utc.strftime("%Y%m%d")
        outdir, today_var, init_var, df_var = weekAverage(d_str, out_dir)
        plot_cont(outdir, today_var, init_var, df_var, "Week")

        print("Done with week average!")

    # set monthly averaging to occur every 5th of month
    # to give allowance for weeks that overlap into first
    # few days of month
    if init_dt_utc.day == 5:
        print("Getting month average contingency table from weekly averages")
        outdir = Path(f"/home/modelman/forecast/output/validation/{yyyymmdd}/00")
        _, today_var, init_var, df_var = allsundays_compute_month_average(
            init_dt_utc, out_dir
        )

        plot_cont(
            outdir,
            today_var,
            init_var,
            df_var,
            "Month",
        )

        print("Done with month average!")
