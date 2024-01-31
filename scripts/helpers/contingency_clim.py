from ARI import *

class Contingency_clim:
    """Class for contingency based skill scores for each grid point in ARI than historgram 
    
    Parameters
    ----------
    observations : xarray.Dataset or xarray.DataArray
        Labeled array(s) over which to apply the function.
    forecasts : xarray.Dataset or xarray.DataArray
        Labeled array(s) over which to apply the function.
    
    Returns
    -------
    
    xarray.Dataset of observed, forecast, extremes, hits, miss, false alarm, and miss
    table summaraizing results of the contingecny and skill metrics 
    
    Example usage
    --------------
    
    test = Contingency(gsmap_ari, wrf_ari, 1)
    to call hits do " test.hits "
    
    """
    import warnings
    warnings.filterwarnings("ignore")

    def __init__(
        self,
        observed,
        forecasts,
    ):
        self._observed = observed.copy()
        self._forecasts = forecasts.copy()
        self._observed_extreme, self._forecast_extreme = self._get_model_agreement()[:2]
        self._hits, self._miss, self._false, self._non_event = self._get_contingency()
        self._table = self._get_table()
        
    @property
    def observed(self):
        return self._observed
    @property
    def forecasts(self):
        return self._forecasts
    @property
    def observe(self):
        return self._observed_extreme
    @property
    def forecast(self):
        return self._forecast_extreme
    @property
    def hits(self):
        return self._hits
    @property
    def miss(self):
        return self._miss
    @property
    def false(self):
        return self._false
    @property
    def non_event(self):
        return self._non_event
    @property
    def table(self):
        return self._table
    
    def _regrid_ds(self):
        _observe = self.observed
        _forecast = self.forecasts
        _trmm = xr.open_dataset(script_dir / "nc/trmm_1998-2015_clim.nc")
        
        _ref_grid = (xr.open_dataset(script_dir / "nc/trmm_domain_regrid.nc")
                    .sel(lon=slice(117.375, 126.375), lat=slice(5.125, 18.875))
                    .drop(("time_bnds", "time", "precipitation")))
        
        _observe_regrid = mask(regrid(_observe, _ref_grid))
        _forecast_regrid = mask(regrid(_forecast, _ref_grid))
        _trmm_regrid = mask(regrid(_trmm, _ref_grid))
        
        return (_observe_regrid, _forecast_regrid, _trmm_regrid)
    
    def _get_model_agreement(self):
        
        _observe, _forecast, _trmm = self._regrid_ds()
        
        _trmm2 = _trmm.sel(time=(_trmm.time.dt.month == _forecast.time.dt.month[0])).isel(time=0)
        _trmm2 = _trmm2.rename({"precipitation" : "rain"})
        
        _model_exceed = xr.where(_forecast.rain > _trmm2.rain, 1, np.nan)
        _model_exceed =  _model_exceed.to_dataset(name="rain")
        _model_counts = _model_exceed.where(_model_exceed == 1).sum("ens")
        
        _observe = _observe.rename({"precip" : "rain"})
        _observe_extreme = xr.where(_observe.rain > _trmm2.rain, 1, np.nan)
        _observe_extreme = _observe_extreme.to_dataset(name="rain")
        
        _forecast_extreme = xr.where(_model_counts.rain >= 2, 1, np.nan)
        _forecast_extreme = _forecast_extreme.to_dataset(name="rain")
        
        _observed_non = xr.where(_observe.rain < _trmm2.rain, 1, np.nan)
        _observed_non = _observed_non.to_dataset(name="rain")
        
        _forecast_non = xr.where(_model_counts.rain < 2, 1, np.nan)
        _forecast_non = _forecast_non.to_dataset(name="rain")
        
        return (_observe_extreme, _forecast_extreme, _observed_non, _forecast_non)
    
    def _get_contingency(self):
        
        _observe, _forecast, _observe_non, _forecast_non = self._get_model_agreement()
        _observe, _forecast = _observe["rain"], _forecast["rain"]
        _observe_non, _forecast_non = _observe_non["rain"], _forecast_non["rain"]
        
        _hits = xr.where(_observe == _forecast, 1, np.nan)
        
        _miss = xr.where(_observe.where(_observe == 1).isin(_forecast.where(_forecast == 1)), 1, np.nan)
        _miss = _miss.where((_miss - _hits) != 0)
        
        _false = _forecast.where( (_forecast - _observe) != 0)
        
        _non_event = xr.where(_forecast_non == _observe_non, 1, np.nan)
        
        _hits = _hits.to_dataset(name="hits")
        _miss = _miss.to_dataset(name="miss")
        _false = _false.to_dataset(name="false")
        _non_event = _non_event.to_dataset(name="non_event")
        
        return (_hits, _miss, _false, _non_event)
    
    def _get_table(self):
        
        _contigent_ds = xr.merge(self._get_contingency())
        _contingent_df = _contigent_ds.count(dim=["lon", "lat"]).to_dataframe()
        
        _contingent_df["BIAS"] = _contingent_df.apply(lambda x: (x["hits"] + x["false"]) / (x["hits"] + x["miss"]), axis=1)
        _contingent_df["POD"] = _contingent_df.apply(lambda x: x["hits"] / (x["hits"] + x["miss"]), axis=1)
        _contingent_df["FAR"] = _contingent_df.apply(lambda x: x["false"] / (x["hits"] + x["false"]), axis=1)
        _contingent_df["SR"] = _contingent_df.apply(lambda x: x["hits"] / (x["hits"] + x["false"]), axis=1)
        _contingent_df["CSI"] = _contingent_df.apply(lambda x: x["hits"] / (x["hits"] + x["false"] + x["miss"]), axis=1)
        _contingent_df["PCR"] = _contingent_df.apply(lambda x: x["non_event"] / (x["false"]+x["non_event"]), axis=1)

        _var_ls = ["BIAS", "POD", "FAR", "SR", "CSI", "PCR"]
        _contingent_df[_var_ls] = _contingent_df[_var_ls].round(3)

        return _contingent_df