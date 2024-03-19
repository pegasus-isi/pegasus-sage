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


aqt_global_NEIU = {'conventions': "CF 1.10",
                   'site_ID' : "NEIU",
                  'CAMS_tag' : "CMS-AQT-001",
                  'datastream' : "CMS_aqt580_NEIU_a1",
                  'datalevel' : "a1",
                  'latitude' : 41.9804526,
                  'longitude' : -87.7196038}

var_attrs_aqt = {'pm2.5' : {'standard_name' : 'mole_concentration_of_pm2p5_ambient_aerosol_particles_in_air',
                       'units' : 'ug/m^3'},
            'pm10.0' : {'standard_name' : 'mole_concentration_of_pm10p0_ambient_aerosol_particles_in_air',
                       'units' : 'ug/m^3'},
            'pm1.0' : {'standard_name' : 'mole_concentration_of_pm1p0_ambient_aerosol_particles_in_air',
                       'units' : 'ug/m^3'},
                'no' : {'standard_name' : 'mole_fraction_of_nitrogen_monoxide_in_air',
                       'units' : 'Parts Per Million'},
                'o3' : {'standard_name' : 'mole_fraction_of_ozone_in_air',
                       'units' : 'Parts Per Million'},
                'co' : {'standard_name' : 'mole_fraction_of_carbon_monoxide_in_air',
                       'units' : 'Parts Per Million'},
                'no2' : {'standard_name' : 'mole_fraction_of_nitrogen_dioxide_in_air',
                       'units' : 'Parts Per Million'},
                'temperature': {'standard_name' : 'air_temperature',
                       'units' : 'celsius'},
                'humidity': {'standard_name' : 'relative_humidity',
                       'units' : 'percent'},
                'dewpoint': {'standard_name' : 'dew_point_temperature',
                       'units' : 'celsius'},
                'pressure': {'standard_name' : 'air_pressure',
                       'units' : 'hPa'}}


def ingest_aqt(st, global_attrs, var_attrs):
    hours = 24
    start = st.strftime('%Y-%m-%dT%H:%M:%SZ')
    end = (st + timedelta(hours=hours)).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    print(f"Data start date {start}")
    print(f"Data end date {end}")

    df_aq = sage_data_client.query(
        start=start,
        end=end, 
        filter={
            "plugin": "registry.sagecontinuum.org/jrobrien/waggle-aqt:0.23.5.04.*",
            "vsn": "W08D"
        }
    )

    pm25 = df_aq[df_aq['name']=='aqt.particle.pm2.5']
    pm10 = df_aq[df_aq['name']=='aqt.particle.pm1']
    pm100 = df_aq[df_aq['name']=='aqt.particle.pm10']

    no = df_aq[df_aq['name']=='aqt.gas.no']
    o3 = df_aq[df_aq['name']=='aqt.gas.ozone']
    no2 = df_aq[df_aq['name']=='aqt.gas.no2']
    co = df_aq[df_aq['name']=='aqt.gas.co']
    aqtemp = df_aq[df_aq['name']=='aqt.env.temp']
    aqhum = df_aq[df_aq['name']=='aqt.env.humidity']
    aqpres = df_aq[df_aq['name']=='aqt.env.pressure']


    pm25['time'] = pd.DatetimeIndex(pm25['timestamp'])

    aqvals = pm25.set_index('time')
    aqvals['pm2.5'] = aqvals.value.to_numpy().astype(float)
    aqvals['pm1.0'] = pm10.value.to_numpy().astype(float)
    aqvals['pm10.0'] = pm100.value.to_numpy().astype(float)

    aqvals['no'] = no.value.to_numpy().astype(float)
    aqvals['o3'] = o3.value.to_numpy().astype(float)
    aqvals['no2'] = no2.value.to_numpy().astype(float)
    aqvals['co'] = co.value.to_numpy().astype(float)
    aqvals['temperature'] =  aqtemp.value.to_numpy().astype(float)
    aqvals['humidity'] =  aqhum.value.to_numpy().astype(float)
    aqvals['pressure'] =  aqpres.value.to_numpy().astype(float)
    

    dp = dewpoint_from_relative_humidity( aqvals.temperature.to_numpy() * units.degC, 
                                         aqvals.humidity.to_numpy() * units.percent)

    aqvals['dewpoint'] = dp

    _ = aqvals.pop('value')
    _ = aqvals.pop('timestamp')
    
    
    fname = st.strftime('crocus-neiu-aqt-a1-%Y%m%d-%H%M%S.nc')
    valsxr = xr.Dataset.from_dataframe(aqvals)
    valsxr = valsxr.sortby('time')
    
    
    valsxr = valsxr.assign_attrs(global_attrs)
    
    for varname in var_attrs.keys():
        valsxr[varname] = valsxr[varname].assign_attrs(var_attrs[varname])
    
    try:
        os.remove(fname)
    except OSError:
        pass
    
    # Ensure time is saved properly
    valsxr["time"] = pd.to_datetime(valsxr.time)

    if valsxr['pm2.5'].shape[0] > 0:
        valsxr.to_netcdf(fname, format='NETCDF4')
    else:
        print('not saving... no data')
    
    #return valsxr


def main():
    parser = ArgumentParser(description="AQT Ingest")
    parser.add_argument("--date", metavar="STR", type=lambda s: datetime.strptime(s, '%Y-%m-%d'), required=True, help="Date to pull data for (example: '2021-08-10')")

    args = parser.parse_args()
    
    try:
        start_time = time()
        ingest_aqt(args.date, aqt_global_NEIU, var_attrs_aqt)
        print("Success...")
        end_time = time()
        print(f"Time taken: {end_time - start_time}")
    except Exception as e:
        print(e)

if __name__ == "__main__":
    main()
