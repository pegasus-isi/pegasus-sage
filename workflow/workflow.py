#!/usr/bin/env python3
import os
import sys
from pathlib import Path
import datetime

# --- Import Pegasus API -----------------------------------------------------------
from Pegasus.api import *

class SageWorkflow():
    wf = None

    # --- Init ---------------------------------------------------------------------
    def __init__(self):
        self.wf_name = "SageWorkflow" 
    
        ts = datetime.datetime.now()
        self.wf = Workflow(self.wf_name, infer_dependencies=True)
        
        # Add a preprocess job
        a = File("example.jpg")
        b = File("color.out")
        edge_image_job = Job("edge_image.py")\
                            .add_inputs(a)\
                            .set_stdout(b, stage_out=True, register_replica=False)

        self.wf.add_jobs(edge_image_job)

    def submit(self):
        try:
            properties = {"env.PEGASUS_HOME": "/usr"}
            self.wf.plan(
                input_dirs=["./inputs"], 
                output_dir="./outputs", 
                transformations_dir="./executables",
                submit=True,
                **properties
            ).wait().analyze()
        except Exception as e:
            print(e)
            exit(-1)


if __name__ == '__main__':
    workflow = SageWorkflow()
    workflow.submit()
