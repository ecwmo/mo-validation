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

# -------------------------------------------- #
#                 GSMaP                        #
# -------------------------------------------- #

echo "--------------------------"
echo " Processing GSMaP files  "
echo "--------------------------"

cd "$MAINDIR/scripts" || exit

FILE=$(find "${GSMAP_NC_DIR}"/*"${FCST_YY_GSMAP}"-"${FCST_MM_GSMAP}"-"${FCST_DD_GSMAP}"_"${FCST_ZZ_GSMAP}"* | head -1)

if [ $DOWNLOAD_INPUT -eq 1 ] && [ ! -f "$FILE" ]; then

  mkdir -p "$GSMAP_TEMP_DIR"
  # Download GSMaP data
  ./download_gsmap.sh

  cd "$SCRIPT_DIR/python" || exit
  # Convert GSMaP .gz files to .nc
  $PYTHON convert_gsmap_nc.py -i "$GSMAP_TEMP_DIR" -o "$GSMAP_NC_DIR"
  # Remove .gz files
  rm -rf "${GSMAP_TEMP_DIR?:}"
fi

cd "$VAL_DIR/scripts/gsmap" || exit

# Plot GSMaP
gsmap_in_nc=$GSMAP_NC_DIR/gsmap_${GSMAP_DATA}_${FCST_YY}-${FCST_MM}-${FCST_DD}_${FCST_ZZ}_day.nc
$PYTHON plot_gsmap_24hr_rain.py -i "$gsmap_in_nc" -o "$VAL_OUTDIR"

# Extract GSMaP
gsmap_in_nc=$GSMAP_NC_DIR/gsmap_${GSMAP_DATA}_${FCST_YY}-${FCST_MM}-${FCST_DD}_${FCST_ZZ}.nc
$PYTHON extract_gsmap_24hr_rain.py -i "$gsmap_in_nc" -o "$VAL_OUTDIR"

echo "--------------------------"
echo " Done with GSMaP!         "
echo "--------------------------"
# -------------------------------------------- #
#                   GFS                        #
# -------------------------------------------- #
echo "--------------------------"
echo " Processing GFS files...  "
echo "--------------------------"

cd "$VAL_DIR/scripts/gfs" || exit

# Convert GFS precipitation grb files to .nc
$PYTHON convert_gfs_nc.py -i "$GFSDIR" -o "$GFS_NC_DIR"

# Plot GFS
gfs_in_nc=$GFS_NC_DIR/gfs_${FCST_YY}-${FCST_MM}-${FCST_DD}_${FCST_ZZ}_day.nc
$PYTHON plot_gfs_24hr_rain.py -i "$gfs_in_nc" -o "$VAL_OUTDIR"
$PYTHON plot_gfs_acc_rain.py -i "$gfs_in_nc" -o "$VAL_OUTDIR"

# Extract GFS
gfs_in_nc=$GFS_NC_DIR/gfs_${FCST_YY}-${FCST_MM}-${FCST_DD}_${FCST_ZZ}.nc
$PYTHON extract_gfs_24hr_rain.py -i "$gfs_in_nc" -o "$VAL_OUTDIR"

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
cd "$VAL_DIR/scripts/compare" || exit
gsmap_in_nc=$GSMAP_NC_DIR/gsmap_${GSMAP_DATA}_${FCST_YY}-${FCST_MM}-${FCST_DD}_${FCST_ZZ}_day.nc
$PYTHON plot_24hr_rain_diff.py -i "$gsmap_in_nc" -o "$VAL_OUTDIR"

# 24-hr GSMaP versus TRMM Climatology
cd "$VAL_DIR/scripts/gsmap" || exit
gsmap_in_nc=$GSMAP_NC_DIR/gsmap_${GSMAP_DATA}_${FCST_YY}-${FCST_MM}-${FCST_DD}_${FCST_ZZ}_day.nc
clim_out_dir="${OUTDIR}/climatology/${FCST_YY}${FCST_MM}${FCST_DD}/$FCST_ZZ"
mkdir -p "clim_out_dir"
$PYTHON plot_gsmap_clim.py -i "$gsmap_in_nc" -o "$clim_out_dir"

# 24-hr timeseries plot (WRF, GFS, GSMaP)
cd "$VAL_DIR/python" || exit

# Concatenate csv
$PYTHON concat_rain.py -i "$VAL_OUTDIR" -o "$VAL_OUTDIR"

# Plot 24hr time series
$PYTHON plot_ts.py -i "$VAL_OUTDIR" -o "$VAL_OUTDIR"

# Edit time series plotting script

# Plot 5-day time series WRF, AWS, and GSMaP
$PYTHON plot_stations_ts.py -o "$VAL_OUTDIR"

# Plot statistical error metrics (month summary only, runs every 5th day of month)
$PYTHON scalar_measures.py -o "$VAL_OUTDIR"

echo "--------------------------"
echo " Done with comparison!    "
echo "--------------------------"
# -------------------------------------------- #
#            CONTINGENCY TABLE                 #
# -------------------------------------------- #
echo "---------------------------------"
echo " Processing contingency plot...  "
echo "---------------------------------"

cd "$VAL_DIR/contingency" || exit

# Plot contingency table
$PYTHON forecast_verification.py -o "$VAL_OUTDIR"

# only executes during Sundays
$PYTHON forecast_verification_week_and_month_average.py

echo "---------------------------"
echo " Done with contingency!    "
echo "---------------------------"

cd "$VAL_DIR" || exit

# Upload files
"$VAL_DIR"/web_upload.sh

# -------------------------------------------- #
#              CLEAN UP FILES                  #
# -------------------------------------------- #
# rm ${VAL_DIR}/gsmap/nc/*.nc
# rm ${VAL_DIR}/gsmap/log/*.log
# rm ${VAL_DIR}/gfs/nc/${FCST_YY}${FCST_MM}${FCST_DD}/${FCST_ZZ}/*.nc
echo "----------------------"
echo " Validation finished! "
echo "----------------------"
