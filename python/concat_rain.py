#!/usr/bin/env python
# coding: utf-8

yyyymmdd = '2022-03-09'
init = '08'
IN_DIR = '/home/modelman/forecast/output/validation/20220309/00'
OUT_DIR = '/home/modelman/forecast/output/validation/20220309/00'

# combine gfs and gsmap data into one csv
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df_stat = pd.read_csv(f'./station_id.csv',names=['stations'])
stations = df_stat['stations'].tolist()
for stn in stations:
    print(f"Concatinating data at {yyyymmdd}_{init}PHT...")

    df_gfs = pd.read_csv( Path(IN_DIR)/f'gfs_{yyyymmdd}_{init}PHT_{stn}_pr.csv',names=['gfs'])
    df_gsmap = pd.read_csv( Path(IN_DIR)/f'gsmap_{yyyymmdd}_{init}PHT_{stn}_pr.csv',names=['gsmap'])

    frames = [df_gfs,df_gsmap]
    result = pd.concat(frames, axis=1)

    #NOTE: the missing value is replaced to 0 for now (2021 May 05 - gela)
    #result= result.replace(-999000000.0,0)
    out_file = Path(OUT_DIR) / f'{stn}_gfs_gsmap_{yyyymmdd}_{init}PHT.csv'
    out_file.parent.mkdir(parents=True,exist_ok=True)
    result.to_csv(str(out_file), index=False)
