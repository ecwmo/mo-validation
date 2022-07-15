import sys
import getopt
from pathlib import Path
import gzip
import numpy as np
import pandas as pd
import xarray as xr
import salem

from tqdm import tqdm


def convert_to_xr(gz_file, var_name="precip"):
    gz = gzip.GzipFile(gz_file, "rb")
    dd = np.frombuffer(gz.read(), dtype=np.float32)
    dat = dd.reshape((1, 1200, 3600))
    ts = pd.to_datetime("-".join(gz_file.name.split(".")[1:3]), format="%Y%m%d-%H00")
    lon = np.linspace(0.05, 359.95, 3600)
    lat = np.linspace(59.95, -59.95, 1200)

    ds = xr.Dataset(
        {var_name: (["time", "lat", "lon"], dat)},
        coords={"time": ("time", [ts]), "lat": ("lat", lat), "lon": ("lon", lon)},
    )
    return ds.reindex(lat=ds.lat[::-1])


def proc(in_dir, out_dir):
    in_files = list(in_dir.glob("*.dat.gz"))
    in_files.sort()
    ds = [convert_to_xr(f) for f in tqdm(in_files, desc="Convert to ds")]
    ds = xr.concat(ds, dim="time")

    ds.attrs["Conventions"] = "CF-1.7"
    ds.attrs["source"] = "gsmap_gauge"
    ds.precip.attrs["long_name"] = "hourly averaged rain rate [mm/hr]"
    ds.precip.attrs["missing_value"] = -99.0
    ds.lon.attrs["units"] = "degrees_east"
    ds.lon.attrs["standard_name"] = "longitude"  # Optional
    ds.lon.attrs["long_name"] = "longitude"
    ds.lat.attrs["units"] = "degrees_north"
    ds.lat.attrs["standard_name"] = "latitude"  # Optional
    ds.lat.attrs["long_name"] = "latitude"

    out_file_prefix = in_files[0].name.split(".")[0]
    ts = pd.to_datetime(
        "-".join(in_files[0].name.split(".")[1:3]), format="%Y%m%d-%H00"
    )

    print("Saving nc...")
    out_file = out_dir / f"{out_file_prefix}_{ts:%Y-%m-%d_%H}.nc"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    ds2 = ds.sel(lon=slice(115, 129), lat=slice(4.8, 21))
    ds2.to_netcdf(out_file)
    ds2 = salem.open_xr_dataset(out_file)
    print("Saving daily accum precip...")
    out_file = out_dir / f"{out_file_prefix}_{ts:%Y-%m-%d_%H}_day.nc"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    ds3 = ds2.sum("time", keep_attrs=True)
    ds3.to_netcdf(out_file)


if __name__ == "__main__":
    in_dir = Path("dat")
    out_dir = Path("nc")
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hi:o:", ["idir=", "odir="])
    except getopt.GetoptError:
        print("convert_gsmap_nc.py -i <input dir> -o <output dir>")
        sys.exit(2)
    for opt, arg in opts:
        if opt == "-h":
            print("convert_gsmap_nc.py -i <input dir> -o <output dir>")
            sys.exit()
        elif opt in ("-i", "--idir"):
            in_dir = Path(arg)
        elif opt in ("-o", "--odir"):
            out_dir = Path(arg)
            out_dir.mkdir(parents=True, exist_ok=True)
    proc(in_dir, out_dir)
