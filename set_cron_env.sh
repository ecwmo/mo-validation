#!/bin/bash

export STATION_ID="MOIP"
export STATION_NAME="Manila Observatory"
export CITY_ID="NCR"

export VAL_DIR=$MAINDIR/validation

export TEMP_DIR=${VAL_DIR}/.tmp

export VAL_GFS_NC_DIR=${VAL_DIR}/input/gfs
export PYWRF_NC_DIR=${VAL_DIR}/input/wrf_out

export TRMM_CLIM_DIR=${VAL_DIR}/input/climatology/trmm
export APHRODITE_CLIM_DIR=${VAL_DIR}/input/climatology/aphrodite

export FCST_DIR=$OUTDIR/web/json
export STN_CLIM_DIR=$VAL_DIR/aws/csv

export WRF_JSON_DIR=$MAINDIR/output/stations_fcst_for_validation/json

export CONDA_PREFIX=${VAL_DIR}/venv
export MPLBACKEND="agg"
export PYTHONPATH=${VAL_DIR}/scripts:$PYTHONPATH
export PYTHON=${CONDA_PREFIX}/bin/python
