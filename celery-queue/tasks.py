import os
import time
from celery import Celery
from celery.schedules import crontab
from celery.utils.log import get_task_logger
import redis

import argparse
from pytz import timezone
import math
import datetime
import time

import influxdb_client
from influxdb_client import InfluxDBClient, Point, WritePrecision, BucketsApi
from influxdb_client.client.write_api import SYNCHRONOUS

from Ashare.Ashare import *
from Ashare.MyTT import *


token = "myadmintoken"
org = "myorganization"
bucket = "stockdata"


logger = get_task_logger(__name__)


CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379'),
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379')

celery = Celery('tasks', broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)



# # Connect Redis db
# redis_db = redis.Redis(
#     host="localhost", port="6379", db=1, charset="utf-8", decode_responses=True
# )

# # Initialize timer in redis
# redis_db.mset({"minute": 0, "second": 0})



# Add periodic tasks
celery_beat_schedule = {
    "time_scheduler": {
        "task": "tasks.timer",
        # Run every second
        "schedule": crontab(minute='*/1'),
    }
}


celery.conf.update(
    result_backend=CELERY_RESULT_BACKEND,
    broker_url=CELERY_BROKER_URL,
    timezone="Asia/Shanghai",
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    beat_schedule=celery_beat_schedule,
)

def scrape_into_influxdb():
    """Define function to generate the sin wave."""

    client = InfluxDBClient(url="http://influxdb:8086", token=token, org=org)

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

        ts: datetime.datetime = index
        print("------")
        print(ts)
        print(ts.timestamp())

        # timestamp = ts.timestamp()
        # dt_object = datetime.datetime.fromtimestamp(timestamp, tz=timezone('Asia/Shanghai'))
        # print(dt_object.timestamp())
        # print(str(dt_object))

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
             .time(ts, write_precision=WritePrecision.S))

        write_api.write(bucket=bucket, org=org, record=p)

    query = 'from(bucket: "stockdata") |> range(start: -7d)'
    tables = client.query_api().query(query, org=org)
    for table in tables:
        for record in table.records:
            print(record)

    client.close()


@celery.task(name='tasks.timer')
def timer():
    # second_counter = int(redis_db.get("second")) + 1
    # if second_counter >= 59:
    #     # Reset the counter
    #     redis_db.set("second", 0)
    #     # Increment the minute
    #     redis_db.set("minute", int(redis_db.get("minute")) + 1)
    # else:
    #     # Increment the second
    #     redis_db.set("second", second_counter)

    scrape_into_influxdb()

    logger.critical("second")
    logger.critical("222222222222")


@celery.task(name='tasks.add')
def add(x: int, y: int) -> int:
    time.sleep(5)
    return x + y
