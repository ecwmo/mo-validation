import pandas as pd
import numpy as np
import matplotlib as mp
import matplotlib.pyplot as plt

from pathlib import Path
import os
import getopt

import sys
sys.path.append("/home/modelman/forecast/validation/scripts/helpers")

from contingency_config import config_lead

forecast_date = config_lead().forecast_date_str.strftime("%Y-%m-%d_%H")
forecast_day = config_lead().forecast_date_str.strftime("%Y%m%d")
forecast_hour = config_lead().forecast_hour
_forecast_date_str = config_lead().forecast_date_str

_path = os.getenv("OUTDIR")
_path = f"{_path}/validation/extreme/{forecast_day}/{forecast_hour}"

def plot_performance_diagram(event):
    ### Borrowed from METplotpy performance diagram (https://metplotpy.readthedocs.io/en/develop/Users_Guide/performance_diagram.html)
    
    print(f"Plotting {_forecast_date_str}......")
    
    clim = pd.read_csv(inp_dir / f"wrf_cont_clim_{forecast_date}.csv")
    ari = pd.read_csv(inp_dir / f"wrf_cont_ari_{forecast_date}.csv")
    
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
    
    for dat,color in zip([_clim, _ari], ["#0055FF", "#FF4E58"]):
        for idx,(x,y) in enumerate(zip(dat.SR.values, dat.POD.values)):
            ax1.text(x+0.01, y+0.01, str(idx+1), color=color, fontsize=13, fontweight="semibold")
            
    _init_dt_str = _forecast_date_str + pd.Timedelta(8, "H")
    _init_dt_title = _init_dt_str.strftime("%Y-%m-%d %H")
    _init_dt_str = _init_dt_str.strftime("%Y-%m-%d_%H")
    
    fig.suptitle(f"WRF ensemble forecast initialized at {_init_dt_title} PHT", fontsize=15)
    ax1.set_xlabel("Success Ratio (SR)", labelpad=15, fontsize=15)
    ax1.set_ylabel("Probability of Detection (POD)", fontsize=15)
    ax2.set_ylabel("Critical Success Index (CSI)", labelpad=35, fontsize=15)
    ax1.annotate("Bias", xy=(0.5, 1.0), xytext=(0.5, 1.05), fontsize=15)
    ax1.legend(ncol=2, loc="lower center", bbox_to_anchor=[0.18, -0.18], fontsize=15)

    out_file = out_dir / f"img/wrf_diag_{_init_dt_str}PHT.png"
    fig.savefig(
        out_file
        , dpi=200, 
        facecolor="white", 
        bbox_inches="tight",
        )
            
    plt.close()

if __name__ == "__main__":
    
    inp_dir = Path(f"{_path}/csv") # Set default path
    out_dir = Path(_path) # Set default path
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hw:o:", ["inp_dir=", "out_dir="])
    except getopt.GetoptError:
        print("Usage: script.py -w <run_diagram> [--inp_dir] [-o <out_dir>]")
        sys.exit(2)
    
    for opt, arg in opts:
        
        if opt == "-h":
            print("Usage: script.py -w <inp_dir>")
            sys.exit()
            
        elif opt in ("-w", "--inp_dir"): # Convert to path
            inp_dir = Path(arg)
        
        elif opt in ("-o", "--out_dir"):
            out_dir = Path(arg) # Convert to path
            out_dir = out_dir / f"{forecast_day}/{forecast_hour}"
            
    out_dir.mkdir(parents=True, exist_ok=True)
    
    img_dir = out_dir / "img"
    img_dir.mkdir(parents=True, exist_ok=True)
    
    plot_performance_diagram("LPS")
    
# USAGE: python plot_roebber_diagram.py 
# If infile and outfile are different from the default, pass -w "<ifile>" -o "<ofile>", respectively 
# (i.e. python plot_roebber_diagram.py -w "$indir" "$outdir")