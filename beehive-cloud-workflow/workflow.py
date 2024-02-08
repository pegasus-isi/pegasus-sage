#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from dateutil import tz

# --- Import Pegasus API -----------------------------------------------------------
from Pegasus.api import *

class SageWorkflow():
    wf = None

    # --- Init ---------------------------------------------------------------------
    def __init__(self):
        self.wf_name = "SageCloudWorkflow" 
    
        self.wf = Workflow(self.wf_name, infer_dependencies=True)
        
        tc = TransformationCatalog()

        temperature = Transformation(
                "temperature_stats.py",
                site="local",
                pfn= "/home/ubuntu/beehive-cloud-processing/executables/temperature_stats.py",
                is_stageable=True,
                arch=Arch.X86_64,
                os_type=OS.LINUX
            )
        
        tc.add_transformations(temperature)
        self.wf.add_transformation_catalog(tc)


        start_date = datetime.now(tz=tz.tzutc()) - timedelta(hours=24)
        for i in range(48):
            end_date = start_date + timedelta(minutes=29, seconds=59)

            # Add a preprocess job
            temperature_job = Job("temperature_stats.py")\
                                .add_args(
                                    "--start", 
                                    f"'{start_date.strftime('%Y-%m-%dT%H:%M:%S %z')}'",
                                    "--end", 
                                    f"'{end_date.strftime('%Y-%m-%dT%H:%M:%S %z')}'",
                                    "--output", 
                                    f"{start_date.strftime('%Y-%m-%dT%H-%M-%S')}_{end_date.strftime('%Y-%m-%dT%H-%M-%S')}_temperature.csv"
                                )\
                                .add_outputs(f"{start_date.strftime('%Y-%m-%dT%H-%M-%S')}_{end_date.strftime('%Y-%m-%dT%H-%M-%S')}_temperature.csv", stage_out=True, register_replica=False)

            self.wf.add_jobs(temperature_job)

            start_date += timedelta(minutes=30)

    def submit(self):
        try:
            self.wf.plan(
                output_dir="./outputs",
                input_dirs=["./inputs"],
                transformations_dir="./executables",
                submit=True
            ).wait()
        except Exception as e:
            print(e)
            exit(-1)


if __name__ == '__main__':
    workflow = SageWorkflow()
    workflow.submit()
