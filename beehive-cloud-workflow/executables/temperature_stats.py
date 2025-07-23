#!/usr/bin/env python3

"""
This example demonstrates querying all temperature data and exporting basic stats grouped by VSN and sensor in a csv file
"""
import sage_data_client
from argparse import ArgumentParser

def query_sage(start_date, end_date):
    # query and load data into pandas data frame
    df = sage_data_client.query(
        start=start_date,
        end=end_date,
        filter={
            "name": "env.temperature",
        }
    )

    if df.empty:
        return df

    # return stats of the temperature data grouped by node + sensor.
    return df.groupby(["meta.vsn", "meta.sensor"]).value.agg(["size", "min", "max", "mean"])


def main():
    parser = ArgumentParser(description="Get Temperature Data From SAGE")
    parser.add_argument("--start", metavar="INT", type=str, default="", help="Query Start Time", required=True)
    parser.add_argument("--end", metavar="INT", type=str, default="", help="Query End Time", required=True)
    parser.add_argument("--output", metavar="STR", type=str, default="temperature.csv", help="Output file", required=False)

    args = parser.parse_args()

    df = query_sage(args.start, args.end)

    df.to_csv(args.output)


if __name__ == "__main__":
    main()

