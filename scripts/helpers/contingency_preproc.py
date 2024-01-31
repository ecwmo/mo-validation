from ARI import *
from contingency_config import * 
from pathlib import Path

_wrf_dir = Path(os.getenv("WRF_NC_DIR"))
_gsmap_dir =  Path(os.getenv("GSMAP_NC_DIR"))

class dataset_op:
    """Class for pprec-processing forecast and observed ari to calculate their contingencies
    using contingency_ari.py. Used in rain_extremes_verification.py
    
    Returns
    -------
    
    xr.Datarray of observed and forecasted ARI
    
    Example usage
    --------------
    from contingency_preproc import dataset_op
    _datasets = dataset_op(forecast_days)
    
    """
    
    def __init__(
        self,
        forecast_days=None
    ):
         if forecast_days is None:
             self._forecast_days =  1
         else:
             self._forecast_days = forecast_days
             
         self._forecast, self._observed = self._get_forecast_obs()
         self._ari_forecast, self._ari_observed = self._get_ari()
    
    @property
    def forecast(self):
        return self._forecast
    
    @property
    def observed(self):
        return self._observed
    
    @property
    def ari_forecast(self):
        return self._ari_forecast
    
    @property
    def ari_observed(self):
        return self._ari_observed
    
    
    def _get_forecast_obs(self):
        _config = config_op()
        _forecast_day = _config.forecast_day
        _forecast_hour = _config.forecast_hour
        _forecast_date_str = _config.forecast_date_str
        
        _wrf_ds = (xr.open_dataset(_wrf_dir / f"wrf_{_forecast_date_str}.nc")[["rain"]]
                .resample(time="24H", base=int(_forecast_hour))
                .sum("time")
                .isel(time=slice(self._forecast_days)))
        
        _dates = _wrf_ds.time.dt.strftime("%Y-%m-%d_%H").values
        _gsmap_files = [_gsmap_dir / f"gsmap_gauge_{date}.nc" for date in _dates]
        
        _gsmap_ds = (xr.open_mfdataset(_gsmap_files, concat_dim="time", combine="nested"))
        _gsmap_ds = _gsmap_ds.load().resample(time="24H", base=int(_forecast_hour)).sum("time")
        _gsmap_ds = _gsmap_ds.isel(time=slice(self._forecast_days))
        
        return (_wrf_ds, _gsmap_ds)
    
    def _get_ari(self):
        
        _wrf_ds, _gsmap_ds = self._get_forecast_obs()
        _ari_wrf = wrf_ari(_wrf_ds)
        _ari_gsmap = gsmap_ari(_gsmap_ds)
        
        return (_ari_wrf, _ari_gsmap)

class dataset_lead:
    def __init__(
        self,
    ):
         self._forecast, self._observed = self._get_forecast_obs()
         self._ari_forecast, self._ari_observed = self._get_ari()
    
    @property
    def forecast(self):
        return self._forecast
    
    @property
    def observed(self):
        return self._observed
    
    @property
    def ari_forecast(self):
        return self._ari_forecast
    
    @property
    def ari_observed(self):
        return self._ari_observed
    
    
    def _get_forecast_obs(self):
        _config = config_lead()
        _forecast_day = _config.forecast_day
        _forecast_hour = _config.forecast_hour
        _forecast_date_str = _config.forecast_date_str
        _forecast_dates = _config.forecast_dates
        _fnl_files = _config.fnl_files
        _forecast_index = _config.forecast_index
        
        _gsmap_ds, _wrf_ds = [], []
        for idx,file in zip(_forecast_index, _fnl_files):
            wrf = (xr.open_dataset(file)[["rain"]]
                .resample(time="24H", base=int(_forecast_hour))
                .sum("time")
                .sel(time=_forecast_date_str)
                    )
            wrf = (wrf
                    .assign(time=pd.to_datetime(_forecast_dates[idx], format="%Y-%m-%d_%H"))
                    .expand_dims("time"))
            
            gsmap = (xr.open_dataset(_gsmap_dir / f"gsmap_gauge_{_forecast_dates[-1]}.nc")
                    .resample(time="24H", base=int(_forecast_hour))
                    .sum("time")
                    .isel(time=0))
            gsmap = (gsmap
                    .assign(time=pd.to_datetime(_forecast_dates[idx], format="%Y-%m-%d_%H"))
                    .expand_dims("time"))
            
            _gsmap_ds.append(gsmap)
            _wrf_ds.append(wrf)
        
        _wrf_ds = xr.concat(_wrf_ds, dim="time")
        _gsmap_ds = xr.concat(_gsmap_ds, dim="time")
        
        return (_wrf_ds, _gsmap_ds)
    
    def _get_ari(self):
        
        _wrf_ds, _gsmap_ds = self._get_forecast_obs()
        _ari_wrf = wrf_ari(_wrf_ds)
        _ari_gsmap = gsmap_ari(_gsmap_ds)
        
        return (_ari_wrf, _ari_gsmap)
