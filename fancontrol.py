#!/usr/bin/env python3

import time
import os

from gpiozero import OutputDevice

ON_THRESHOLD = 55  # (degrees Celsius) Fan kicks on at this temperature.
OFF_THRESHOLD = 50  # (degress Celsius) Fan shuts off at this temperature.
SLEEP_INTERVAL = 30  # (seconds) How often we check the core temperature.
GPIO_PIN = 1  # Which GPIO pin you're using to control the fan. refer to BCM Mode
HOST_NAME = os.uname()[1] # get hostname

# influxdb lib section
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
token = "[YOUR DB TOKEN HERE]"
org = "[YOUR ORGANIZATION NAME HERE]"
bucket = "YOUR DB NAME HERE"
client = InfluxDBClient(url="[YOUR HOST:PORT HERE]", token=token)
write_api = client.write_api(write_options=SYNCHRONOUS)


def get_temp():
    """Get the core temperature.

    Read file from /sys to get CPU temp in temp in C *1000

    Returns:
        int: The core temperature in thousanths of degrees Celsius.
    """
    with open('/sys/class/thermal/thermal_zone0/temp') as f:
        temp_str = f.read()
        #print("{}{}".format("CPU Temp : ",temp_str))

    try:
        return int(temp_str) / 1000
    except (IndexError, ValueError,) as e:
        raise RuntimeError('Could not parse temperature output.') from e

def write_db(temp):
    data = "control,id=" + HOST_NAME + " temp="+str(temp)
    write_api.write(bucket, org, data) # write temp
    #print("Write data to DB")

if __name__ == '__main__':
    # Validate the on and off thresholds
    if OFF_THRESHOLD >= ON_THRESHOLD:
        raise RuntimeError('OFF_THRESHOLD must be less than ON_THRESHOLD')

    fan = OutputDevice(GPIO_PIN)

    while True:
        temp = get_temp()
        write_db(temp)

        # Start the fan if the temperature has reached the limit and the fan
        # isn't already running.
        # NOTE: `fan.value` returns 1 for "on" and 0 for "off"
        if temp > ON_THRESHOLD and not fan.value:
            fan.on()

        # Stop the fan if the fan is running and the temperature has dropped
        # to 10 degrees below the limit.
        elif fan.value and temp < OFF_THRESHOLD:
            fan.off()

        time.sleep(SLEEP_INTERVAL)
