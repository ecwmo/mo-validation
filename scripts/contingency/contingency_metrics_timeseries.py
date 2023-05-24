# Title: Contingency table time series
# Author: Kevin Henson
# Last edited: Feb. 8, 2022

# !/usr/bin/env python
# coding: utf-8

from pathlib import Path
import matplotlib.pyplot as plt

# import datetime as dt
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
import sys
import getopt


def main(out_dir):
    nc_dir = os.getenv("PYWRF_NC_DIR")
    flist = os.listdir(nc_dir)[1:]

    for fn in flist:
        ds = salem.open_xr_dataset(f"{nc_dir}/{fn}")
        print(ds)
        sys.exit()


if __name__ == "__main__":
    out_dir = Path("img")
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h:o:", ["odir="])
    except getopt.GetoptError:
        print("contingency_metrics_timeseries.py -o <output dir>")
        sys.exit(2)
    for opt, arg in opts:
        if opt == "-h":
            print("contingency_metrics_timeseries.py-o <output dir>")
            sys.exit()
        elif opt in ("-o", "--odir"):
            out_dir = Path(arg)
            out_dir.mkdir(parents=True, exist_ok=True)
    main(out_dir)
