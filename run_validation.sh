#!/bin/bash

#################### CONSTANTS ####################
DOWNLOAD_INPUT=1
###################################################

#################### FUNCTIONS ####################
function show_usage() {
  printf "Usage: %s [options [parameters]]\n" "$0"
  printf "\n"
  printf "Options:\n"
  printf " --no-download, Do not download inputs (GSMAP, etc...)\n"
  printf " -h|--help, Print help\n"

  return 0
}
###################################################

################### PROCESS ARGS ###################
while [ -n "$1" ]; do
  case "$1" in
  --no-download)
    DOWNLOAD_INPUT=0
    ;;
  *)
    show_usage
    ;;
  esac
  shift
done
###################################################

DATE_STR1=$(date -d "${FCST_YY}-${FCST_MM}-${FCST_DD} $FCST_ZZ:00:00 8 hours" +'%Y-%m-%d_%H')
read -r FCST_YY_PHT FCST_MM_PHT FCST_DD_PHT FCST_HH_PHT <<<"${DATE_STR1//[-_]/ }"
# -------------------------------------------- #
#                 GSMaP                        #
# -------------------------------------------- #

echo "--------------------------"
echo " Processing GSMaP files  "
echo "--------------------------"

cd "$VAL_DIR/gsmap" || exit

if [ $DOWNLOAD_INPUT -eq 1 ]; then
  export GSMAP_TEMP_DIR="$TEMP_DIR/gsmap/$FCST_YYYYMMDD/$FCST_ZZ"
  mkdir -p "$GSMAP_TEMP_DIR"
  # Download GSMaP data
  ./download_gsmap.sh
  # Convert GSMaP .gz files to .nc
  $PYTHON convert_gsmap_nc.py -i "$GSMAP_TEMP_DIR" -o "$VAL_DIR/input/gsmap"
  # Remove .gz files
  rm -rf "${GSMAP_TEMP_DIR?:}"
fi

# Plot GSMaP
gsmap_in_nc=$VAL_DIR/input/gsmap/gsmap_${GSMAP_DATA}_${FCST_YY}-${FCST_MM}-${FCST_DD}_${FCST_ZZ}_ph.nc
gsmap_out_img=$VAL_OUTDIR/gsmap-24hr_rain_day1_${DATE_STR1}PHT.png
$PYTHON plot_gsmap_24hr_rain.py -i "$gsmap_in_nc" -o "$gsmap_out_img"

echo "--------------------------"
echo " Done with GSMaP!         "
echo "--------------------------"
# -------------------------------------------- #
#                   GFS                        #
# -------------------------------------------- #
echo "--------------------------"
echo " Processing GFS files...  "
echo "--------------------------"

cd "$VAL_DIR/gfs" || exit

# Convert GFS precipitation grb files to .nc
./convert_gfs_nc.sh

# Plot GFS
mkdir -p "$VAL_OUTDIR"
cd "$VAL_DIR/grads" || exit

# Edit GrADS plotting script
DATE_STR1=$(date -d "${FCST_YY}-${FCST_MM}-${FCST_DD} $FCST_ZZ:00:00 8 hours" +'%Y-%m-%d_%H')
read -r FCST_YY_PHT FCST_MM_PHT FCST_DD_PHT FCST_HH_PHT <<<"${DATE_STR1//[-_]/ }"
DATE_STR2=$(date -d "${FCST_YY}-${FCST_MM}-${FCST_DD} $FCST_ZZ:00:00 32 hours" +'%Y-%m-%d_%H')
DATE_STR3=$(date -d "${FCST_YY}-${FCST_MM}-${FCST_DD} $FCST_ZZ:00:00 56 hours" +'%Y-%m-%d_%H')
DATE_STR4=$(date -d "${FCST_YY}-${FCST_MM}-${FCST_DD} $FCST_ZZ:00:00 80 hours" +'%Y-%m-%d_%H')

sed -i "1s/.*/date='${DATE_STR1}PHT'/" gfs_24hr_rain.gs
sed -i "2s/.*/date2='${DATE_STR1} PHT'/" gfs_24hr_rain.gs
sed -i "3s/.*/date3='${DATE_STR1} to ${DATE_STR2} PHT'/" gfs_24hr_rain.gs
sed -i "4s/.*/date4='${DATE_STR2} to ${DATE_STR3} PHT'/" gfs_24hr_rain.gs
sed -i "5s/.*/date5='${DATE_STR3} to ${DATE_STR4} PHT'/" gfs_24hr_rain.gs
sed -i "6s~.*~outdir='${VAL_OUTDIR}'~" gfs_24hr_rain.gs
sed -i "7s~.*~gfsdir='${VAL_DIR}/gfs/nc/${FCST_YY}${FCST_MM}${FCST_DD}/${FCST_ZZ}'~" gfs_24hr_rain.gs

grads -pbc gfs_24hr_rain.gs

sed -i "1s/.*/date='${DATE_STR1}PHT'/" gfs_acc_rain.gs
sed -i "2s/.*/date2='${DATE_STR1} PHT'/" gfs_acc_rain.gs
sed -i "3s/.*/date3='${DATE_STR1} to ${DATE_STR2} PHT'/" gfs_acc_rain.gs
sed -i "4s/.*/date4='${DATE_STR2} to ${DATE_STR3} PHT'/" gfs_acc_rain.gs
sed -i "5s/.*/date5='${DATE_STR3} to ${DATE_STR4} PHT'/" gfs_acc_rain.gs
sed -i "6s~.*~outdir='${VAL_OUTDIR}'~" gfs_acc_rain.gs
sed -i "7s~.*~gfsdir='${VAL_DIR}/gfs/nc/${FCST_YY}${FCST_MM}${FCST_DD}/${FCST_ZZ}'~" gfs_acc_rain.gs

grads -pbc gfs_acc_rain.gs

# Get hourly data over stations
rm -rf $VAL_OUTDIR/gfs_${DATE_STR1}PHT*.csv

# Edit GrADS extract script
sed -i "1s/.*/date='${DATE_STR1}PHT'/" gfs_extract_rain.gs
sed -i "2s~.*~outdir='${VAL_OUTDIR}'~" gfs_extract_rain.gs
sed -i "3s~.*~gfsdir='${VAL_DIR}/gfs/nc/${FCST_YY}${FCST_MM}${FCST_DD}/${FCST_ZZ}'~" gfs_extract_rain.gs

grads -pbc gfs_extract_rain.gs

echo "--------------------------"
echo " Done with GFS!           "
echo "--------------------------"
# -------------------------------------------- #
#            COMPARISON PLOTS                  #
# -------------------------------------------- #
echo "---------------------------------"
echo " Processing comparison plots...  "
echo "---------------------------------"

# 24-hr difference plot (WRF-GSMaP, GFS-GSMaP)
cd "$VAL_DIR/grads" || exit

ln -s "${WRF_ENS}/wrffcst_d01_${FCST_YY}-${FCST_MM}-${FCST_DD}_${FCST_ZZ}_ens.nc" ${VAL_DIR}/grads/nc/.

# Edit GrADS plotting script
sed -i "5s/.*/date='${DATE_STR1}PHT'/" bias_24hr_rain.gs
sed -i "6s/.*/date2='${DATE_STR1} PHT'/" bias_24hr_rain.gs
sed -i "7s/.*/date3='${FCST_YY}-${FCST_MM}-${FCST_DD}_$FCST_ZZ'/" bias_24hr_rain.gs
sed -i "8s~.*~outdir='${VAL_OUTDIR}'~" bias_24hr_rain.gs
sed -i "9s~.*~wrfdir='nc'~" bias_24hr_rain.gs

grads -pbc bias_24hr_rain.gs

# 24-hr GSMaP versus TRMM Climatology
mkdir -p "${OUTDIR}/climatology/${FCST_YY}${FCST_MM}${FCST_DD}/$FCST_ZZ"

cd "$SCRIPT_DIR/grads" || exit

# Edit GrADS plotting script
DATE_STRM=$(date -d "${FCST_YY}-${FCST_MM}-${FCST_DD} $FCST_ZZ:00:00 8 hours" +'%Y-%B-%d_%H')
read -r FCST_YY_PHT2 FCST_MM_PHT2 FCST_DD_PHT2 FCST_HH_PHT2 <<<"${DATE_STR1//[-_]/ }"
DATE_STR2=$(date -d "${FCST_YY}-${FCST_MM}-${FCST_DD} $FCST_ZZ:00:00 32 hours" +'%Y-%m-%d_%H')

sed -i "1s/.*/date='${DATE_STR1}PHT'/" gsmap_clim.gs
sed -i "2s~.*~d1title='${DATE_STR1} to ${DATE_STR2} PHT'~" gsmap_clim.gs
sed -i "3s~.*~outdir='${OUTDIR}/climatology/${FCST_YY}${FCST_MM}${FCST_DD}/$FCST_ZZ'~" gsmap_clim.gs
sed -i "4s/.*/date2='${DATE_STR1} PHT'/" gsmap_clim.gs
sed -i "6s~.*~'sdfopen ${VAL_DIR}/gsmap/nc/gsmap_${GSMAP_DATA}_${FCST_YY}-${FCST_MM}-${FCST_DD}_${FCST_ZZ}_ph.nc'~" gsmap_clim.gs
sed -i "9s~.*~climdir='${MAINDIR}/climatology/frJulie/01_forForecasting'~" gsmap_clim.gs
sed -i "10s~.*~month='${FCST_MM_PHT}'~" gsmap_clim.gs
sed -i "11s~.*~monname='${FCST_MM_PHT2}'~" gsmap_clim.gs

grads -pbc gsmap_clim.gs

# 24-hr timeseries plot (WRF, GFS, GSMaP)
cd "$VAL_DIR/python" || exit

# Edit concatenating csv script
sed -i "4s/.*/yyyymmdd = '${FCST_YY_PHT}-${FCST_MM_PHT}-${FCST_DD_PHT}'/" concat_rain.py
sed -i "5s/.*/init = '${FCST_HH_PHT}'/" concat_rain.py
sed -i "6s~.*~IN_DIR = '${VAL_OUTDIR}'~" concat_rain.py
sed -i "7s~.*~OUT_DIR = '${VAL_OUTDIR}'~" concat_rain.py

# Concatenate csv
$PYTHON concat_rain.py

# Edit time series plotting script
sed -i "7s/.*/yyyymmdd = '${FCST_YY_PHT}-${FCST_MM_PHT}-${FCST_DD_PHT}'/" timeseries_plot.py
sed -i "8s/.*/init = '${FCST_HH_PHT}'/" timeseries_plot.py
sed -i "9s~.*~FCST_DIR = '${OUTDIR}/web/json'~" timeseries_plot.py
sed -i "10s~.*~CSV_DIR = '${VAL_OUTDIR}'~" timeseries_plot.py
sed -i "11s~.*~OUT_DIR = '${VAL_OUTDIR}'~" timeseries_plot.py
sed -i "12s~.*~CLIM_DIR = '${VAL_DIR}/aws/csv'~" timeseries_plot.py
sed -i "13s/.*/month = '${FCST_MM_PHT}'/" timeseries_plot.py
sed -i "14s/.*/stn = '${STATION_ID}'/" timeseries_plot.py
sed -i "15s/.*/station = '${STATION_NAME}'/" timeseries_plot.py
sed -i "16s/.*/city_stn = '${CITY_ID}'/" timeseries_plot.py

# Plot 24hr time series
$PYTHON timeseries_plot.py

# Edit time series plotting script

# Plot 5-day time series WRF, AWS, and GSMaP
$PYTHON timeseries_plot_stations.py

# Plot statistical error metrics (month summary only, runs every 5th day of month)
$PYTHON scalar_meaures.py

echo "--------------------------"
echo " Done with comparison!    "
echo "--------------------------"
# -------------------------------------------- #
#            CONTINGENCY TABLE                 #
# -------------------------------------------- #
echo "---------------------------------"
echo " Processing contingency plot...  "
echo "---------------------------------"

cd "$VAL_DIR/grads/nc" || exit
$CDO remapbil,wrf_24hr_rain_day1_${DATE_STR1}PHT.nc gsmap_24hr_rain_day1_${DATE_STR1}PHT.nc gsmap_24hr_rain_day1_${DATE_STR1}PHT_re.nc

cd "$VAL_DIR/contingency" || exit

# Edit contingency script
sed -i "4s/.*/yyyymmdd = '${FCST_YY_PHT}-${FCST_MM_PHT}-${FCST_DD_PHT}'/" forecast_verification.py
sed -i "5s/.*/init = '${FCST_HH_PHT}'/" forecast_verification.py
sed -i "6s~.*~EXTRACT_DIR = '${VAL_DIR}/grads/nc'~" forecast_verification.py
sed -i "7s~.*~OUT_DIR = '${VAL_OUTDIR}'~" forecast_verification.py

# Plot contingency table
$PYTHON forecast_verification.py

# only executes during Sundays
$PYTHON forecast_verification_week_and_month_average.py

echo "---------------------------"
echo " Done with contingency!    "
echo "---------------------------"

# -------------------------------------------- #
#              CLEAN UP FILES                  #
# -------------------------------------------- #
# rm ${VAL_DIR}/gsmap/nc/*.nc
rm ${VAL_DIR}/gsmap/log/*.log
rm ${VAL_DIR}/gfs/nc/${FCST_YY}${FCST_MM}${FCST_DD}/${FCST_ZZ}/*.nc
echo "----------------------"
echo " Validation finished! "
echo "----------------------"
cd "$VAL_DIR" || exit
