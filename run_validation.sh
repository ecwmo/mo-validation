#!/bin/bash
#export FCST_YYYYMMDD="20200310"; export FCST_ZZ="00"; . $HOME/forecast/set_cron_env.sh; . $SCRIPT_DIR/set_date_vars.sh; . /home/modelman/forecast/validation/run_validation.sh
PYTHONCONDA=/home/miniconda3/envs/toolbox/bin/python
CDO=/opt/tools/nc/cdo
export VAL_DIR=$MAINDIR/validation
#export VAL_OUTDIR=$VAL_DIR/output/${FCST_YY}${FCST_MM}${FCST_DD}/$FCST_ZZ
export VAL_OUTDIR=${OUTDIR}/validation/${FCST_YY}${FCST_MM}${FCST_DD}/$FCST_ZZ
# options : gauge , nrt , now [can only be run at 9:00 PHT sharp]
export GSMAP_DATA="gauge"
export STATION_ID="MOIP"
export STATION_NAME="Manila Observatory"
export CITY_ID="NCR"

DATE_STR1=$(date -d "${FCST_YY}-${FCST_MM}-${FCST_DD} $FCST_ZZ:00:00 8 hours" +'%Y-%m-%d_%H')
read FCST_YY_PHT FCST_MM_PHT FCST_DD_PHT FCST_HH_PHT <<< ${DATE_STR1//[-_]/ }
# -------------------------------------------- #
#                 GSMaP                        #
# -------------------------------------------- #


echo "--------------------------"
echo " Processing GSMaP files  "
echo "--------------------------"

cd ${VAL_DIR}/gsmap

rm ${VAL_DIR}/gsmap/dat/gsmap_nrt.${FCST_YY}${FCST_MM}${FCST_DD}*.dat
# Download GSMaP data
./download_gsmap.aria2.sh 

# Convert GSMaP .dat files to .nc
./convert_gsmap_nc.sh

# Plot GSMaP
mkdir -p $VAL_OUTDIR
cd ${VAL_DIR}/grads

# Edit GrADS plotting script

sed -i "1s/.*/date='${DATE_STR1}PHT'/" gsmap_24hr_rain.gs
sed -i "2s/.*/date2='${DATE_STR1} PHT'/" gsmap_24hr_rain.gs
sed -i "3s/.*/date3='${FCST_YY}-${FCST_MM}-${FCST_DD}_$FCST_ZZ'/" gsmap_24hr_rain.gs
sed -i "4s~.*~outdir='${VAL_OUTDIR}'~" gsmap_24hr_rain.gs
sed -i "5s/.*/data='${GSMAP_DATA}'/" gsmap_24hr_rain.gs
sed -i "6s~.*~'sdfopen ${VAL_DIR}/gsmap/nc/gsmap_'data'_'date3'.nc'~" gsmap_24hr_rain.gs

grads -pbc gsmap_24hr_rain.gs

echo "--------------------------"
echo " Done with GSMaP!         "
echo "--------------------------"
# -------------------------------------------- #
#                   GFS                        #
# -------------------------------------------- #
echo "--------------------------"
echo " Processing GFS files...  "
echo "--------------------------"

cd ${VAL_DIR}/gfs

# Convert GFS precipitation grb files to .nc
./convert_gfs_nc.sh

# Plot GFS
mkdir -p $VAL_OUTDIR
cd ${VAL_DIR}/grads

# Edit GrADS plotting script
DATE_STR1=$(date -d "${FCST_YY}-${FCST_MM}-${FCST_DD} $FCST_ZZ:00:00 8 hours" +'%Y-%m-%d_%H')
read FCST_YY_PHT FCST_MM_PHT FCST_DD_PHT FCST_HH_PHT <<< ${DATE_STR1//[-_]/ }
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
9cho "---------------------------------"
echo " Processing comparison plots...  "
echo "---------------------------------"

# 24-hr difference plot (WRF-GSMaP, GFS-GSMaP)
cd ${VAL_DIR}/grads

ln -s ${WRF_ENS}/wrffcst_d01_${FCST_YY}-${FCST_MM}-${FCST_DD}_${FCST_ZZ}_ens.nc ${VAL_DIR}/grads/nc/.

# Edit GrADS plotting script
sed -i "5s/.*/date='${DATE_STR1}PHT'/" bias_24hr_rain.gs
sed -i "6s/.*/date2='${DATE_STR1} PHT'/" bias_24hr_rain.gs
sed -i "7s/.*/date3='${FCST_YY}-${FCST_MM}-${FCST_DD}_$FCST_ZZ'/" bias_24hr_rain.gs
sed -i "8s~.*~outdir='${VAL_OUTDIR}'~" bias_24hr_rain.gs
sed -i "9s~.*~wrfdir='nc'~" bias_24hr_rain.gs

grads -pbc bias_24hr_rain.gs

# 24-hr GSMaP versus TRMM Climatology
mkdir -p ${OUTDIR}/climatology/${FCST_YY}${FCST_MM}${FCST_DD}/$FCST_ZZ

cd ${SCRIPT_DIR}/grads

# Edit GrADS plotting script
DATE_STRM=$(date -d "${FCST_YY}-${FCST_MM}-${FCST_DD} $FCST_ZZ:00:00 8 hours" +'%Y-%B-%d_%H')
read FCST_YY_PHT2 FCST_MM_PHT2 FCST_DD_PHT2 FCST_HH_PHT2 <<< ${DATE_STR1//[-_]/ }
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
cd ${VAL_DIR}/python

# Edit concatenating csv script
sed -i "4s/.*/yyyymmdd = '${FCST_YY_PHT}-${FCST_MM_PHT}-${FCST_DD_PHT}'/" concat_rain.py
sed -i "5s/.*/init = '${FCST_HH_PHT}'/" concat_rain.py
sed -i "6s~.*~IN_DIR = '${VAL_OUTDIR}'~" concat_rain.py
sed -i "7s~.*~OUT_DIR = '${VAL_OUTDIR}'~" concat_rain.py

# Concatenate csv
$PYTHONCONDA concat_rain.py

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
export MPLBACKEND="agg"; $PYTHONCONDA timeseries_plot.py

# # Get hourly 5-day data over stations
rm -rf $VAL_OUTDIR/gsmap_5days*.csv
$PYTHONCONDA extract_points_gsmap.py

# Edit time series plotting script

# Plot 5-day time series WRF, AWS, and GSMaP
export MPLBACKEND="agg"; $PYTHONCONDA timeseries_plot_stations.py

echo "--------------------------"
echo " Done with comparison!    "
echo "--------------------------"
# -------------------------------------------- #
#            CONTINGENCY TABLE                 #
# -------------------------------------------- #
echo "---------------------------------"
echo " Processing contingency plot...  "
echo "---------------------------------"

cd ${VAL_DIR}/grads/nc
$CDO remapbil,wrf_24hr_rain_day1_${DATE_STR1}PHT.nc gsmap_24hr_rain_day1_${DATE_STR1}PHT.nc gsmap_24hr_rain_day1_${DATE_STR1}PHT_re.nc

cd ${VAL_DIR}/contingency

# Edit contingency script
sed -i "4s/.*/yyyymmdd = '${FCST_YY_PHT}-${FCST_MM_PHT}-${FCST_DD_PHT}'/" forecast_verification.py
sed -i "5s/.*/init = '${FCST_HH_PHT}'/" forecast_verification.py
sed -i "6s~.*~EXTRACT_DIR = '${VAL_DIR}/grads/nc'~" forecast_verification.py
sed -i "7s~.*~OUT_DIR = '${VAL_OUTDIR}'~" forecast_verification.py

# Plot contingency table
export MPLBACKEND="agg"; $PYTHONCONDA forecast_verification.py

# only executes during Sundays
export MPLBACKEND="agg"; $PYTHONCONDA forecast_verification_7day_average.py

echo "---------------------------"
echo " Done with contingency!    "
echo "---------------------------"

# -------------------------------------------- #
#              CLEAN UP FILES                  #
# -------------------------------------------- #
# rm ${VAL_DIR}/grads/nc/*.nc
rm ${VAL_DIR}/gsmap/dat/*.dat
# rm ${VAL_DIR}/gsmap/nc/*.nc
rm ${VAL_DIR}/gsmap/log/*.log
rm ${VAL_DIR}/gfs/nc/${FCST_YY}${FCST_MM}${FCST_DD}/${FCST_ZZ}/*.nc 
echo "----------------------"
echo " Validation finished! "
echo "----------------------"
cd ${VALDIR}
