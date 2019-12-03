#! /usr/bin/env python3

# import the sensors
from BB3 import BB3
from BB9 import BB9
from BB import BB
from NTU import NTU
from GPS_ublox7 import GPS_UBLOX7

# Write constant values for each sensor
CONST_BB3 = "BB3"
CONST_BB9 = "BB9"
CONST_BB = "BB"
CONST_NTU = "NTU"
CONST_GPS_UBLOX7 = "GPS_UBLOX7"

# Put the sensors into a dictionary so the class for each sensor can be instantiated.
sensors = {
    CONST_BB3: BB3,
    CONST_BB9: BB9, 
    CONST_BB: BB,
    CONST_NTU: NTU,
    CONST_GPS_UBLOX7: GPS_UBLOX7
}

def factory(type, port):
    """
    When a sensor name is passed in, return an object of that sensor.
    """
    if type in sensors.keys():
        return sensors[type](port)