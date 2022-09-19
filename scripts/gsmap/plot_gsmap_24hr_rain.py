import sys
import getopt
import pytz
from pathlib import Path
import pandas as pd
import salem

import matplotlib.pyplot as plt

from helpers.plot import plot_map

tz = pytz.timezone("Asia/Manila")

var_name = "precip"
var_opts = {
    "title": "GSMaP 24-hr Total Rainfall (mm/day)",
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
}


def main(in_file, out_dir):
    ds = salem.open_xr_dataset(in_file)

    init_dt = pd.to_datetime(
        "_".join(in_file.name.split("_")[2:4]), format="%Y-%m-%d_%H", utc=True
    ).astimezone(tz)
    init_dt_str = init_dt.strftime("%Y-%m-%d %H")
    init_dt_str2 = init_dt.strftime("%Y-%m-%d_%H")

    da = ds[var_name]

    var_opts["title"] = f"{var_opts['title']}\nfrom {init_dt_str} PHT"
    var_opts["annotation"] = f"GSMaP (gauge calibrated) at {init_dt_str} PHT."
    fig = plot_map(da, var_opts)

    out_file = out_dir / f"gsmap-24hr_rain_{init_dt_str2}PHT.png"
    fig.savefig(out_file, bbox_inches="tight", dpi=300)
    plt.close("all")


if __name__ == "__main__":
    in_file = Path("dat")
    out_dir = Path("img")
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hi:o:", ["ifile=", "odir="])
    except getopt.GetoptError:
        print("plot_gsmap_24hr_rain.py -i <input file> -o <output dir>")
        sys.exit(2)
    for opt, arg in opts:
        if opt == "-h":
            print("plot_gsmap_24hr_rain.py -i <input file> -o <output dir>")
            sys.exit()
        elif opt in ("-i", "--ifile"):
            in_file = Path(arg)
        elif opt in ("-o", "--odir"):
            out_dir = Path(arg)
            out_dir.mkdir(parents=True, exist_ok=True)
    main(in_file, out_dir)
