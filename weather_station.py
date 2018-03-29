#!/usr/bin/python
# ****************************************************************************************
#  AWS Pi Temperature Station
#  By Dan Beerman
# ------------------------------------------
#  This is a Raspberry Pi project that measures weather values (temperature, humidity and pressure) using
#  the Astro Pi Sense HAT then uploads the data to a Weather Underground weather station.
#  Opens Source refs from: much of the Pi HAT code attributed John Wargo's wonderful walkthrough found here:
#  Many thanks to Mr. Kramer for hookin me up on the AWS mentorship.
#  great ref on AWS: Calvin Boey (https://github.com/szazo/DHT11_Python)
# ****************************************************************************************
from __future__ import print_function
import datetime
import os
import sys
import time
from urllib import urlencode
import urllib2
import socket

from sense_hat import SenseHat
from config import Config
# ============================================================================
# Constants  (Change vals when testing the code, etc)
# ============================================================================
# how often POST data / save Sense HAT measurements (in minutes)
MEASUREMENT_INTERVAL = 1
# Enable upload for various endpoints:
WEATHER_UPLOAD = True
AWS_UPLOAD = True
# Endpoint address:
WU_URL = "http://weatherstation.wunderground.com/weatherstation/updateweatherstation.php"
EC2 = "http://ec2-34-210-122-38.us-west-2.compute.amazonaws.com:3000/"
# for style
SINGLE_HASH = "|"
HASHES = "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
SLASH_N = "\n"
# LED display settings
LOW_LIGHT_MODE = True
b = [0, 0, 255]  # blue
r = [255, 0, 0]  # red
e = [0, 0, 0]  # empty
# constants used to display an up and down arrows plus bars
# modified from https://www.raspberrypi.org/learning/getting-started-with-the-sense-hat/worksheet/
# set up the colours (blue, red, empty)
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
    # convert Celsius to Fahrenheit
    return (input_temp * 1.8) + 32

def get_cpu_temp():
    # 'borrowed' from https://www.raspberrypi.org/forums/viewtopic.php?f=104&t=111457
    # executes a command at the OS to pull in the CPU temperature
    res = os.popen('vcgencmd measure_temp').readline()
    return float(res.replace("temp=", "").replace("'C\n", ""))

def get_smooth(x):
    # use moving average to smooth readings
    # do we have the t object?
    if not hasattr(get_smooth, "t"):
        # then create it
        get_smooth.t = [x, x, x]
    # manage the rolling previous values
    get_smooth.t[2] = get_smooth.t[1]
    get_smooth.t[1] = get_smooth.t[0]
    get_smooth.t[0] = x
    # average the three last temperatures
    xs = (get_smooth.t[0] + get_smooth.t[1] + get_smooth.t[2]) / 3
    return xs


def get_temp():
    # ====================================================================
    # Getting an accurate temperature reading from the Sense HAT is improbable:
    # https://www.raspberrypi.org/forums/viewtopic.php?f=104&t=111457
    # The Pi foundation recommended using the following:
    # http://yaab-arduino.blogspot.co.uk/2016/08/accurate-temperature-reading-sensehat.html
    # ====================================================================
    # First, get temp readings from both sensors
    t1 = sense.get_temperature_from_humidity()
    t2 = sense.get_temperature_from_pressure()
    # t becomes the average of the temperatures from both sensors
    t = (t1 + t2) / 2
    # Now, grab the CPU temperature
    t_cpu = get_cpu_temp()
    # Calculate the 'real' temperature compensating for CPU heating
    t_corr = t - ((t_cpu - t) / 1.5)
    # Finally, average out that value across the last three readings
    t_corr = get_smooth(t_corr)
    # convoluted, right?
    # Return the calculated temperature
    return t_corr

def toggleLLmode():
    # Toggle the brightness on the LED display 
    LOW_LIGHT_MODE = (LOW_LIGHT_MODE != True)
    if (LOW_LIGHT_MODE):
	sense.low_light = True
    else:
	sense.low_light = False

def joystickPress():
    # Set the effects of pressing the joystick
    toggleLLmode()
    sense.set_pixel(str(LOW_LIGHT_MODE))
    sense.clear()

def pushed_up(event):
    sense.show_message(str(socket.gethostbyname(socket.gethostname()))
    sense.clear()

def pushed_down(event):
    sense.show_message("HIRE ME!",
                       text_colour=[255, 255, 0], scroll_speed=0.5)
    sense.clear()

def pushed_left(event):
    sense.show_message("EXECUTE ORDER 66", text_colour=b, scroll_speed=0.8)
    sense.clear()

def pushed_right(event):
    sense.show_message("Hi Adam! (and Ryan?)", text_colour=r, scroll_speed=0.5)
    sense.clear()

# Listen for joystick key
sense.stick.direction_up = pushed_up
sense.stick.direction_down = pushed_down
sense.stick.direction_left = pushed_left
sense.stick.direction_right = pushed_right

def main():
    global last_temp
    # initialize the lastMinute variable to the current time to start
    # on startup, just use the previous minute as lastMinute
    last_minute = datetime.datetime.now().minute
    last_minute -= 1
    if last_minute == 0:
        last_minute = 59

    while 1:
        # infinite loop to continuously check weather values
        # Measure every 5 seconds - for smoothing algorithm, POST every MEASUREMENT_INTERVAL
        current_second = datetime.datetime.now().second
        if (current_second == 0) or ((current_second % 5) == 0):
            # ========================================================
            # Read values from the Sense HAT
            # ========================================================
            # get_temp function 'adjusts' the recorded temp in order to accommodate radiation from the processor
            # When Sense HAT is mounted on the Pi in a case, is significant.
            # NOTE: when the Sense HAT is external, comment this out (#):
            calc_temp = get_temp()
            # Then uncomment either of the following:
            # calc_temp = sense.get_temperature_from_pressure()
            # calc_temp = sense.get_temperature_from_humidity()
            # ========================================================
            # Now get the data packaged up:
            temp_c = round(calc_temp, 1)
            temp_f = round(c_to_f(calc_temp), 1)
            humidity = round(sense.get_humidity(), 0)
            # convert P from millibars to inHg before POST
            pressure = round(sense.get_pressure() * 0.0295300, 1)
            print("Temp: %sF (%sC), Pressure: %s inHg, Humidity: %s%%" % (temp_f, temp_c, pressure, humidity))
	        sense.show_message(str(temp_f)+"°F")
            # get the current minute
            current_minute = datetime.datetime.now().minute
            # is it the same minute as the last time we checked?
            if current_minute != last_minute:
                last_minute = current_minute
                # Take measurements every MEASUREMENT_INTERVAL
                if (current_minute == 0) or ((current_minute % MEASUREMENT_INTERVAL) == 0):
                    # timestamp
                    now = datetime.datetime.now()
                    print("\n%d minute mark (%d @ %s)" % (MEASUREMENT_INTERVAL, current_minute, str(now)))
                    # did the temperature go up or down? Changes disp. momentarily
                    if last_temp != temp_f:
                        if last_temp > temp_f:
                            sense.set_pixels(arrow_down)
                        else:
                            sense.set_pixels(arrow_up)
                    else:
                        # temperature stayed the same: Bars!
                        sense.set_pixels(bars)
                    # save the temp
                    last_temp = temp_f
                    # ========================================================
                    # SHAPE THE POST DATA
                    # ========================================================
                    weather_data = {
                        "action": "updateraw",
                        "ID": wu_station_id,
                        "PASSWORD": wu_station_key,
                        "dateutc": now,
                        "tempf": str(temp_f),
                        "humidity": str(humidity),
                        "baromin": str(pressure),
                    }
                    # ========================================================
                    # UPLOAD TO EC2   (UPLOAD === True?)
                    # ========================================================
                    if AWS_UPLOAD:
                        print("Uploading data to EC2 Instance")
                        try:
                            url_data = urlencode(weather_data)
                            response = urllib2.urlopen(EC2, url_data)
                            html = response.read()
                            # on succesful upload - have a visual cue!
                            print("Server response:", html)
                            sense.show_message("✓ POSTED", text_colour=[
                                               32, 178, 170], back_colour=[0, 100, 0])
			                sense.clear()
                            response.close()  # best practice to close the file
                        except:
                            print("Exception: ", sys.exc_info()[0], SLASH_N)
                            sense.show_message(str(sys.exc_info()[0]), text_colour=[
                                               0, 255, 0], back_colour=[0, 0, 255])
                    else:
                        print("Skipping AWS Upload")
                    # ========================================================
                    # UPLOAD TO WU    (UPLOAD === True)
                    # ========================================================
                    # is weather upload enabled (True)?
                    if WEATHER_UPLOAD:
                        # From http://wiki.wunderground.com/index.php/PWS_-_Upload_Protocol
                        print("Uploading data to Weather Underground")
                        try:
                            upload_url = WU_URL + "?" + urlencode(weather_data)
                            response = urllib2.urlopen(upload_url)
                            html = response.read()
                            # on succesful upload - have a visual cue!
                            print("Server response:", html)
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
print(SINGLE_HASH, "ClimaStatus - a Pi HAT Weather Station     ", SINGLE_HASH)
print(SINGLE_HASH, "By Dan Beerman. POSTing data to WU and AWS:", SINGLE_HASH)
print(SINGLE_HASH, "Temp, Humidity, Barometric Pressure        ", SINGLE_HASH)
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
print("Station key:", wu_station_key)

# ============================================================================
# initialize the Sense HAT object
# ============================================================================
try:
    print("Initializing the Sense HAT client")
    sense = SenseHat()
    sense.set_rotation(0)
    # then write some text to the Sense HAT's 'screen'
    # sense.show_message("Low Light: " + LOW_LIGHT_MODE, scroll_speed=0.5)
    sense.show_message("Party On!", text_colour=[255, 255, 0], back_colour=[0, 0, 255])
    # clear the screen
    sense.clear()
    # get the current temp to use when checking the previous measurement
    last_temp = round(c_to_f(get_temp()), 1)
    print("Current temperature reading: ", last_temp)
except:
    print("Unable to initialize the Sense HAT library:", sys.exc_info()[0])
    sys.exit(1)

print("Initialization complete - posting data to endpoints!")

# Now see what we're supposed to do next
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sense.show_message("Goodbye")
        print("\nExiting application\n")
        sys.exit(0)
