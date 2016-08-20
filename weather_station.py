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

from sense_hat import SenseHat

from config import Config

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


def main():
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
                print("\n%d minute mark (%d @ %s)" % (measurement_interval, current_minute, str(now)))

                # ========================================================
                # read the temperature from the Sense HAT
                # ========================================================
                humidity = round(sense.get_humidity(), 2)
                # convert pressure from millibars to inHg before posting
                pressure = round(sense.get_pressure() * 0.0295300, 2)
                temp_c = round(sense.get_temperature(), 1)
                temp_f = c_to_f(temp_c)
                print("Temp: %sF (%sC), Pressure: %s inHg, Humidity: %s%%" % (temp_f, temp_c, pressure, humidity))

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

# ============================================================================
#  Read Weather Underground Configuration Parameters
# ============================================================================
print("\nInitializing Weather Underground configuration")
wu_station_id = Config.STATION_ID
wu_station_key = Config.STATION_KEY
if (wu_station_id is None) or (wu_station_key is None):
    print("Missing values from the Weather Underground configuration file\n")
    sys.exit(1)
# we made it this far, so it must have worked...
print("URL:", weather_underground_url)
print("Station ID:", wu_station_id)
print("Station key:", wu_station_key)
print("Successfully read Weather Underground configuration values")

# ============================================================================
# initialize the Sense HAT object
# ============================================================================
try:
    print("\nInitializing the Sense HAT client")
    sense = SenseHat()
    # sense.set_rotation(180)
    # then write some text to the Sense HAT's 'screen'
    sense.show_message("Init", text_colour=[255, 255, 0], back_colour=[0, 0, 255])
    # clear the screen
    sense.clear()
    # get the current temp to use when checking the previous measurement
    last_temp = c_to_f(sense.get_temperature())
    print("Current temperature:", last_temp)
except:
    print("Unable to initialize the Sense HAT library:", sys.exc_info()[0])
    sys.exit(1)

print("\nInitialization complete!\n")

# Now see what we're supposed to do next
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting application\n")
        sys.exit(0)
