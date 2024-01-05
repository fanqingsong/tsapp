# -*- coding: utf-8 -*-
"""Tutorial using all elements to define a sine wave."""

import argparse

import math
import datetime
import time
from pytz import timezone
import influxdb_client
from influxdb_client import InfluxDBClient, Point, WritePrecision, BucketsApi
from influxdb_client.client.write_api import SYNCHRONOUS

from Ashare.Ashare import *
from Ashare.MyTT import *


token = "myadmintoken"
org = "myorganization"
bucket = "sine_wave"


def main(host='localhost', port=8086):
    """Define function to generate the sin wave."""

    client = InfluxDBClient(url="http://localhost:8086", token=token, org=org)

    version = client.ping()
    print(version)
    # print("Successfully connected to InfluxDB: " + version)

    write_api = client.write_api(write_options=SYNCHRONOUS)

    df = get_price('sh000001', frequency='1m', count=1000)
    print(df)
    # CLOSE = df.close.values
    # print(CLOSE)

    for index, row in df.iterrows():
        print(row)

        ts = index
        print("------")
        print(ts)
        print(ts.timestamp())

        timestamp = ts.timestamp()
        dt_object = datetime.datetime.fromtimestamp(timestamp)
        print(dt_object.timestamp())
        print(str(dt_object))
        
        open = row['open']
        high = row['high']
        low = row['low']
        close = row['close']
        volume = row['volume']

        p = (influxdb_client.Point("day_stock_data")
             .tag("stock_id", "sh000001")
             .field("open", open)
             .field("high", high)
             .field("low", low)
             .field("close", close)
             .field("volume", volume)
             .time(int(timestamp), write_precision=WritePrecision.S))

        write_api.write(bucket=bucket, org=org, record=p)

    query = 'from(bucket: "sine_wave") |> range(start: -7d)'
    tables = client.query_api().query(query, org=org)
    for table in tables:
        for record in table.records:
            print(record)

    client.close()



def parse_args():
    """Parse the args."""
    parser = argparse.ArgumentParser(
        description='example code to play with InfluxDB')
    parser.add_argument('--host', type=str, required=False,
                        default='localhost',
                        help='hostname influxdb http API')
    parser.add_argument('--port', type=int, required=False, default=8086,
                        help='port influxdb http API')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    main(host=args.host, port=args.port)