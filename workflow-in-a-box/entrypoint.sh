#!/usr/bin/env bash

/usr/sbin/condor_master
su - pegasus -c "bash /opt/pegasus-wrapper"
