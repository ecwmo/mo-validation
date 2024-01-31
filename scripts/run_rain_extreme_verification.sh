#!/bin/bash

echo "---------------------------------------------"
echo "     Starting WRF Rainfall verification      "
echo "---------------------------------------------"

# -------------------------------------------- #
#              Calculating                     #
# -------------------------------------------- #

# source "$SCRIPT_DIR/set_date_vars.sh"

cd "$VAL_DIR/scripts/rainfall_extremes" || exit

out_dir=$OUTDIR/validation/extreme

# Usage of  Py script: set -w --plot after python script to plot spatial map and roebber's diagram
$PYTHON rain_extremes_verification.py --forecast_days 5 --ari 5 -o "$out_dir"

echo "---------------------------------"
echo " Calculation and plots finished! "
echo "---------------------------------"
cd "$MAINDIR" || exit

#  . $HOME/forecast/set_cron_env.sh; . $HOME/forecast/scripts/set_date_vars.sh; . $VAL_DIR/scripts/run_rain_extreme_verification.sh