#!/bin/bash

export S_DATE=(20210620)
export S_ZZ=(00)

WORKDIR=/home/modelman/forecast/validation/contingency
ARWPOST_DIR=/home/modelman/forecast/validation/contingency/wrf_dugong
PYTHONCONDA=/home/miniconda3/envs/toolbox/bin/python

YYYY=${S_DATE:0:4}
MM=${S_DATE:4:2}
DD=${S_DATE:6:2}

DATE2=$(date -d "${YYYY}-$MM-$DD ${S_ZZ}:00:00 0 hours" +'%Y-%b-%d %H:%M:%S')
read YY2 mm2 DD2 HH2 MM2 SS2 <<< ${DATE2//[-: ]/ }
DATE_LOC=$(date -d "${YYYY}-$MM-$DD ${S_ZZ}:00:00 8 hours" +'%Y-%m-%d %H:%M:%S')
read YYL mmL DDL HHL MML SSL <<< ${DATE_LOC//[-: ]/ }

# Download GSMaP_gauge data
# Assume data in dat directory is available

# Get data from Dugong
# Assume data from dugong is in wrf_dugong dir

# Edit gsmap ctl file
sed -i "16s/.*/TDEF   24 LINEAR ${S_ZZ}Z${DD}${mm2}${YYYY} 1hr/" gsmap_gauge.ctl

# Edit grads script to extract to netCDF
sed -i "1s/.*/date='${YYL}-${mmL}-${DDL}_${HHL}PHT'/" convert_nc.gs
sed -i "2s~.*~outdir='${WORKDIR}/nc'~" convert_nc.gs
sed -i "3s~.*~'open ${ARWPOST_DIR}/wrffcst_d01_${YYYY}-${MM}-${DD}_${S_ZZ}.ctl'~" convert_nc.gs

grads -pbc convert_nc.gs

# cdo convert gsmap to finer resolution
source activate toolbox
cdo remapbil,${WORKDIR}/nc/wrf-p24_2021-06-20_08PHT.nc ${WORKDIR}/nc/gsmap-p24_2021-06-20_08PHT.nc ${WORKDIR}/nc/gsmap-p24_2021-06-20_08PHT_re.nc 

# Edit python script to compute for forecast verification statistics

sed -i "4s/.*/yyyymmdd = '${YYL}-${mmL}-${DDL}'/" forecast_verification.py
sed -i "5s/.*/init = '${HHL}'/" forecast_verification.py
sed -i "6s~.*~EXTRACT_DIR = '${WORKDIR}/nc'~" forecast_verification.py
sed -i "7s~.*~OUT_DIR = '${WORKDIR}/img'~" forecast_verification.py

export MPLBACKEND="agg"; $PYTHONCONDA forecast_verification.py
