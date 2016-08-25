#!/usr/bin/python
'''*****************************************************************************************************************
    Pi Temperature Station
    By John M. Wargo
    www.johnwargo.com

    This is a Raspberry Pi project that measures weather values (temperature, humidity and pressure) using
    the Astro Pi Sense HAT then uploads the data to a Weather Underground weather station.
********************************************************************************************************************'''

from __future__ import print_function

import datetime
import sys
import time
from urllib import urlencode

import urllib2
from sense_hat import SenseHat

from config import Config

# ============================================================================
# Constants
# ============================================================================
# specifies how often to measure values from the Sense HAT (in minutes)
MEASUREMENT_INTERVAL = 10  # minutes
# Set to False when testing the code and/or hardware
# Set to True to enable upload of weather data to Weather Underground
WEATHER_UPLOAD = True
# the weather underground URL used to upload weather data
WU_URL = "http://weatherstation.wunderground.com/weatherstation/updateweatherstation.php"
# some string constants
SINGLE_HASH = "#"
HASHES = "########################################"
SLASH_N = "\n"

# constants used to display an up and down arrows plus bars
# modified from https://www.raspberrypi.org/learning/getting-started-with-the-sense-hat/worksheet/
# set up the colours (blue, red, empty)
b = [0, 0, 255]  # blue
r = [255, 0, 0]  # red
e = [0, 0, 0]  # empty
# create images for up and down arrows
arrow_up = [
    e, e, e, r, r, e, e, e,
    e, e, r, r, r, r, e, e,
    e, r, e, r, r, e, r, e,
    r, e, e, r, r, e, e, r,
    e, e, e, r, r, e, e, e,
    e, e, e, r, r, e, e, e,
    e, e, e, r, r, e, e, e,
    e, e, e, r, r, e, e, e
]
arrow_down = [
    e, e, e, b, b, e, e, e,
    e, e, e, b, b, e, e, e,
    e, e, e, b, b, e, e, e,
    e, e, e, b, b, e, e, e,
    b, e, e, b, b, e, e, b,
    e, b, e, b, b, e, b, e,
    e, e, b, b, b, b, e, e,
    e, e, e, b, b, e, e, e
]
bars = [
    e, e, e, e, e, e, e, e,
    e, e, e, e, e, e, e, e,
    r, r, r, r, r, r, r, r,
    r, r, r, r, r, r, r, r,
    b, b, b, b, b, b, b, b,
    b, b, b, b, b, b, b, b,
    e, e, e, e, e, e, e, e,
    e, e, e, e, e, e, e, e
]


def c_to_f(input_temp):
    return round((input_temp * 1.8) + 32, 1)


def getCPUtemperature():
    # from https://www.raspberrypi.org/forums/viewtopic.php?f=104&t=111457
    res = os.popen('vcgencmd measure_temp').readline()
    return (res.replace("temp=", "").replace("'C\n", ""))

    
def main():
    global last_temp
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
            # we're only going to take measurements every MEASUREMENT_INTERVAL minutes
            if (current_minute == 0) or ((current_minute % MEASUREMENT_INTERVAL) == 0):
                # get the reading timestamp
                now = datetime.datetime.now()
                print("\n%d minute mark (%d @ %s)" % (MEASUREMENT_INTERVAL, current_minute, str(now)))

                # ========================================================
                # read the temperature from the Sense HAT
                # ========================================================
                # Unfortunately, getting an accurate temperature reading from the Sense HAT is improbably
                # https://www.raspberrypi.org/forums/viewtopic.php?f=104&t=111457
                # so we'll have to do some approximation of the actual temp taking CPU temp into account
                # first, get the CPU temp
                cpuTemp = int(float(getCPUtemperature()))
                # next use get_temperature_from_pressure() to read the temp as get_temperature is less accurate
                ambient = sense.get_temperature_from_pressure()
                # calculate the ambient temperature
                calctemp = ambient - ((cpuTemp - ambient) / 1.5)
                # now use it for our purposes
                temp_c = round(calctemp, 1)
                temp_f = c_to_f(temp_c)
                humidity = round(sense.get_humidity(), 2)
                # convert pressure from millibars to inHg before posting
                pressure = round(sense.get_pressure() * 0.0295300, 2)
                print("Temp: %sF (%sC), Pressure: %s inHg, Humidity: %s%%" % (temp_f, temp_c, pressure, humidity))

                # did the temperature go up or down?
                if last_temp != temp_f:
                    if last_temp > temp_f:
                        # display a blue, down arrow
                        sense.set_pixels(arrow_down)
                    else:
                        # display a red, up arrow
                        sense.set_pixels(arrow_up)
                else:
                    # temperature stayed the same
                    # display red and blue bars
                    sense.set_pixels(bars)
                # set last_temp to the current temperature before we measure again
                last_temp = temp_f

                # ========================================================
                # Upload the weather data to Weather Underground
                # ========================================================
                # is weather upload enabled (True)?
                if WEATHER_UPLOAD:
                    # From http://wiki.wunderground.com/index.php/PWS_-_Upload_Protocol
                    print("Uploading data to Weather Underground")
                    # build a weather data object
                    weather_data = {
                        "action": "updateraw",
                        "ID": wu_station_id,
                        "PASSWORD": wu_station_key,
                        "dateutc": "now",
                        "tempf": str(temp_f),
                        "humidity": str(humidity),
                        "baromin": str(pressure),
                    }
                    try:
                        upload_url = WU_URL + "?" + urlencode(weather_data)
                        response = urllib2.urlopen(upload_url)
                        html = response.read()
                        print("Server response:", html)
                        # do something
                        response.close()  # best practice to close the file
                    except:
                        print("Exception:", sys.exc_info()[0], SLASH_N)
                else:
                    print("Skipping Weather Underground upload")

        # wait a second then check again
        # You can always increase the sleep value below to check less often
        time.sleep(1)  # this should never happen since the above is an infinite loop

    print("Leaving main()")


# ============================================================================
# here's where we start doing stuff
# ============================================================================
print(SLASH_N + HASHES)
print(SINGLE_HASH, "Pi Weather Station                  ", SINGLE_HASH)
print(SINGLE_HASH, "By John M. Wargo (www.johnwargo.com)", SINGLE_HASH)
print(HASHES)

# make sure we don't have a MEASUREMENT_INTERVAL > 60
if (MEASUREMENT_INTERVAL is None) or (MEASUREMENT_INTERVAL > 60):
    print("The application's 'MEASUREMENT_INTERVAL' cannot be empty or greater than 60")
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
print("Successfully read Weather Underground configuration values")
print("Station ID:", wu_station_id)
# print("Station key:", wu_station_key)

# ============================================================================
# initialize the Sense HAT object
# ============================================================================
try:
    print("Initializing the Sense HAT client")
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

print("Initialization complete!")

# Now see what we're supposed to do next
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting application\n")
        sys.exit(0)
