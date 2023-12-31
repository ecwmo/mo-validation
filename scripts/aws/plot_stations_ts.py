# Description: 5-day time series comparison
# Author: Kevin Henson
# Last edit: May 19, 2023

import sys
import getopt
import pytz
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
from matplotlib.legend import Legend

from get_5day_gsmap_aws_wrf import get_5day_gsmap_aws_wrf


tz = pytz.timezone("Asia/Manila")


# Define function for plotting
def plot_comparison(dt, ax, var, label, data_aws, data_wrf, ymin, data_gsmap=None):
    print("plotting " + var + " time series plots...")

    data_aws = np.array(data_aws, dtype=float)
    data_gsmap = np.array(data_gsmap, dtype=float)

    wrf_ensmean = data_wrf[f"{var}_ensmean"]
    indices = range(len(wrf_ensmean))
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
    x_range_for_shading = pd.date_range(
        date_var_str + "-08", periods=121, freq="H"
    ).strftime("%a %H")

    if var == "rain":
        w = 0.2

        # Check if data exists/is complete
        if len(data_aws) == 120:
            leg_items.append(
                ax.bar(
                    indices - width,
                    data_aws,
                    edgecolor="black",
                    facecolor="black",
                    width=w,
                    zorder=2,
                )
            )

            labels1.append("AWS")

        # Check if data exists/is complete
        if len(wrf_ensmean) == 120:
            leg_items.append(
                ax.bar(
                    indices,
                    wrf_ensmean,
                    edgecolor="C0",
                    facecolor="C0",
                    width=w,
                    zorder=2,
                )
            )

            labels1.append("WRF ensmean")

        # Check if data exists/is complete
        if len(data_gsmap) == 120:
            leg_items.append(
                ax.bar(
                    indices + width,
                    data_gsmap,
                    edgecolor="red",
                    facecolor="red",
                    width=w,
                    zorder=2,
                )
            )

            labels1.append("GSMAP")

        ax.legend(
            leg_items,
            labels1,
            framealpha=0.5,
            frameon=True,
            loc="upper right",
            prop={"size": 24},
        )

    else:
        # Check if data exists/is complete
        if len(data_aws) == 120:
            ax.plot(
                indices,
                data_aws,
                c="k",
                marker="",
                linewidth=4,
                label="AWS",
                zorder=100,
            )

        # List variable ensemble members and mean in json file
        if var == "temp":
            starts_with_var = [x for x in data_wrf.columns if x.startswith(f"{var}_")]
        else:
            starts_with_var = [x for x in data_wrf.columns if x.startswith(f"{var}")]

        # Loop through ensemble
        for i, var_name in enumerate(starts_with_var):
            data = data_wrf[var_name]
            # Check if data exists/is complete
            if len(data) == 120:
                var_label = var_name.split("_")[-1]
                # put ensmean "on top"
                if var_label == "ensmean":
                    ax.plot(
                        indices,
                        data,
                        c=f"C{i}",
                        marker="",
                        linewidth=4,
                        label=f"WRF {var_label}",
                        zorder=99,
                    )
                else:
                    ax.plot(
                        indices,
                        data,
                        c=f"C{i}",
                        marker="",
                        linewidth=4,
                        label=f"WRF {var_label}",
                    )

            ax.legend(
                framealpha=0.5,
                frameon=True,
                loc="lower center",
                prop={"size": 24},
                ncol=len(starts_with_var) + 1,
            )

    xmin1, xmax1 = ax.get_xlim()
    ymin1, ymax1 = ax.get_ylim()
    yrange = ymax1 - ymin1

    # Define function for plot shading
    def plot_shading(shading):
        labels = list(shading.keys())
        for cat in labels:
            leg_items2.append(
                ax.fill_between(
                    x_range_for_shading,
                    shading[cat][1],
                    shading[cat][2],
                    color=shading[cat][0],
                    alpha=0.5,
                    zorder=1,
                )
            )
            labels2.append(cat)

    # Rain-specific plotting parameters
    if var == "rain":
        shading = {
            "Heavy": ["yellow", 7.5, 15, "(7.5-15 mm/hr)"],
            "Intense": ["orange", 15, 30, "(15-30 mm/hr)"],
            "Torrential": ["red", 30, ymax1 + yrange * 0.1, "(> 30 mm/hr)"],
        }

        plot_shading(shading)

    # Heat index-specific plotting parameters
    if var == "hi":
        shading = {
            "Caution": ["#EFE685", 27, 32, "(27-32 \N{DEGREE SIGN}C)"],
            "Extreme Caution": ["#FF8C00", 32, 41, "(32-41 \N{DEGREE SIGN}C)"],
            "Danger": ["#B3211A", 41, 54, "(41-54 \N{DEGREE SIGN}C)"],
            "Extreme Danger": [
                "#9A27CF",
                54,
                ymax1 + yrange * 0.1,
                "(> 54 \N{DEGREE SIGN}C)",
            ],
        }
        plot_shading(shading)

    # get dates for x-axis labels
    x_range = pd.date_range(date_var_str + "-08", periods=121, freq="H").strftime("%H")
    x_range2 = pd.date_range(date_var_str + "-08", periods=121, freq="H").strftime(
        "%a "
    )

    x_tick_labels = []
    for i, t in enumerate(x_range):
        if t == "02" or i == 0:
            x_tick_labels.append(x_range[i] + "\n" + x_range2[i])
        else:
            x_tick_labels.append(x_range[i])
    x_tick_labels = np.array(x_tick_labels)

    ax.set_xticks(np.arange(0, len(x_range) + 1, 3))

    plot_range = yrange * 1.2
    if plot_range < 30:
        increment = 2.5
    elif plot_range > 60:
        increment = 10
    else:
        increment = 5

    for i, _ in enumerate(np.arange(ymin, ymax1, increment)):
        ax.axhline(
            y=ymin + increment * i,
            xmin=xmin1,
            xmax=xmax1,
            linestyle="dotted",
            color="gray",
            zorder=0,
        )

    def round_down(num, divisor):
        return num - (num % divisor)

    if var == "rain":
        ax.set_ylim([0, ymax1 + yrange * 0.1])
    else:
        ax.set_ylim([round_down(ymin1 - yrange * 0.1, 5), ymax1 + yrange * 0.1])
    ax.set_xlim([-1, 121])
    ax.tick_params(axis="y", labelsize=24)
    ax.set_xticklabels(x_tick_labels[np.arange(0, len(x_range) + 1, 3)])

    ax.tick_params(axis="x", labelsize=20)

    for tick_label in ax.xaxis.get_ticklabels()[1::2]:
        tick_label.set_visible(False)

    ax.set_ylabel(label, size=24, color="black")

    if var == "rain":
        leg = Legend(
            ax,
            leg_items2,
            labels2,
            framealpha=0.5,
            frameon=False,
            loc=[0.7, -0.22],
            title="Shading",
            prop={"size": 16},
            ncol=len(labels2),
        )
        ax.add_artist(leg)
        plt.setp(leg.get_title(), fontsize="16")

    if var == "hi":
        leg = Legend(
            ax,
            leg_items2,
            labels2,
            framealpha=0.5,
            frameon=False,
            loc=[0.5, -0.305],
            title="Shading",
            prop={"size": 16},
            ncol=len(labels2),
        )
        ax.add_artist(leg)
        plt.setp(leg.get_title(), fontsize="16")


def proc(out_dir):
    yyyymmdd = out_dir.parent.name
    zz = out_dir.name

    init_dt = pd.to_datetime(
        f"{yyyymmdd}_{zz}", format="%Y%m%d_%H", utc=True
    ).astimezone(tz)
    init_dt_str = init_dt.strftime("%Y-%m-%d_%H")

    dt = init_dt.date()

    station_list = pd.read_csv("stations_lufft.csv")

    # Loop through stations
    for i, stn in station_list.iterrows():
        df_wrf, df_aws, df_gsmap, dt_var_str = get_5day_gsmap_aws_wrf(dt, stn)

        # Plotting for each station
        plt.figure(dpi=300)
        plt.rcParams["figure.figsize"] = (20, 24)

        fig, (ax1, ax2, ax3, ax4) = plt.subplots(ncols=1, nrows=4)

        plot_comparison(
            dt,
            ax1,
            "rain",
            "Rainfall (mm/hr)",
            df_aws["rr"],
            df_wrf,
            0,
            df_gsmap["precip"],
        )
        plot_comparison(
            dt,
            ax2,
            "temp",
            "Temperature (C\N{DEGREE SIGN})",
            df_aws["temp"],
            df_wrf,
            15,
        )
        plot_comparison(
            dt, ax3, "rh", "Relative Humidity (%)", df_aws["rh"], df_wrf, 10
        )
        plot_comparison(
            dt,
            ax4,
            "hi",
            "Heat Index (C\N{DEGREE SIGN})",
            df_aws["hi"],
            df_wrf,
            15,
        )

        ax1.set_title(
            f"Forecast ({stn['name']})\nInitialized at {dt_var_str} 08:00 PHT",
            pad=28,
            fontsize=28,
        )

        ax4.set_xlabel("Day and Time (PHT)", size=24)

        label = stn["name"].replace(" ", "_")
        out_file = (
            Path(out_dir) / f"validation_aws_combined_{label}_{init_dt_str}PHT.png"
        )
        out_file.parent.mkdir(parents=True, exist_ok=True)
        fig.tight_layout(pad=2.0)
        plt.savefig(str(out_file), dpi=300)
        print("Saved figure " + str(out_file))

if __name__ == "__main__":
    out_dir = Path("")
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ho:", ["odir="])
    except getopt.GetoptError:
        print("plot_station_ts.py -o <output dir>")
        sys.exit(2)
    for opt, arg in opts:
        if opt == "-h":
            print("plot_station_ts.py -o <output dir>")
            sys.exit()
        elif opt in ("-o", "--odir"):
            out_dir = Path(arg)
            out_dir.mkdir(parents=True, exist_ok=True)
    proc(out_dir)
