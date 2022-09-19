#!/usr/bin/env bash

YY=${FCST_YYYYMMDD:0:4}
mm=${FCST_YYYYMMDD:4:2}
dd=${FCST_YYYYMMDD:6:2}

echo "--------------------------"
echo " Uploading files for web  "
echo "--------------------------"

SRCDIR=${OUTDIR}

web_dirs=("panahon.alapaap:websites/panahon-php" "panahon.linode:websites/panahon-php")

for web_dir in "${web_dirs[@]}"; do
  scp "$SRCDIR/validation/$YY$mm$dd/$FCST_ZZ"/*rain*".png" "${web_dir}/resources/validation/"
  scp "$SRCDIR/validation/$YY$mm$dd/$FCST_ZZ"/*aws*".png" "${web_dir}/resources/validation/"
done

echo "-----------------------------"
echo " Done uploading web files!!! "
echo "-----------------------------"
