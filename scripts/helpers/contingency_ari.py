from ARI import *

class Contingency_ari:
    """Class for contingency based skill scores for each grid point in ARI than historgram 
    
    Parameters
    ----------
    observations : xarray.Dataset or xarray.DataArray
        Labeled array(s) over which to apply the function.
    forecasts : xarray.Dataset or xarray.DataArray
        Labeled array(s) over which to apply the function.
    ari : filter used for considering extreme rainfall and non-extreme rainfall based on ari values in years
        Numerical object over which to apply the function to filter extreme and non-extreme.
    
    Returns
    -------
    
    xarray.Dataset of observed, forecast, extremes, hits, miss, false alarm, and miss
    table summaraizing results of the contingecny and skill metrics 
    
    Example usage
    --------------
    
    test = Contingency(gsmap_ari, wrf_ari, 1)
    to call hits do " test.hits "
    
    """
    
    def __init__(
        self,
        observed,
        forecasts,
        ari
    ):
        self._observed = observed.copy()
        self._forecasts = forecasts.copy()
        self._ari = ari
        self._extremes = self._get_extremes(ari)
        self._hits = self._get_hits()
        self._miss = self._get_miss()
        self._false = self._get_false()
        self._non_event = self._get_non_event(ari)
        self._table = self._get_table()
        
    @property
    def observed(self):
        return self._observed

    @property
    def forecasts(self):
        return self._forecasts
    
    @property
    def ari(self):
        return self._ari
    
    @property
    def extremes(self):
        return self._extremes
    
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
    
    
    def _get_extremes(self, ari):
        _forecast_ari = xr.where(self.forecasts.rain > ari, 1, np.nan).to_dataset(name="forecast")
        _observed_ari = xr.where(self.observed.rain > ari, 1, np.nan).to_dataset(name="observed")

        _extreme_ds =  xr.merge([_forecast_ari, _observed_ari])
        
        return _extreme_ds
    
    def _get_hits(self):
        
        _extreme_ds = self.extremes
        _hits = xr.where(_extreme_ds["forecast"] == (_extreme_ds["observed"]), 1, np.nan)

        return _hits.to_dataset(name="hits")
    
    def _get_false(self):
        
        _extreme_ds = self.extremes
        observe, forecast = _extreme_ds["observed"], _extreme_ds["forecast"]
        _false = forecast.where( (forecast - observe) != 0)
        
        return _false.to_dataset(name="false")
    
    def _get_miss(self):
        
        _extreme_ds = self.extremes
        _hits = self.hits["hits"]
        
        observe, forecast = _extreme_ds["observed"], _extreme_ds["forecast"]
        _miss = xr.where(observe.where(observe == 1).isin(forecast.where(forecast == 1)), 1, np.nan)
        _miss = _miss.where((_miss - _hits) != 0)
        
        return _miss.to_dataset(name="miss")
    
    def _get_non_event(self, ari):
        _forecast_ari = xr.where(self.forecasts.rain < ari, 1, np.nan).to_dataset(name="forecast")
        _observed_ari = xr.where(self.observed.rain < ari, 1, np.nan).to_dataset(name="observed")
        
        _non_event = xr.where(_forecast_ari["forecast"] == _observed_ari["observed"], 1, np.nan)
        
        return _non_event.to_dataset(name="non_event")
    
    def _get_contingency(self):
        _hits, _miss, _false, _non_event = self.hits, self.miss, self.false, self.non_event
        _contingency_ds = xr.merge([_hits, _miss, _false, _non_event])
        
        return _contingency_ds
    
    def _get_table(self):

        _contigent_ds = self._get_contingency()
        _contingent_df = _contigent_ds.count(dim=["longitude", "latitude"]).to_dataframe()
        
        _contingent_df["BIAS"] = _contingent_df.apply(lambda x: (x["hits"] + x["false"]) / (x["hits"] + x["miss"]), axis=1)
        _contingent_df["POD"] = _contingent_df.apply(lambda x: x["hits"] / (x["hits"] + x["miss"]), axis=1)
        _contingent_df["FAR"] = _contingent_df.apply(lambda x: x["false"] / (x["hits"] + x["false"]), axis=1)
        _contingent_df["SR"] = _contingent_df.apply(lambda x: x["hits"] / (x["hits"] + x["false"]), axis=1)
        _contingent_df["CSI"] = _contingent_df.apply(lambda x: x["hits"] / (x["hits"] + x["false"] + x["miss"]), axis=1)
        _contingent_df["PCR"] = _contingent_df.apply(lambda x: x["non_event"] / (x["false"]+x["non_event"]), axis=1)

        _var_ls = ["BIAS", "POD", "FAR", "SR", "CSI", "PCR"]
        _contingent_df[_var_ls] = _contingent_df[_var_ls].round(3)

        return _contingent_df