# Pegasus Sage Collaboration
This repository contains workflows and approaches that leverage the Pegasus WMS in Sage's workflows.

## Beehive Cloud Workflow
This is an example workflow that pulls data from Sage's beehive datastore and saves them into files.

## Beehive Fabric Processing
This example contains a recipe to spawn computational resources on FABRIC. It then loads up the Beehive Cloud Workflow
and executes it on the spawned FABRIC resources.

## Crocus Processing
This workflow is inspired by CROCUS urban project and their ingest pipelines (https://github.com/CROCUS-Urban/ingests/).</br>
The workflow receives target dates as input followed by lag days. Then it creates a job for each day for data ingestion
and saves the ingested data into files.

## Workflow In A Box
This is a special use case for Sage. This directory contains a recipe for building an example Sage app with 
Pegasus and HTCONDOR ready to be deployed on Sage's Waggle nodes (IoT nodes). The workflow runs entirely on 
a single Waggle node and pushes data to the Beehive datastore.
