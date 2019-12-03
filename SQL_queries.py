#! /usr/bin/env python3
import sqlite3
from sqlite3 import Error
import datetime
import time

from configparser import ConfigParser

#Linux database location is /users/rsg/jkb/Documents/Monocle/sensordata
#Pi database location is /home/pi/Documents/Sensors.db

parser = ConfigParser()

#parser.read('/home/pi/sensor_recorder/Config.ini')
parser.read('Config.ini')

def Sensors_Select():
    """
    Select all sensors in the database and return the data
    """
    try:
        conn=sqlite3.connect(parser.get('database','connection'))
        cur=conn.cursor()       
        cur.execute("SELECT * FROM Sensors")
        rows = cur.fetchall()
        conn.close()
        if(rows == None): 
            rows=[]
        return rows
    except Error as e:
        print("Did not connect, error: {}".format(e))

def Sensors_Update(port, sensorID):
    """
    Select all sensors in the database and return the data
    """
    try:
        conn=sqlite3.connect(parser.get('database','connection'))
        cur=conn.cursor()     
        data = (port, sensorID)
        cur.execute("UPDATE Sensors SET port = (?) WHERE id = (?)", data)
        conn.commit()
        conn.close()
    except Error as e:
        print("Did not connect, error: {}".format(e))

def Sensors_insert(sensorType, sensorPort, uniqueName):
    """
    Insert a new sensor into the Sensors table.
    """
    try:      
        conn=sqlite3.connect(parser.get('database','connection'))
        conn.execute("INSERT INTO Sensors(sensorType, port, uniqueName) VALUES((?),(?),(?))", (sensorType,sensorPort,uniqueName,))
        conn.commit()
        conn.close()
    except Error as e:
        print("Did not connect to database so couldn't insert new sensor, error: {}".format(e))

def Sensors_select_type():
    """
    Select all sensors in the database and return their type
    """
    try:
        conn=sqlite3.connect(parser.get('database','connection'))
        cur=conn.cursor()       
        cur.execute("SELECT sensorType FROM Sensors")
        rows = cur.fetchall()
        conn.close()
        return rows
    except Error as e:
        print("Did not connect, error: {}".format(e))

def Sensors_select_id():
    """
    Select all sensors in the database and return their ID
    """
    try:
        conn=sqlite3.connect(parser.get('database','connection'))
        cur=conn.cursor()       
        cur.execute("SELECT id FROM Sensors")
        rows = cur.fetchall()
        conn.close()
        return rows
    except Error as e:
        print("Did not connect, error: {}".format(e))

def Sensors_select_port():
    """
    Select all sensors in the database and return their associated port
    """
    try:
        conn=sqlite3.connect(parser.get('database','connection'))
        cur=conn.cursor()       
        cur.execute("SELECT port FROM Sensors")
        rows = cur.fetchall()
        conn.close()
        return rows
    except Error as e:
        print("Did not connect, error: {}".format(e))

def BB3_select():
    """
    Select all the data from the BB3 table in the database.
    """
    try:
        conn=sqlite3.connect(parser.get('database','connection'))
        cur=conn.cursor()       
        cur.execute("SELECT currentdate, currenttime, value1, value2, value3, temperature FROM BB3")
        rows = cur.fetchall()
        conn.close()
        return rows
    except Error as e:
        print("Did not connect, error: {}".format(e))


def BB3_insert(Line, sensorID):
    """
    Parameters: date, time, 3 values of readings, temperature
    Inserts the passed data into the database.
    """
    try:      
        conn=sqlite3.connect(parser.get('database','connection'))
        conn.execute("INSERT INTO BB3(sensor_ID, currentdate, currenttime, value1, value2, value3, temperature) VALUES((?),(?),(?),(?),(?),(?),(?))", (sensorID, Line[0], Line[1], Line[3], Line[5], Line[7], Line[8]))
        conn.commit()
        conn.close()
    except Error as e:
        print("Did not connect, error: {}".format(e))


def BB9_insert(Line, sensorID):
    """
    Parameters: date, time, 3 values of readings, temperature

    Inserts the passed data into the database.

    """
    try:
        conn=sqlite3.connect(parser.get('database','connection'))     
        conn.execute("INSERT INTO BB9(sensor_ID, Header, Meter_Type_and_SN, Number_Of_Columns, Packet_Version, Record_Counter, Reference_1, Signal_1, Reference_2, Signal_2, Reference_3, Signal_3, Reference_4, Signal_4, Reference_5, Signal_5, Reference_6, Signal_6, Reference_7, Signal_7, Reference_8, Signal_8, Reference_9, Signal_9, CheckSum) VALUES((?),(?),(?),(?),(?),(?),(?),(?),(?),(?),(?),(?),(?),(?),(?),(?),(?),(?),(?),(?),(?),(?),(?),(?),(?))", (sensorID, Line[0], Line[1], Line[2], Line[3], Line[4], Line[5], Line[6], Line[7], Line[8], Line[9], Line[10], Line[11], Line[12], Line[13], Line[14], Line[15], Line[16], Line[17], Line[18], Line[19], Line[20], Line[21], Line[22], Line[23]))
        conn.commit()
        conn.close()
    except Error as e:
        print("Did not connect, error: {}".format(e))


def BB9_select():
    """
    Select all the data from the BB9 table in the database.

    """
    try:
        conn=sqlite3.connect(parser.get('database','connection'))
        cur=conn.cursor()       
        cur.execute("SELECT * FROM BB9")
        rows = cur.fetchall()
        for row in rows:   
            print(row)
        conn.close()
    except Error as e:
        print("Did not connect, error: {}".format(e))

def BB_select():
    """
    Select all the data from the BB table in the database.

    """
    try:
        conn=sqlite3.connect(parser.get('database','connection'))
        cur=conn.cursor()     
        conn.execute("SELECT * FROM BB")
        rows = cur.fetchall()
        for row in rows:   
            print(row)
        conn.close()
    except Error as e:
        print("Did not connect, error: {}".format(e))



def BB_insert(Line, sensorID):
    """
    Parameters: date, time, scattering reference, scattering signal, thermistor

    Inserts the passed data into the database.

    """
    try:
        conn=sqlite3.connect(parser.get('database','connection'))     
        conn.execute("INSERT INTO BB(sensor_ID, currentdate, currenttime, scattering_reference, scattering_signal, thermistor) VALUES((?),(?),(?),(?),(?),(?))", (sensorID, Line[0], Line[1], Line[2], Line[3], Line[4]))
        conn.commit()
        conn.close()
    except Error as e:
        print("Did not connect, error: {}".format(e))

def NTU_insert(Line, sensorID):
    """
    Parameters: date, time, NTU signal, thermistor

    Inserts the passed data into the database.

    """
    try:
        conn=sqlite3.connect(parser.get('database','connection'))      
        conn.execute("INSERT INTO NTU(sensor_ID, date, time, lambda, NTU_Signal, Thermistor) VALUES((?),(?),(?),(?),(?),(?))", (sensorID, Line[0], Line[1], Line[2], Line[4], Line[5]))
        conn.commit()
        conn.close()
    except Error as e:
        print("Did not connect, error: {}".format(e))

def NTU_select(Line):
    """
    Select all the data from the NTU table in the database.

    """
    try:
        conn=sqlite3.connect(parser.get('database','connection'))
        cur=conn.cursor()       
        cur.execute("SELECT * FROM NTU")
        rows = cur.fetchall()
        for row in rows:   
            print(row)
        conn.close()
    except Error as e:
        print("Did not connect, error: {}".format(e))

def GPS_insert(Line, sensorID):
    """
    Parameters: date, time, NTU signal, thermistor

    Inserts the passed data into the database.

    """

    try:
        conn=sqlite3.connect(parser.get('database','connection'))      
        conn.execute("INSERT INTO GPS(sensor_ID, TIME, Date, Latitude_Value, Latitude_Direction, Longitude_Value, Longitude_Direction, Number_Of_Satelites, GPRMC, GPVTG, GPGGA, GPGSA, GPGSV, GPGLL) VALUES((?),(?),(?),(?),(?),(?),(?),(?),(?),(?),(?),(?),(?),(?))", (sensorID, Line[0], Line[1], Line[2], Line[3], Line[4], Line[5], Line[6], Line[7], Line[8], Line[9], Line[10], Line[11], Line[12]))
        conn.commit()
        conn.close()
    except Error as e:
        print("Did not connect, error: {}".format(e))


def SchemaLooper():
    for schema in SQLSchema:
        try:
            conn=sqlite3.connect(parser.get('database','connection'))      
            conn.execute(schema[1])
            conn.commit()
            conn.close()
            print(schema[0] + " made")
        except Error as e:
            print("Did not connect, error: {}".format(e))


# use a switch factory hybrid so the sensor manager knows which insert statement to use for each sensor.
SQLInsertQueries = [
    ["BB3",BB3_insert],
    ["BB9",BB9_insert],
    ["BB",BB_insert],
    ["NTU",NTU_insert],
    ["GPS_UBLOX7",GPS_insert]
]

SQLSelectQueries = [
    ["BB3",BB3_select]
]


# Another switch factory hybrid to create a table when it doesn't exist, feature still needs to be added to sensor manager.
SQLSchema = [
    ["BB3", "CREATE TABLE BB3(id INTEGER PRIMARY KEY AUTOINCREMENT, sensor_ID NUMERIC, currentdate DATE, currenttime TIME, value1 NUMERIC, value2 NUMERIC, value3 NUMERIC, temperature NUMERIC, FOREIGN KEY (sensor_ID) REFERENCES Sensors(id));"],
    ["BB9", "CREATE TABLE BB9(id INTEGER PRIMARY KEY AUTOINCREMENT, sensor_ID NUMERIC, Header TEXT, Meter_Type_and_SN TEXT, Number_Of_Columns NUMERIC, Packet_Version NUMERIC, Record_Counter NUMERIC, Reference_1 NUMERIC, Signal_1 NUMERIC, Reference_2 NUMERIC, Signal_2 NUMERIC, Reference_3 NUMERIC, Signal_3 NUMERIC, Reference_4 NUMERIC, Signal_4 NUMERIC, Reference_5 NUMERIC, Signal_5 NUMERIC, Reference_6 NUMERIC, Signal_6 NUMERIC, Reference_7 NUMERIC, Signal_7 NUMERIC, Reference_8 NUMERIC, Signal_8 NUMERIC, Reference_9 NUMERIC, Signal_9 NUMERIC, CheckSum TEXT, FOREIGN KEY (sensor_ID) REFERENCES Sensors(id));"],
    ["BB", "CREATE TABLE BB(id INTEGER PRIMARY KEY AUTOINCREMENT, sensor_ID NUMERIC, currentdate DATE, currenttime TIME, scattering_reference NUMERIC, scattering_signal NUMERIC, thermistor NUMERIC, FOREIGN KEY (sensor_ID) REFERENCES Sensors(id));"],
    ["NTU", "CREATE TABLE NTU(id INTEGER PRIMARY KEY AUTOINCREMENT, sensor_ID NUMERIC, currentdate DATE, currenttime TIME, lambda NUMERIC, NTU_Signal NUMERIC, Thermistor NUMERIC, FOREIGN KEY (sensor_ID) REFERENCES Sensors(id));"],
    ["Sensors", "CREATE TABLE Sensors(id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE, sensorType TEXT, port TEXT, uniqueName TEXT);"],
    ["GPS", "CREATE TABLE GPS(EntryID INTEGER PRIMARY KEY AUTOINCREMENT, sensor_ID NUMERIC, Time TIME, Date DATE, Latitude_Value, Latitude_Direction, Longitude_Value, Longitude_Direction, Number_Of_Satelites, GPRMC, GPVTG, GPGGA, GPGSA, GPGSV, GPGLL, FOREIGN KEY (sensor_ID) REFERENCES Sensors(id));"]    
]