#!/usr/bin/env python3

import os
import sys
import logging
import tarfile
import requests
import numpy as np
import pandas as pd
from pathlib import Path
from argparse import ArgumentParser
from datetime import datetime
from datetime import timedelta

#logging.basicConfig(level=logging.DEBUG)

# --- Import Pegasus API -----------------------------------------------------------
from Pegasus.api import *

class CrocusWorkflow():
    wf = None
    sc = None
    tc = None
    rc = None
    props = None

    dagfile = None
    wf_dir = None
    shared_scratch_dir = None
    local_storage_dir = None
    wf_name = "crocus"

    # --- Init ---------------------------------------------------------------------
    def __init__(self, aqt_end_date, aqt_lag, wxt_end_date, wxt_lag, dagfile="workflow.yml"):
        self.dagfile = dagfile

        self.wf_dir = str(Path(__file__).parent.resolve())
        self.shared_scratch_dir = os.path.join(self.wf_dir, "scratch")
        self.local_storage_dir = os.path.join(self.wf_dir, "output")

        self.aqt_end_date = aqt_end_date
        self.aqt_lag = aqt_lag
        self.wxt_end_date = wxt_end_date
        self.wxt_lag = wxt_lag


    # --- Write files in directory -------------------------------------------------
    def write(self):
        self.sc.write()
        self.props.write()
        self.rc.write()
        self.tc.write()
        self.wf.write()


    # --- Configuration (Pegasus Properties) ---------------------------------------
    def create_pegasus_properties(self):
        self.props = Properties()
        return


    # --- Site Catalog -------------------------------------------------------------
    def create_sites_catalog(self, exec_site_name="condorpool"):
        self.sc = SiteCatalog()

        local = (Site("local")
                    .add_directories(
                        Directory(Directory.SHARED_SCRATCH, self.shared_scratch_dir)
                            .add_file_servers(FileServer("file://" + self.shared_scratch_dir, Operation.ALL)),
                        Directory(Directory.LOCAL_STORAGE, self.local_storage_dir)
                            .add_file_servers(FileServer("file://" + self.local_storage_dir, Operation.ALL))
                    )
                )

        exec_site = (Site(exec_site_name)
                        .add_condor_profile(universe="vanilla")
                        .add_pegasus_profile(
                            style="condor"
                        )
                    )


        self.sc.add_sites(local, exec_site)
        return 


    # --- Transformation Catalog (Executables and Containers) ----------------------
    def create_transformation_catalog(self, exec_site_name="condorpool"):
        self.tc = TransformationCatalog()

        crocus_container = Container("crocus_container",
            container_type = Container.SINGULARITY,
            image="docker://papajim/crocus:latest",
            image_site="docker_hub"
        )

        # Add the crocus processing
        aqt_ingest = Transformation("aqt_ingest", site=exec_site_name, pfn=os.path.join(self.wf_dir, "executables/aqt-ingest.py"), is_stageable=True, container=crocus_container)
        wxt_ingest = Transformation("wxt_ingest", site=exec_site_name, pfn=os.path.join(self.wf_dir, "executables/wxt-ingest.py"), is_stageable=True, container=crocus_container)


        self.tc.add_containers(crocus_container)
        self.tc.add_transformations(aqt_ingest, wxt_ingest)
        return


    # --- Replica Catalog ----------------------------------------------------------
    def create_replica_catalog(self):
        self.rc = ReplicaCatalog()
        return


    # --- Create Workflow ----------------------------------------------------------
    def create_workflow(self):
        self.wf = Workflow(self.wf_name, infer_dependencies=True)
        
        #create aqt jobs
        aqt_start_date = self.aqt_end_date - timedelta(days=self.aqt_lag)
        for i in range(self.aqt_lag):
            curr_aqt_date = aqt_start_date + timedelta(days=i)
            date_time_str = curr_aqt_date.strftime("%Y-%m-%d")
            output_file = curr_aqt_date.strftime('crocus-neiu-aqt-a1-%Y%m%d-%H%M%S.nc'), 
            aqt_ingest_job = (
                Job("aqt_ingest", _id=f"crocus-neiu-aqt-{date_time_str}", node_label=f"crocus-neiu-aqt-{date_time_str}")
                    .add_args("--date", curr_aqt_date.strftime("%Y-%m-%d"))
                    .add_outputs(curr_aqt_date.strftime('crocus-neiu-aqt-a1-%Y%m%d-%H%M%S.nc'), register_replica=True, stage_out=True)
            )
        
            self.wf.add_jobs(aqt_ingest_job)



        #create wxt jobs
        wxt_start_date = self.wxt_end_date - timedelta(days=self.wxt_lag)
        for i in range(self.wxt_lag):
            curr_wxt_date = wxt_start_date + timedelta(days=i)
            date_time_str = curr_wxt_date.strftime("%Y-%m-%d")
            output_file = curr_wxt_date.strftime('crocus-neiu-wxt-a1-%Y%m%d-%H%M%S.nc')
            wxt_ingest_job = (Job("wxt_ingest", _id=f"crocus-neiu-wxt-{date_time_str}", node_label=f"crocus-neiu-wxt-{date_time_str}")
                    .add_args("--date", date_time_str)
                    .add_outputs(output_file, register_replica=True, stage_out=True)
            )
        
            self.wf.add_jobs(wxt_ingest_job)

    def submit(self):
        workflow.write()
        try:
            self.wf.plan(
                output_dir="./outputs",
                dir="./submit",
                submit=True
            )
        #.wait().analyze()
        except Exception as e:
            print(e)
            exit(-1)



if __name__ == '__main__':
    parser = ArgumentParser(description="Pegasus CROCUS Workflow")

    parser.add_argument("-o", "--output", metavar="STR", type=str, default="workflow.yml", help="Output file (default: workflow.yml)")
    parser.add_argument("--aqt-end-date", metavar="STR", type=lambda s: datetime.strptime(s, '%Y-%m-%d'), required=True, help="AQT end date (example: '2024-01-01')")
    parser.add_argument("--aqt-lag", metavar="INT", type=int, default=1, required=False, help="AQT days lag (default: 1)")
    parser.add_argument("--wxt-end-date", metavar="STR", type=lambda s: datetime.strptime(s, '%Y-%m-%d'), required=True, help="WXT end date (example: '2024-01-01')")
    parser.add_argument("--wxt-lag", metavar="INT", type=int, default=1, required=False, help="WXT days lag (default: 1)")

    args = parser.parse_args()

    workflow = CrocusWorkflow(
                    aqt_end_date = args.aqt_end_date,
                    aqt_lag = args.aqt_lag,
                    wxt_end_date = args.wxt_end_date,
                    wxt_lag = args.wxt_lag,
                    dagfile = args.output)

    print("Creating execution sites...")
    workflow.create_sites_catalog()

    print("Creating workflow properties...")
    workflow.create_pegasus_properties()

    print("Creating transformation catalog...")
    workflow.create_transformation_catalog()

    print("Creating replica catalog...")
    workflow.create_replica_catalog()

    print("Creating crocus workflow dag...")
    workflow.create_workflow()

    workflow.submit()
