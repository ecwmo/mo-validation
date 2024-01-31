import pandas as pd
import numpy as np
from pathlib import Path
import os
import glob

class config_op:
    """Class for setting configurations for contingency_preproc.py
    
    Returns
    -------
    
    Configuration dates for operational contingency and offline lead time contingency
    
    Example usage
    --------------
    
    from cintingency_config import config_op
    forecast_hour = config_op().forecast_hour
    
    """
    
    def __init__(self):
        self._forecast_day = os.getenv("FCST_YYYYMMDD")
        self._forecast_hour = os.getenv("FCST_ZZ")
        self._forecast_date_str = f"{self._forecast_day[:4]}-{self._forecast_day[4:6]}-{self._forecast_day[6:8]}_{self._forecast_hour}"
        self._forecast_date_str = (pd.to_datetime(self._forecast_date_str, format="%Y-%m-%d_%H") - pd.offsets.Day(1)).strftime("%Y-%m-%d_%H")

    @property
    def forecast_day(self):
        return self._forecast_day
    @property
    def forecast_hour(self):
        return self._forecast_hour
    @property
    def forecast_date_str(self):
        return self._forecast_date_str
    
class config_lead:
    def __init__(self):
        self._forecast_day = os.getenv("FCST_YYYYMMDD")
        self._forecast_hour = os.getenv("FCST_ZZ")
        self._forecast_date_str = f"{self._forecast_day[:4]}-{self._forecast_day[4:6]}-{self._forecast_day[6:8]}_{self._forecast_hour}"
        self._forecast_date_str = pd.to_datetime(self._forecast_date_str, format="%Y-%m-%d_%H")
        self._forecast_dates = pd.date_range(end=self._forecast_date_str, periods=5, freq="D").strftime("%Y-%m-%d_%H")
        self._fnl_files, self._forecast_index = self._get_files()

    @property
    def forecast_day(self):
        return self._forecast_day
    @property
    def forecast_hour(self):
        return self._forecast_hour
    @property
    def forecast_date_str(self):
        return self._forecast_date_str
    @property
    def forecast_dates(self):
        return self._forecast_dates
    @property
    def fnl_files(self):
        return self._fnl_files
    @property
    def forecast_index(self):
        return self._forecast_index

    def _get_files(self):
        
        from pathlib import Path
        _wrf_dir = Path(os.getenv("WRF_NC_DIR"))
        
        _init_files = [_wrf_dir / f"wrf_{date}.nc" for date in self._forecast_dates]
        _ref = [sorted(_wrf_dir.glob(f"*{date}*")) for date in self._forecast_dates]
        _ref = [num for sublist in _ref for num in sublist]
        _fnl_files = pd.Index(_init_files).intersection(_ref)
        _forecast_index = pd.Index(_init_files).get_indexer(_fnl_files)

        return (_fnl_files, _forecast_index)