#!/usr/bin/python
'''*****************************************************************************************************************
    Pi Temperature Station
    By John M. Wargo
    www.johnwargo.com

********************************************************************************************************************'''

from __future__ import print_function

import datetime
import sys
import time

import Adafruit_DHT
import ConfigParser
import explorerhat

# import urllib2
# from urllib import urlencode


# ============================================================================
# Numeric constants
# ============================================================================
# specifies how often to measure values from the Sense HAT (in minutes)
measurement_interval = 1  # minutes

# ============================================================================
# String constants
# ============================================================================
single_hash = "#"
hashes = "########################################"
slash_n = "\n"
# the weather underground URL used to upload weather data
weather_underground_url = "http://weatherstation.wunderground.com/weatherstation/updateweatherstation.php"


def config_section_map(section):
    dict1 = {}
    options = Config.options(section)
    for option in options:
        try:
            dict1[option] = Config.get(section, option)
            if dict1[option] == -1:
                print("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1


def main():
    # assign the sensor type
    sensor = Adafruit_DHT.DHT22
    # it's connected to pin 23
    pin = 23
    # initialize the lastMinute variable to the current time to start
    last_minute = datetime.datetime.now().minute
    # on startup, just use the previous minute as lastMinute
    if last_minute == 0:
        last_minute = 59
    else:
        last_minute -= 1
    # infinite loop to continuously check weather values
    while 1:
        # get the current minute
        current_minute = datetime.datetime.now().minute
        # is it the same minute as the last time we checked?
        if current_minute != last_minute:
            # print("Checking minute:", current_minute)
            # reset last_minute to the current_minute
            last_minute = current_minute
            # is minute zero, or divisible by 10?
            # we're only going to take measurements every measurement_interval minutes
            if (current_minute == 0) or ((current_minute % measurement_interval) == 0):
                # get the reading timestamp
                now = datetime.datetime.now()
                # print("\nOn a", measurement_interval, "minute mark:", current_minute)
                print("\n%d minute mark (%d @ %s)" % (measurement_interval, current_minute, str(now)))
                # read the temperature
                print("Turning the light on")
                explorerhat.light.green.on()
                print("Taking the measurement")
                humidity, temp_c = Adafruit_DHT.read_retry(sensor, pin)
                print("Turning the light off")
                explorerhat.light.green.off()
                if humidity is not None and temp_c is not None:
                    # calculate temp in F and round to one decimal place
                    temp_f = round((temp_c * 1.8) + 32, 1)
                    # round the temp to one decimal place
                    temp_c = round(temp_c, 1)
                    # write the data to the console
                    print('Temp: {0:0.1f}*F/{0:0.1f}*C  Humidity: {1:0.1f}%'.format(temp_f, temp_c, humidity))

                    # ========================================================
                    # Upload the weather data to Weather Underground
                    # ========================================================
                    # From http://wiki.wunderground.com/index.php/PWS_-_Upload_Protocol
                    # print("\nUploading data to Weather Underground")
                    # build a weather data object
                    # weather_data = {
                    #     "action": "updateraw",
                    #     "ID": wu_station_id,
                    #     "PASSWORD": wu_station_key,
                    #     "dateutc": "now",
                    #     "tempf": str(temp_f),
                    #     "humidity": str(humidity)
                    # }
                    # try:
                    #     upload_url = weather_underground_url + "?" + urlencode(weather_data)
                    #     response = urllib2.urlopen(upload_url)
                    #     html = response.read()
                    #     print(html)
                    #     # do something
                    #     response.close()  # best practice to close the file
                    # except:
                    #     print("Exception:", sys.exc_info()[0], slash_n)
                else:
                    print('Failed to get reading.')

        # wait a second then check again
        # You can always increase the sleep value below to check less often
        time.sleep(1)  # this should never happen since the above is an infinite loop

    print("Leaving main()")

# ============================================================================
# here's where we start doing stuff
# ============================================================================
print(slash_n + hashes)
print(single_hash, "Pi Temperature Station              ", single_hash)
print(single_hash, "By John M. Wargo (www.johnwargo.com)", single_hash)
print(hashes)

# make sure we don't have a measurement_interval > 60
if (measurement_interval is None) or (measurement_interval > 60):
    print("The application's 'measurement_interval' cannot be empty or greater than 60")
    sys.exit(1)

# calculate how many times we're checking temp in an hour.
# used to manage last_values array length
num_past_temp_values = int(60 / measurement_interval)

# setup the config parser
Config = ConfigParser.ConfigParser()
print("\nOpening configuration file")
try:
    Config.read("./config.ini")
except:
    print("Exception:", sys.exc_info()[0], slash_n)
    sys.exit(1)

# ============================================================================
#  Read Weather Underground Configuration Parameters
# ============================================================================
print("\nInitializing Weather Underground configuration")
wu_station_id = config_section_map("WeatherUnderground")["station_id"]
wu_station_key = config_section_map("WeatherUnderground")["station_key"]
if (wu_station_id is None) or (wu_station_key is None):
    print("Missing values from the Weather Underground configuration file\n")
    sys.exit(1)
# we made it this far, so it must have worked...
print("URL:", weather_underground_url)
print("Station ID:", wu_station_id)
print("Station key:", wu_station_key)
print("Successfully read Weather Underground configuration values")
print("\nInitialization complete!\n")

# Now see what we're supposed to do next
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting application\n")
        sys.exit(0)
