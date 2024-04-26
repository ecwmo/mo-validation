import numpy as np 
import pandas as pd
import xarray as xr 
import salem
import xesmf as xe
from scipy.interpolate import interp1d

import os
from pathlib import Path

script_dir = Path(f"{os.getenv('SCRIPT_DIR')}/python/resources") 

def regrid(ds, _ds_out):
    return xe.Regridder(ds, _ds_out, "bilinear")(ds)


def mask(ds):
    _mask = salem.read_shapefile(
        script_dir / "shp/PHL_adm0/PHL_adm0.shp"
    )
    _ds_mask = ds.salem.roi(shape=_mask)

    return _ds_mask


def interpd(_newx, _vals, _idxs):
    return interp1d(_vals, _idxs, bounds_error=False, fill_value="extrapolate")(_newx)


def ARIinterp(_newx):
    _ph_ari_file = script_dir / "nc/PHIL_ARI.nc"
    _dat = xr.open_dataset(f"{_ph_ari_file}").rename({"precip": "rain"})

    _ari = [1, 2, 5, 10, 25, 30, 50, 100, 200, 500, 1000]
    _idx = xr.DataArray(_ari, dims=["ari"]).broadcast_like(_dat).to_dataset(name="rain")

    _ari_interpd = xr.apply_ufunc(
        interpd,
        _newx,
        _dat,
        _idx,
        input_core_dims=[["time"], ["ari"], ["ari"]],
        output_core_dims=[["time"]],
        vectorize=True,
        dask="parallelized",
    )
    return _ari_interpd

def wrf_ari(ds):
    _ds = ds.mean("ens").rename({"lon": "longitude", "lat": "latitude"})

    _trmm = (
        xr.open_dataset(script_dir / "nc/trmm_domain_regrid.nc")
        .rename({"precipitation": "rain", "lon": "longitude", "lat": "latitude"})
        .sel(longitude=slice(117.375, 126.375), latitude=slice(5.125, 18.875))
        .drop("time_bnds")
    )

    _ds_out = _trmm.drop(("time", "rain"))

    _wrf_inp = mask(regrid(_ds, _ds_out))
    _wrf_ari = ARIinterp(_wrf_inp)

    return _wrf_ari


def gsmap_ari(ds):
    _ds = ds.rename({"precip": "rain"})

    _trmm = (
        xr.open_dataset(script_dir / "nc/trmm_domain_regrid.nc")
        .rename({"precipitation": "rain", "lon": "longitude", "lat": "latitude"})
        .sel(longitude=slice(117.375, 126.375), latitude=slice(5.125, 18.875))
        .drop("time_bnds")
    )

    _ds_out = _trmm.drop(("time", "rain"))

    _wrf_inp = mask(regrid(_ds, _ds_out))
    _wrf_ari = ARIinterp(_wrf_inp)

    return _wrf_ari


