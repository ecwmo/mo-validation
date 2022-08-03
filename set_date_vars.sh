#!/usr/bin/env bash

########## Dynamic Variables ##########
# Get date in UTC minus offset (cron at 12:45 PHT the next day)
OFFSET=28
if [ -z "$FCST_YYYYMMDD" ]; then
  FCST_YYYYMMDD=$(date -d "$OFFSET hours ago" -u +"%Y%m%d")
  export FCST_YYYYMMDD
fi

if [ -z "$FCST_ZZ" ]; then
  FCST_ZZ=$(date -d "$OFFSET hours ago" -u +"%H")
  export FCST_ZZ
fi

export FCST_YY=${FCST_YYYYMMDD:0:4}
export FCST_MM=${FCST_YYYYMMDD:4:2}
export FCST_DD=${FCST_YYYYMMDD:6:2}

# Get end date
FCST_YYYYMMDD2=$(date -d "${FCST_YY}-${FCST_MM}-${FCST_DD} $FCST_ZZ:00:00 ${WRF_FCST_DAYS} days" +'%Y%m%d')
export FCST_YYYYMMDD2
FCST_ZZ2=$(date -d "${FCST_YY}-${FCST_MM}-${FCST_DD} $FCST_ZZ:00:00 ${WRF_FCST_DAYS} days" +'%H')
export FCST_ZZ2
export FCST_YY2=${FCST_YYYYMMDD2:0:4}
export FCST_MM2=${FCST_YYYYMMDD2:4:2}
export FCST_DD2=${FCST_YYYYMMDD2:6:2}

export VAL_OUTDIR=${OUTDIR}/validation/${FCST_YY}${FCST_MM}${FCST_DD}/$FCST_ZZ

export GFSDIR=$MAINDIR/input/gfs_files/$FCST_YYYYMMDD/$FCST_ZZ
export NUM_FILES=$((WRF_FCST_DAYS * 24 + 1))

# set variables for download_gsmap.sh
export FCST_YYYYMMDD_GSMAP=$FCST_YYYYMMDD
export FCST_ZZ_GSMAP=$FCST_ZZ
export FCST_YY_GSMAP=$FCST_YY
export FCST_MM_GSMAP=$FCST_MM
export FCST_DD_GSMAP=$FCST_DD
export GSMAP_TEMP_DIR="$TEMP_DIR/gsmap/$FCST_YYYYMMDD_GSMAP/$FCST_ZZ_GSMAP"

########## Dynamic Variables ##########
