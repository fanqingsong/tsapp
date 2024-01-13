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

import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr

my_sender = os.environ.get('EMAIL_SENDER_ADDR')
my_pass = os.environ.get('EMAIL_PASSWORD')
my_user = os.environ.get('EMAIL_RECEIVER_ADDR')
smtp_server = os.environ.get('EMAIL_SMTP_SERVER')
smtp_port = os.environ.get('EMAIL_SMTP_PORT')



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
        # "schedule": crontab(minute='*/1', day_of_week='mon-fri'),
        "schedule": crontab(minute=0, hour='*/2', day_of_week='mon-fri'),
        # "schedule": crontab(minute=0, hour='*/3,8-17'),
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

def mail(head :str = 'test', content :str = 'this is just a test'):
    ret = True
    try:
        msg = MIMEText(content, 'html', 'utf-8')
        msg['From'] = formataddr(["tracy", my_sender])
        msg['To'] = formataddr(["test", my_user])
        msg['Subject'] = head

        server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        server.login(my_sender, my_pass)
        server.sendmail(my_sender, [my_user, ], msg.as_string())
        server.quit()
    except Exception:
        ret = False
    return ret

def scrape_into_influxdb():
    """Define function to generate the sin wave."""

    client = InfluxDBClient(url="http://influxdb:8086", token=token, org=org)

    version = client.ping()
    print(version)
    # print("Successfully connected to InfluxDB: " + version)

    write_api = client.write_api(write_options=SYNCHRONOUS)

    df = get_price('sh000001', frequency='1d', count=2000)
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
             .tag("frequency", "daily")
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

    ret = mail("scrape over", "hooray")
    if ret:
        print("email sent succeeded")
    else:
        print("email set failed")

def watch_recent_trend():

    client = InfluxDBClient(url="http://influxdb:8086", token=token, org=org)

    version = client.ping()
    print(version)

    query = '''
        from(bucket: "stockdata") 
            |> range(start: -7d)
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            |> yield()
        '''
    df = client.query_api().query_data_frame(query, org=org)

    print("---- df -------")
    print(df.columns)
    print(df)

    df['close_prev_one'] = df['close'].shift(1)
    df['volume_prev_one'] = df['volume'].shift(1)

    df['close_change'] = df['close'] - df['close_prev_one']
    df['volume_change'] = df['volume'] - df['volume_prev_one']


    ret = mail("Change for Latest 7 Days.", df.to_html())
    if ret:
        print("email sent succeeded")
    else:
        print("email set failed")



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

    watch_recent_trend()


@celery.task(name='tasks.add')
def add(x: int, y: int) -> int:
    time.sleep(5)
    return x + y

@celery.task(name='tasks.trigger_scrape')
def trigger_scrape() -> None:
    scrape_into_influxdb()

    watch_recent_trend()


