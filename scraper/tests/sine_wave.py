# -*- coding: utf-8 -*-
"""Tutorial using all elements to define a sine wave."""

import argparse

import math
import datetime
import time

import influxdb_client
from influxdb_client import InfluxDBClient, Point, WritePrecision, BucketsApi
from influxdb_client.client.write_api import SYNCHRONOUS

token = "myadmintoken"
org = "myorganization"
bucket = "sine_wave"


def main(host='localhost', port=8086):
    """Define function to generate the sin wave."""

    client = InfluxDBClient(url="http://localhost:8086", token=token, org=org)

    version = client.ping()
    print(version)
    # print("Successfully connected to InfluxDB: " + version)

    # bucketapi = BucketsApi(client)
    #
    # bucketapi.create_bucket('sine_wave')

    write_api = client.write_api(write_options=SYNCHRONOUS)

    now = datetime.datetime.today()
    for angle in range(0, 360):
        y = 10 + math.sin(math.radians(angle)) * 10

        # point = {
        #     "measurement": 'foobar',
        #     "time": int(now.strftime('%s')) + angle,
        #     "fields": {
        #         "value": y
        #     }
        # }

        time.sleep(1)

        p = influxdb_client.Point("foobar").tag("location", "Prague").field("value", y)
        write_api.write(bucket=bucket, org=org, record=p)
    #
    # query = 'SELECT * FROM foobar'
    # print("Querying data: " + query)
    # result = client.query(query, database=DBNAME)
    # print("Result: {0}".format(result))

    """
    You might want to comment the delete and plot the result on InfluxDB
    Interface. Connect on InfluxDB Interface at http://127.0.0.1:8083/
    Select the database tutorial -> Explore Data

    Then run the following query:

        SELECT * from foobar
    """
    #
    # print("Delete database: " + DBNAME)
    # client.drop_database(DBNAME)


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