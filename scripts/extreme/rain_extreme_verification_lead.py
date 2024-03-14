import pandas as pd
import numpy as np
import xarray as xr
import matplotlib as mp
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from pathlib import Path
import os
import glob
import getopt


import sys
sys.path.append("/home/modelman/forecast/validation/scripts/helpers")

from plot_format import *
from contingency_ari import *
from contingency_clim import *
from contingency_config import config_lead
from contingency_preproc import dataset_lead


config = config_lead()
_forecast_day = config.forecast_day
_forecast_hour = config.forecast_hour
_forecast_date_str = config.forecast_date_str
_forecast_dates = config.forecast_dates
_fnl_files = config.fnl_files
_forecast_index = config.forecast_index


def plot_contigency(clim_ds, ari_ds):
    fig, axes = plt.subplots(ncols=2, figsize=(12,12), subplot_kw={"projection":ccrs.PlateCarree()})
    axlist = axes.flatten()
    
    _clim_dat = [clim_ds.hits, clim_ds.miss, clim_ds.false, clim_ds.non_event]
    _ari_dat = [ari_ds.hits, ari_ds.miss, ari_ds.false, ari_ds.non_event]
    _day = pd.to_datetime(clim_ds.hits.time.values) + pd.Timedelta(8, "H")
    _vars = ["hits", "miss", "false", "non_event"]
    _colors = ["#5AAD61", "#CD303A", "#2266AC","#D0DADC"]
    _legend = []
    
    for day in range(len(_day)):
        day_str = _day[day].strftime("%Y-%m-%d_%H")
        print(f"Plotting initialtized {day_str}....")
        
        for clim,ari,var,color in zip(_clim_dat, _ari_dat, _vars, _colors):
            clim[var].isel(time=day).plot.pcolormesh(
            x="lon",
            y="lat",
            levels=[0, 1],
            colors=[color],
            extend="both",
            add_colorbar=False,
            add_labels=False,
            transform=ccrs.PlateCarree(),
            ax=axlist[0]
            )
            
            ari[var].isel(time=day).plot.pcolormesh(
            x="longitude",
            y="latitude",
            levels=[0, 1],
            colors=[color],
            extend="both",
            add_colorbar=False,
            add_labels=False,
            transform=ccrs.PlateCarree(),
            ax=axlist[1]
            )

            _patch = mpatches.Patch(color=color, label=f"{var}")
            _legend.append(_patch)
            
        plt.legend(handles=[_legend[i] for i in range(4)], ncol=4, loc="center", bbox_to_anchor=(-0.1, -0.17))
        
        _dt1 = _forecast_date_str + pd.Timedelta(8, "H")
        _dt1_str = _dt1.strftime("%Y-%m-%d %H")
        _dt2 = _dt1 + pd.Timedelta(1, "D")
        _dt2_str = _dt2.strftime("%Y-%m-%d %H")
        _init_dt_str1 = _day[day].strftime("%Y-%m-%d %H")
        _init_dt_str2 = _forecast_date_str.strftime("%Y-%m-%d_%H")
        
        plt_title = f"Valid from {_dt1_str} to {_dt2_str} PHT"
        plt_annotation = f"WRF ensemble forecast initialized at {_init_dt_str1} PHT."
        
        for ax,title in zip(axlist, ["CLIM", "ARI"]):    
            ax.set_title(f"WRF {title} Verification\n{plt_title}", fontsize=11)
            ax.annotate(plt_annotation, xy=(5, -30), xycoords="axes points", backgroundcolor="white", fontsize=8)
            plot_format(ax)
        
        forecast_day = {"0": "120", "1": "96", "2":"72", "3":"48", "4":"24"}
        tt = (forecast_day.get(str(_forecast_index[day])))
        out_file = out_dir / f"img/wrf_{tt}hr_cont_lead_{_init_dt_str2}PHT.png"
        fig.savefig(
            out_file,
            dpi=200, 
            facecolor="white", 
            bbox_inches="tight",)
            
        plt.close()
        
            
def plot_performance_diagram(clim, ari, event):
    colors = [
        '#ffffff', 
        '#f0f0f0', 
        '#e3e3e3', 
        '#d6d6d6', 
        '#c9c9c9', 
        '#bdbdbd', 
        '#b0b0b0',
        '#a3a3a3', 
        '#969696', 
        '#8a8a8a'
        ]
    cmap = mp.colors.LinearSegmentedColormap.from_list("", colors)

    mp.rcParams["font.size"] = 13
    
    fig = plt.figure(figsize=(10, 10))
    ax1 = fig.add_subplot(111)
    ax2 = ax1.twinx()

    for ax in ([ax1, ax2]):
        ax.set_xlim([0, 1])
        ax.set_ylim([0, 1])


    ax2.set_yticklabels("")
    ax2.set_yticks([])

    x_axis = y_axis = np.arange(0.01, 1.01, 0.01)
    x_mesh, y_mesh = np.meshgrid(x_axis, y_axis)

    _csi = ((1 / x_mesh) + (1 / y_mesh) - 1) ** -1
    _cs_contf = ax1.contourf(
        x_mesh, 
        y_mesh, 
        _csi, 
        np.arange(0.0, 1.1, 0.1), 
        cmap=cmap, 
        )
    _cs_cont = ax1.contour(
        x_mesh, 
        y_mesh, 
        _csi, 
        np.arange(0.0, 1.1, 0.1), 
        colors="grey", 
        linewidths=0.8)
    
    ax1.clabel(_cs_cont, _cs_cont.levels, inline=True, colors="black", fontsize=12)
    
    _biases = [0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 4.0, 10.0]
    _bias_loc_x = [1.0, 1.0, 1.0, 1.0, 1.0, 0.65, 0.48, 0.23, 0.08]
    _bias_loc_y = [0.1, 0.25, 0.5, 0.75, 1.0, 1.0, 1.0, 1.0, 1.0]

    _bias = y_mesh / x_mesh
    _bias_var = ax1.contour(x_mesh, y_mesh, _bias, _biases, colors="black", alpha=0.5, linestyles=':')


    for i, j in enumerate(_biases):
        ax1.annotate(
            j, 
            xy=(_bias_loc_x[i], _bias_loc_y[i]), 
            xytext=(_bias_loc_x[i]+0.01, _bias_loc_y[i]+0.01), 
            fontsize=12
            )

    _clim, _ari = clim.copy(), ari.copy()
    _clim.fillna(0, inplace=True), _ari.fillna(0, inplace=True)
    
    markers = {"LPS": "P", "TC": "o", "M": "X"}
    marker = markers.get(event)
    
    ax1.plot("SR", "POD", data=_clim, linestyle="", marker=marker, markersize=12, color="#0055FF", label="CLIM")
    ax1.plot("SR", "POD", data=_ari, linestyle="", marker=marker, markersize=12, color="#FF4E58", label="ARI")
    
    forecast_day = {"0": "5", "1": "4", "2":"3", "3":"2", "4":"1"}
    forecast_day_str = [forecast_day.get(str(idx)) for idx in _forecast_index]
    for dat,color in zip([_clim, _ari], ["#0055FF", "#FF4E58"]):
        for x,y,fc_day in zip(dat.SR.values, dat.POD.values, forecast_day_str):
            ax1.text(x+0.01, y+0.01, fc_day, color=color, fontsize=13, fontweight="semibold")
    
    _init_dt_str = pd.to_datetime(_forecast_date_str, format="%Y-%m-%d %H") + pd.Timedelta(8, "H")
    _dt1 = _init_dt_str.strftime("%Y-%m-%d_%H")
    _dt2 = (_init_dt_str + pd.Timedelta(1, "D")).strftime("%Y-%m-%d %H")
    _init_dt_str = _init_dt_str.strftime("%Y-%m-%d_%H")
    
    
    fig.suptitle(f"WRF ensemble forecast\nvalid from {_dt1} to {_dt2} PHT", y=1.0, fontsize=15)
    ax1.set_xlabel("Success Ratio (SR)", labelpad=15, fontsize=15)
    ax1.set_ylabel("Probability of Detection (POD)", fontsize=15)
    ax2.set_ylabel("Critical Success Index (CSI)", labelpad=35, fontsize=15)
    ax1.annotate("Bias", xy=(0.5, 1.0), xytext=(0.5, 1.05), fontsize=15)
    ax1.legend(ncol=2, loc="lower center", bbox_to_anchor=[0.18, -0.18], fontsize=15)
    
    
    out_file = out_dir / f"img/wrf_diag_lead_{_init_dt_str}PHT.png"
    fig.savefig(
        out_file
        , dpi=200, 
        facecolor="white", 
        bbox_inches="tight",
        )
            
    plt.close()
    
    
def run_contingency(plot=False, ari=5):
    
    _datasets = dataset_lead()
    
    print(f"Calculating contingencies for {_forecast_date_str}....")
    contingency_ari = Contingency_ari(_datasets.ari_observed, _datasets.ari_forecast, ari)
    contingency_clim = Contingency_clim(_datasets.observed, _datasets.forecast)
    
    print("Done!")
    _cont_ari_df = contingency_ari.table
    _cont_clim_df = contingency_clim.table
    
    
    print("Plotting performance diagram.....")
    plot_performance_diagram(_cont_clim_df, _cont_ari_df, "TC")
    
    if plot == False:
        print("Nothing to plot....")
    else:
        print("Plotting contingency map....")
        plot_contigency(contingency_clim, contingency_ari)

    
if __name__ == "__main__":
    plot = False
    ari = 5  # Default value for ari
    out_dir  = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hw:o:", ["plot=", "ari=", "out_dir="])
    except getopt.GetoptError:
        print("Usage: script.py -w <run_contingency_test> [--plot] [--ari <value>] [-o <out_dir>]")
        sys.exit(2)
    
    for opt, arg in opts:
        if opt == "-h":
            print("Usage: script.py -w <plot>")
            sys.exit()
            
        elif opt in ("-w", "--plot"): # Set plot to True instead of False
            plot = True
        
        elif opt ==  "--ari":
            ari = int(arg)  # Convert argument to an integer, adjust as needed
        
        elif opt == "-o":
            out_dir = Path(arg) # Convert to path
    
    
    out_dir = out_dir / f"{_forecast_day}/{_forecast_hour}"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    img_dir = out_dir / "img"
    img_dir.mkdir(parents=True, exist_ok=True)
    
    run_contingency(plot=plot, ari=ari)

    #USAGE: python rain_extreme_verification_lead.py -w --plot --ari 5 -o "out_dir"
    ## -w --plot sets plotting of spatial verification and roebber's diagrams to true
    ## -ari 5 sets ari threshold to 5 by default but can be changed