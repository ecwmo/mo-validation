import sys
import getopt
import pytz
from pathlib import Path
import pandas as pd

tz = pytz.timezone("Asia/Manila")


def proc(in_dir, out_dir):
    df_stat = pd.read_csv("./station_id.csv", names=["stations"])
    stations = df_stat["stations"].tolist()

    yyyymmdd = in_dir.parent.name
    zz = in_dir.name
    init_dt = pd.to_datetime(
        f"{yyyymmdd}_{zz}", format="%Y%m%d_%H", utc=True
    ).astimezone(tz)
    init_dt_str = init_dt.strftime("%Y-%m-%d_%H")

    print(f"Concatinating data at {init_dt_str}PHT...")
    for stn in stations:
        print(f"  for {stn} station...")

        df_gfs = pd.read_csv(
            in_dir / f"gfs_{init_dt_str}PHT_{stn}_pr.csv", names=["gfs"]
        )
        df_gsmap = pd.read_csv(
            in_dir / f"gsmap_{init_dt_str}PHT_{stn}_pr.csv", names=["gsmap"]
        )

        frames = [df_gfs, df_gsmap]
        result = pd.concat(frames, axis=1)

        # NOTE: the missing value is replaced to 0 for now (2021 May 05 - gela)
        # result= result.replace(-999000000.0,0)
        out_file = out_dir / f"{stn}_gfs_gsmap_{init_dt_str}PHT.csv"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        result.to_csv(str(out_file), index=False)


if __name__ == "__main__":
    in_dir = Path("dat")
    out_dir = Path("")
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hi:o:", ["idir=", "odir="])
    except getopt.GetoptError:
        print("concat_rain.py -i <input file> -o <output dir>")
        sys.exit(2)
    for opt, arg in opts:
        if opt == "-h":
            print("concat_rain.py -i <input file> -o <output dir>")
            sys.exit()
        elif opt in ("-i", "--idir"):
            in_dir = Path(arg)
        elif opt in ("-o", "--odir"):
            out_dir = Path(arg)
            out_dir.mkdir(parents=True, exist_ok=True)
    proc(in_dir, out_dir)
