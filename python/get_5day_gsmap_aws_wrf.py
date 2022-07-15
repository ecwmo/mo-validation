# Description: get 5 day wrf, aws, ang gsmap data
# Author: Kevin Henson
# Last edited: June 17, 2022

import os
from pathlib import Path
from datetime import timedelta
import pandas as pd
import numpy as np
import salem


gsmap_dir = Path(os.getenv("GSMAP_NC_DIR"))
aws_dir = Path(os.getenv("AWS_DIR"))
wrf_json_dir = Path(os.getenv("WRF_JSON_DIR"))


def get_5day_gsmap_aws_wrf(dt, stn):
    # Intialize dataframe for each station
    df_gsmap = pd.DataFrame(
        columns=[
            "time",
            "precip",
        ]
    )
    aws_cols = ["name", "timestamp", "rr", "temp", "rh", "hi"]
    df_aws = pd.DataFrame(columns=aws_cols)

    # Loop through past 5 days
    for day in reversed(np.arange(1, 6)):
        # Set date variable
        dt_var = dt - timedelta(int(day))

        # Access gsmap file and data
        gsmap_fn = gsmap_dir / f"gsmap_gauge_{dt_var}_00.nc"
        if gsmap_fn.is_file():
            gsmap_df = salem.open_xr_dataset(gsmap_fn)
            df_temp_gsmap = gsmap_df.sel(
                lon=stn["lon"], lat=stn["lat"], method="nearest"
            ).to_dataframe()
            df_temp_gsmap = df_temp_gsmap["precip"].reset_index(level="time")

            # Append daily data
            df_gsmap = pd.concat([df_gsmap, df_temp_gsmap])

        aws_fn = aws_dir / f"stn_obs_24hr_{dt_var}_08PHT.csv"
        if aws_fn.is_file():
            aws_df = pd.read_csv(aws_fn, usecols=aws_cols, na_values="-999.000000")
            aws_df = aws_df[aws_df["name"] == stn["name"]]

            # Append daily data
            df_aws = pd.concat([df_aws, aws_df])

    df_gsmap = df_gsmap.reset_index(drop=True)
    df_aws = df_aws.reset_index(drop=True)

    # Add station name column
    df_gsmap.insert(loc=0, column="name", value=stn["name"])

    # Initialize wrf data table
    wrf_vars = {"timestamp": [], "rain": [], "temp": [], "rh": [], "hi": []}

    # Set date variables
    dt_var = dt - timedelta(5)
    dt_var_str = str(dt_var)
    date_str = str(dt)
    dt_gsmap = dt - timedelta(1)
    date_str_gsmap = str(dt_gsmap)

    # Access wrf fcst from 5 days ago
    wrf_fn = wrf_json_dir / f"forecast_lufft_stations_{dt_var_str}_08PHT.json"
    if wrf_fn.is_file():
        df_wrf = pd.read_json(wrf_fn, orient="index")

        # Get 5-day data from wrf fcst json file

        for i in np.arange(0, 120, 1):
            for key in wrf_vars.keys():
                wrf_vars[key].append(df_wrf["forecast"][stn["name"]]["hr"][i][key])

                # Set missing values to NaN
                wrf_vars[key] = [np.nan if v is None else v for v in wrf_vars[key]]

    df_wrf = pd.DataFrame(wrf_vars)
    df_wrf.insert(loc=0, column="name", value=stn["name"])

    # Fill-in missing timesteps
    if len(df_wrf) > 0:
        df_wrf["timestamp"] = df_wrf["timestamp"] + "+08:00"
        df_wrf["timestamp"] = pd.to_datetime(df_wrf["timestamp"])
        start = pd.to_datetime(dt_var_str + " 08:00:00+08:00")
        end = pd.to_datetime(date_str + " 07:00:00+08:00")
        dates = pd.date_range(start=start, end=end, freq="1H")

        df_wrf = (
            df_wrf.set_index("timestamp")
            .reindex(dates)
            .reset_index()
            .reindex(columns=df_wrf.columns)
        )
        cols = df_wrf.columns.difference(list(wrf_vars.keys())[1:])
        df_wrf[cols] = df_wrf[cols].ffill()
        df_wrf["timestamp"] = dates

    if len(df_aws) > 0:
        df_aws["timestamp"] = pd.to_datetime(df_aws["timestamp"])
        start = pd.to_datetime(dt_var_str + " 09:00:00+08:00")
        end = pd.to_datetime(date_str + " 08:00:00+08:00")
        dates = pd.date_range(start=start, end=end, freq="1H")

        df_aws = (
            df_aws.set_index("timestamp")
            .reindex(dates)
            .reset_index()
            .reindex(columns=df_aws.columns)
        )
        cols = df_aws.columns.difference(["rr", "temp", "rh", "hi"])
        df_aws[cols] = df_aws[cols].ffill()
        df_aws["timestamp"] = dates

    if len(df_gsmap) > 0:
        df_gsmap["time"] = pd.to_datetime(df_gsmap["time"])
        start = pd.to_datetime(dt_var_str + " 00:00:00")
        end = pd.to_datetime(date_str_gsmap + " 23:00:00")
        dates = pd.date_range(start=start, end=end, freq="1H")

        df_gsmap = (
            df_gsmap.set_index("time")
            .reindex(dates)
            .reset_index()
            .reindex(columns=df_gsmap.columns)
        )
        cols = df_gsmap.columns.difference(["precip"])
        df_gsmap[cols] = df_gsmap[cols].ffill()
        df_gsmap["time"] = dates

    print("Saved " + stn["name"] + " data")

    return df_wrf, df_aws, df_gsmap, dt_var_str
