#!/usr/bin/env python3

import os
import sage_data_client
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import datetime
import xarray as xr
from datetime import datetime, timedelta
from PIL import Image
from time import time
from argparse import ArgumentParser
from matplotlib.dates import DateFormatter
from metpy.units import units
from metpy.calc import dewpoint_from_relative_humidity, wet_bulb_temperature

wxt_global_NEIU = {'conventions': "CF 1.10",
                   'site_ID' : "NEIU",
                  'CAMS_tag' : "CMS-WXT-002",
                  'datastream' : "CMS_wxt536_NEIU_a1",
                  'datalevel' : "a1",
                  'latitude' : 41.9804526,
                  'longitude' : -87.7196038}

var_attrs_wxt = {'temperature': {'standard_name' : 'air_temperature',
                       'units' : 'celsius'},
                'humidity': {'standard_name' : 'relative_humidity',
                       'units' : 'percent'},
                'dewpoint': {'standard_name' : 'dew_point_temperature',
                       'units' : 'celsius'},
                'pressure': {'standard_name' : 'air_pressure',
                       'units' : 'hPa'},
                'wetbulb': {'standard_name' : 'wet_bulb_temperature',
                       'units' : 'celsius'},
                'wetbulb': {'standard_name' : 'wet_bulb_temperature',
                       'units' : 'celsius'},
                'wind_dir_10s': {'standard_name' : 'wet_bulb_temperature',
                       'units' : 'celsius'}}

def ingest_wxt(st):
    hours = 24
    start = st.strftime('%Y-%m-%dT%H:%M:%SZ')
    end = (st + timedelta(hours=hours)).strftime('%Y-%m-%dT%H:%M:%SZ')
    print(f"Data start date {start}")
    print(f"Data end date {end}")
    df_temp = sage_data_client.query(start=start,
                                     end=end, 
                                        filter={
                                            "name" : 'wxt.env.temp|wxt.env.humidity|wxt.env.pressure|wxt.rain.accumulation',
                                            "plugin" : "registry.sagecontinuum.org/jrobrien/waggle-wxt536:0.23.5.*",
                                            "vsn" : "W08D",
                                            "sensor" : "vaisala-wxt536"
                                        }
    )
    winds = sage_data_client.query(start=start,
                                     end=end, 
                                        filter={
                                            "name" : 'wxt.wind.speed|wxt.wind.direction',
                                            "plugin" : "registry.sagecontinuum.org/jrobrien/waggle-wxt536:0.23.5.*",
                                            "vsn" : "W08D",
                                            "sensor" : "vaisala-wxt536"
                                        }
    )
    
    hums = df_temp[df_temp['name']=='wxt.env.humidity']
    temps = df_temp[df_temp['name']=='wxt.env.temp']
    pres = df_temp[df_temp['name']=='wxt.env.pressure']
    rain = df_temp[df_temp['name']=='wxt.rain.accumulation']


    npres = len(pres)
    nhum = len(hums)
    ntemps = len(temps)
    nrains = len(rain)
    print(npres, nhum, ntemps, nrains)
    minsamps = min([nhum, ntemps, npres, nrains])

    temps['time'] = pd.DatetimeIndex(temps['timestamp'].values)

    vals = temps.set_index('time')[0:minsamps]
    vals['temperature'] = vals.value.to_numpy()[0:minsamps]
    vals['humidity'] = hums.value.to_numpy()[0:minsamps]
    vals['pressure'] = pres.value.to_numpy()[0:minsamps]
    vals['rainfall'] = rain.value.to_numpy()[0:minsamps]

    direction = winds[winds['name']=='wxt.wind.direction']
    speed = winds[winds['name']=='wxt.wind.speed']

    nspeed = len(speed)
    ndir = len(direction)
    print(nspeed, ndir)
    minsamps = min([nspeed, ndir])

    speed['time'] = pd.DatetimeIndex(speed['timestamp'].values)
    windy = speed.set_index('time')[0:minsamps]
    windy['speed'] = windy.value.to_numpy()[0:minsamps]
    windy['direction'] = direction.value.to_numpy()[0:minsamps]


    winds10mean = windy.resample('10s').mean(numeric_only=True).ffill()
    winds10max = windy.resample('10s').max(numeric_only=True).ffill()
    dp = dewpoint_from_relative_humidity(vals.temperature.to_numpy() * units.degC, 
                                         vals.humidity.to_numpy() * units.percent)

    vals['dewpoint'] = dp
    vals10 = vals.resample('10s').mean(numeric_only=True).ffill() #ffil gets rid of nans due to empty resample periods
    wb = wet_bulb_temperature(vals10.pressure.to_numpy() * units.hPa,
                              vals10.temperature.to_numpy() * units.degC,
                              vals10.dewpoint.to_numpy() * units.degC)

    vals10['wetbulb'] = wb
    vals10['wind_dir_10s'] = winds10mean['direction']
    vals10['wind_mean_10s'] = winds10mean['speed']
    vals10['wind_max_10s'] = winds10max['speed']
    _ = vals10.pop('value')

    fname = st.strftime('crocus-neiu-wxt-a1-%Y%m%d-%H%M%S.nc')
    
    try:
        os.remove(fname)
    except OSError:
        pass
    
    vals10xr = xr.Dataset.from_dataframe(vals10)
    vals10xr = vals10xr.sortby('time')
    
    vals10xr.to_netcdf(fname)

def main():
    parser = ArgumentParser(description="WXT Ingest")
    parser.add_argument("--date", metavar="STR", type=lambda s: datetime.strptime(s, '%Y-%m-%d'), required=True, help="Date to pull data for (example: '2021-08-10')")

    args = parser.parse_args()
    
    try:
        start_time = time()
        ingest_wxt(args.date)
        print("Success...")
        end_time = time()
        print(f"Time taken: {end_time - start_time}")
    except Exception as e:
        print(e)

if __name__ == "__main__":
    main()

