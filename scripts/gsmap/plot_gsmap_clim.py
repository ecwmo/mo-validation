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

trmm_clim_dir = Path(os.getenv("TRMM_CLIM_DIR"))
aphro_clim_dir = Path(os.getenv("APHRODITE_CLIM_DIR"))

tz = pytz.timezone("Asia/Manila")

var_opts = {
    "title": "GSMaP 24-hr Total Rain",
    "units": "%",
    "levels": range(25, 151, 25),
    "colors": sns.blend_palette(
        [
            "#ffffff",
            "#54278f",
        ],
        n_colors=7,
    ),
}

clim_dats = [
    {
        "name": "aphro",
        "path": aphro_clim_dir / "rain",
        "var_name": "precip",
        "label": "APHRODITE_V1101_1981-2010",
        "files": [
            {
                "type": "mean",
                "name": "PH_aphro_1981-2010_mm",
                "title": "APHRODITE Climatological Monthly Total Rain",
                "annotation": "Climatological 1-Month Total",
            },
            {
                "type": "99p",
                "name": "PH_aphro_1981-2010_mm99p",
                "title": "APHRODITE Climatological Monthly Extreme Rain",
                "annotation": "Climatological 1-Month 99th %ile",
            },
        ],
    },
    {
        "name": "trmm",
        "path": trmm_clim_dir,
        "var_name": "precipitation",
        "label": "TRMM_3B42_1998-2015",
        "files": [
            {
                "type": "mean",
                "name": "PH_trmm_1998-2015_mm",
                "title": "TRMM Climatological Monthly Total Rain",
                "annotation": "Climatological 1-Month Total",
            },
            {
                "type": "99p",
                "name": "PH_trmm_1998-2015_mm99p",
                "title": "TRMM Climatological Monthly Extreme Rain",
                "annotation": "Climatological 1-Month 99th %ile",
            },
        ],
    },
]


def main(in_file, out_dir):
    gsmap = salem.open_xr_dataset(in_file)["precip"]

    init_dt_utc = pd.to_datetime(
        "_".join(in_file.name.split("_")[2:4]), format="%Y-%m-%d_%H", utc=True
    )
    init_dt = init_dt_utc.astimezone(tz)
    init_dt_str = init_dt.strftime("%Y-%m-%d %H")
    init_dt_str2 = init_dt.strftime("%Y-%m-%d_%H")

    for clim_dat in clim_dats:
        for f in clim_dat["files"]:
            clim_file = clim_dat["path"] / f"{f['name']}_{init_dt:%m}.nc"
            if not clim_file.is_file():
                print(f"{f} file not found")
                # return
            clim_ds = salem.open_xr_dataset(clim_file)

            clim_rain = clim_ds[clim_dat["var_name"]].isel(time=0)
            clim_rain = clim_rain.sel(lat=slice(*YLIM), lon=slice(*XLIM))

            regridder = xe.Regridder(gsmap, clim_rain, "bilinear")
            gsmap_re = regridder(gsmap)

            da = (gsmap_re / clim_rain) * 100

            plt_opts = var_opts.copy()
            plt_opts[
                "title"
            ] = f"{plt_opts['title']} [{init_dt_str} PHT]\nRelative to {f['title']}"
            plt_opts[
                "annotation"
            ] = f"GSMaP (gauge calibrated) at {init_dt_str} PHT.\n{clim_dat['label']} {f['annotation']} for {init_dt:%b}"
            fig = plot_map(da, plt_opts)

            out_file_pref = "gsmap"
            out_file = (
                out_dir
                / f"{out_file_pref}-24hr_rain_day0_{clim_dat['name']}_{f['type']}_{init_dt_str2}PHT.png"
            )
            fig.savefig(out_file, bbox_inches="tight", dpi=300)
            plt.close("all")


if __name__ == "__main__":
    in_file = Path("dat")
    out_dir = Path("img")
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hi:o:", ["ifile=", "odir="])
    except getopt.GetoptError:
        print("plot_gsmap_clim.py -i <input file> -o <output dir>")
        sys.exit(2)
    for opt, arg in opts:
        if opt == "-h":
            print("plot_gsmap_clim.py -i <input file> -o <output dir>")
            sys.exit()
        elif opt in ("-i", "--ifile"):
            in_file = Path(arg)
        elif opt in ("-o", "--odir"):
            out_dir = Path(arg)
            out_dir.mkdir(parents=True, exist_ok=True)
    main(in_file, out_dir)
