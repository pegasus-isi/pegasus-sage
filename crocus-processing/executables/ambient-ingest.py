#!/usr/bin/env python3

from ambient_api.ambientapi import AmbientAPI
import numpy as np
from datetime import datetime, timedelta
import time
import pandas as pd
import xarray as xr
import os
from pathlib import Path

print(os.getenv('AMBIENT_ENDPOINT'))

# Access the Ambient weather API and get the devices available
api = AmbientAPI()
devices = api.get_devices()

attrs_dict = {'tempf':{'standard_name': 'Temperature',
                       'units': 'degF'},
              'dewPoint': {'standard_name': 'Dewpoint Temperature',
                           'units': 'degF'}}

variable_mapping = {'tempf':'outdoor_temperature',
                    'dewPoint':'outdoor_dewpoint',
                    'date':'time'}

station_remapping = {'CMS-AMB-001':'atmos-g1',
                     'CMS-AMB-004':'atmos-g2'}

def process_station(device, attrs=attrs_dict, variable_mapping=variable_mapping):
    
    current_date = datetime.utcnow() - timedelta(days=1)
    # Read in the station data
    data = device.get_data(end_date = current_date)
    
    meta = device.info
    
    # Read into a pandas dataframe
    df = pd.DataFrame(data)
    print(df)
    
    # Format the times properly
    df['date'] = pd.DatetimeIndex(pd.to_datetime(df.date)).tz_convert('UTC').tz_localize(None).astype('datetime64[ns]')

    # Sort the values and set the index to be the date
    df = df.sort_values('date')
    df = df.set_index('date')

    ds = df.to_xarray()

    # Add associated metadata
    for variable in attrs.keys():
        ds[variable].attrs = attrs[variable]
    
    # Rename the variables
    ds = ds.rename(variable_mapping)
        
    # Reshape the data
    ds = ds.expand_dims('station')
    ds['station'] = [station_remapping[meta['name']]]
    ds['latitude'] = meta['coords']['coords']['lat']
    ds['longitude'] = meta['coords']['coords']['lon']
    
    ds = ds.sel(time=f"{current_date.year}-{current_date.month}-{current_date.day}")
    print(ds) 
    return ds

# Loop through for each device and retrieve the data, waiting for the API to clean up first
dsets = []
for device in devices:
    try:
        print(device)
        ds = process_station(device)
        site = f'{ds.station.values[0]}'
        time_label = pd.to_datetime(ds.time.values[0]).strftime(f'{site}.a1.%Y%m%d.000000.nc')
        #time_label = pd.to_datetime(ds.time.values[0]).strftime(f'{site}/{site}.a1.%Y%m%d.000000.nc')
        #full_path = Path(f'/home/mgrover/data/ambients/{time_label}')
        #if not os.path.exists(full_path.parent):
        #    os.makedirs(full_path.parent)
        print(time_label)
        ds.to_netcdf(time_label, mode='w')
    except Exception as e:
        print(e)
        pass
    #time.sleep(20)
