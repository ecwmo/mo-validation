import sys
import getopt
from pathlib import Path

import pandas as pd
import xarray as xr
import salem

from tqdm import tqdm


def convert_to_xr(grb_file, var_name="precip"):
    ds = xr.open_dataset(
        grb_file, filter_by_keys={"stepType": "instant", "typeOfLevel": "surface"}
    )["prate"]
    ds = ds.assign_coords(time=ds.valid_time.values)
    ds = ds.drop_vars(["valid_time", "step", "surface"])
    ds = ds.rename({"latitude": "lat", "longitude": "lon"})
    ds.name = var_name
    return ds


def proc(in_dir, out_dir):
    in_files = list(in_dir.glob("*.grb"))
    in_files.sort()

    ds = [convert_to_xr(f) for f in tqdm(in_files, desc="Convert to ds")]
    ds = xr.concat(ds, dim="time")

    ds = ds.to_dataset()
    ds.precip.attrs = {}
    ds.precip.values = ds.precip.values * 3600

    ds.attrs["Conventions"] = "CF-1.7"
    ds.attrs["source"] = "GFS grib"
    ds.precip.attrs["long_name"] = "rain rate [mm/hr]"
    ds.precip.attrs["missing_value"] = 9999

    out_file_prefix = "gfs"
    ts = pd.to_datetime(ds.time.values[0])

    print("Saving nc...")
    out_file = out_dir / f"{out_file_prefix}_{ts:%Y-%m-%d_%H}.nc"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    ds.to_netcdf(out_file)

    ds = salem.open_xr_dataset(out_file)
    ds2 = ds.groupby("time.day").sum(keep_attrs=True).rename({"day": "time"})
    ds2 = ds2.assign_coords(time=pd.date_range(ds.time.values[0], ds.time.values[-1]))
    out_file = out_dir / f"{out_file_prefix}_{ts:%Y-%m-%d_%H}_day.nc"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    ds2.to_netcdf(out_file)


if __name__ == "__main__":
    in_dir = Path("dat")
    out_dir = Path("nc")
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hi:o:", ["idir=", "odir="])
    except getopt.GetoptError:
        print("convert_gfs_nc.py -i <input dir> -o <output dir>")
        sys.exit(2)
    for opt, arg in opts:
        if opt == "-h":
            print("convert_gfs_nc.py -i <input dir> -o <output dir>")
            sys.exit()
        elif opt in ("-i", "--idir"):
            in_dir = Path(arg)
        elif opt in ("-o", "--odir"):
            out_dir = Path(arg)
            out_dir.mkdir(parents=True, exist_ok=True)
    proc(in_dir, out_dir)
