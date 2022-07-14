import pytz

from cartopy import crs as ccrs
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter

import matplotlib.pyplot as plt

tz = pytz.timezone("Asia/Manila")
plot_proj = ccrs.PlateCarree()

lon_formatter = LongitudeFormatter(zero_direction_label=True, degree_symbol="")
lat_formatter = LatitudeFormatter(degree_symbol="")

lon_labels = range(120, 130, 5)
lat_labels = range(5, 25, 5)
XLIM = (116, 128)
YLIM = (5, 20)


def plot_map(da, plt_opts):
    levels = plt_opts["levels"]
    colors = plt_opts["colors"]

    fig = plt.figure(figsize=(8, 9), constrained_layout=True)
    ax = plt.axes(projection=plot_proj)
    ax.xaxis.set_major_formatter(lon_formatter)
    ax.yaxis.set_major_formatter(lat_formatter)
    ax.set_xticks(lon_labels, crs=plot_proj)
    ax.set_yticks(lat_labels, crs=plot_proj)

    plt_title = plt_opts["title"]
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

    p.colorbar.ax.set_title(f"[{plt_opts['units']}]", pad=20, fontsize=10)
    ax.coastlines()
    ax.set_extent((*XLIM, *YLIM))

    if "annotation" in plt_opts:
        plt_annotation = plt_opts["annotation"]
        ax.annotate(plt_annotation, xy=(5, -30), xycoords="axes points", fontsize=8)

    ax.annotate(
        "observatory.ph",
        xy=(10, 10),
        xycoords="axes points",
        fontsize=10,
        bbox=dict(boxstyle="square,pad=0.3", alpha=0.5),
        alpha=0.5,
    )

    return fig
