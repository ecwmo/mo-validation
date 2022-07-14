import sys
import getopt
import pytz
from pathlib import Path
import pandas as pd
import salem

tz = pytz.timezone("Asia/Manila")
var_name = "precip"


def extract(in_file, out_dir):
    stn_df = pd.read_csv(Path("../../input/csv/station.csv"))
    ds = salem.open_xr_dataset(in_file)

    init_dt = pd.to_datetime(ds.time.values[0], utc=True).astimezone(tz)
    # init_dt_str = init_dt.strftime("%Y-%m-%d %H")
    init_dt_str2 = init_dt.strftime("%Y-%m-%d_%H")

    for irow, row in stn_df.iterrows():
        df = ds.sel(lat=row["lat"], lon=row["lon"], method="nearest").to_dataframe()
        out_file = out_dir / f"gsmap_{init_dt_str2}PHT_{row['name']}.csv"
        df[var_name].head(24).to_csv(out_file, index=False, header=False)


if __name__ == "__main__":
    in_file = Path("dat")
    out_dir = Path("")
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hi:o:", ["ifile=", "odir="])
    except getopt.GetoptError:
        print("extract_gsmap_24hr_rain.py -i <input file> -o <output dir>")
        sys.exit(2)
    for opt, arg in opts:
        if opt == "-h":
            print("extract_gsmap_24hr_rain.py -i <input file> -o <output dir>")
            sys.exit()
        elif opt in ("-i", "--ifile"):
            in_file = Path(arg)
        elif opt in ("-o", "--odir"):
            out_dir = Path(arg)
            out_dir.mkdir(parents=True, exist_ok=True)
    extract(in_file, out_dir)
