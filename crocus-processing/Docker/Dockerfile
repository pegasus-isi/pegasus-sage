FROM ubuntu:22.04

RUN apt-get update \
    && apt-get -y upgrade \
    && apt-get install -y python3-dev python3-pip\
    && rm -rf /var/cache/apt/archives /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir \
    numpy \
    pandas \
    xarray \
    sage-data-client \
    ambient_api \
    matplotlib \
    MetPy \
    pillow \
    netCDF4


