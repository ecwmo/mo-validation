from cartopy import crs as ccrs
import cartopy.feature as cf
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter
import matplotlib as mp
import matplotlib.pyplot as plt

import numpy as np 

mp.rcParams["font.size"] = 9

plot_proj = ccrs.PlateCarree()
def plot_format(ax):
    lon_formatter = LongitudeFormatter(zero_direction_label=True, degree_symbol="")
    lat_formatter = LatitudeFormatter(degree_symbol="")

    lon_labels = range(120, 130, 5)
    lat_labels = range(5, 25, 5)
    xlim = (116, 128)
    ylim = (5, 20)
    
    ax.xaxis.set_major_formatter(lon_formatter)
    ax.yaxis.set_major_formatter(lat_formatter)
    ax.set_xticks(lon_labels, crs=plot_proj)
    ax.set_yticks(lat_labels, crs=plot_proj)
    ax.add_feature(cf.OCEAN.with_scale("10m"), facecolor="white", edgecolor="black", zorder=2)
    ax.add_feature(cf.LAKES.with_scale("10m"), facecolor="None", edgecolor="black", zorder=2)
    ax.set_extent((*xlim, *ylim))
    
    ax.annotate(
        "observatory.ph",
        xy=(10, 10),
        xycoords="axes points",
        fontsize=7,
        bbox=dict(boxstyle="square,pad=0.3", alpha=0.5),
        alpha=0.5,
    )
    
    return ax
    
plot_vars = {
    "rain_actual": {
        "title": "Total Rainfall",
        "units": "mm",
        "levels": np.arange(50, 500, 50),
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
    "rain_anomaly": {
        "title": "Total Rainfall Anomaly",
        "units": "mm",
        "levels": np.arange(-150, 175, 25),
        "colors": [mp.colors.rgb2hex(mp.cm.get_cmap("BrBG")(i)) for i in range(mp.cm.get_cmap("BrBG").N) ],
    },
    "temp_actual": {
        "title": "Average Temperature",
        "units": "°C",
        "levels": np.arange(18, 34, 2),
        "colors": [mp.colors.rgb2hex(mp.cm.get_cmap("YlOrRd")(i)) for i in range(mp.cm.get_cmap("YlOrRd").N) ],
    },
    "temp_anomaly": {
        "title": "Average Temperature",
        "units": "°C",
        "levels": np.arange(-2.5, 3., .5),
        "colors": [mp.colors.rgb2hex(mp.cm.get_cmap("coolwarm")(i)) for i in range(mp.cm.get_cmap("coolwarm").N) ],
    }
}
