from flask import Flask, render_template, jsonify, request
from flask import send_from_directory

app = Flask(__name__, static_url_path="/static")
from random import randrange

# from Sensor_Manager import AddSensor
# import Sensor_Manager
import Restart
from configparser import ConfigParser
import sqlite3
from sqlite3 import Error

import os
import sys 

#Linux database location is /users/rsg/jkb/Documents/Monocle/sensordata.db
#Pi database location is /home/pi/Documents/Sensors.db

parser = ConfigParser()

#parser.read('/home/pi/sensor_recorder/Config.ini')
parser.read('Config.ini')

Data = {}
queue = []

class my_dictionary(dict): 
  
    def __init__(self): 
        self = dict() 
          
    def add(self, key, value): 
        self[key] = value 

import pyudev
import sys
import argparse

def is_usb_serial(device, vid=None, pid=None, vendor=None, serial=None, *args,
                  **kwargs):
    """Checks device to see if its a USB Serial device.
    The caller already filters on the subsystem being 'tty'.
    If serial_num or vendor is provided, then it will further check to
    see if the serial number and vendor of the device also matches.
    """
    if 'ID_VENDOR' not in device:
        return False
    if vid is not None:
        if device['ID_VENDOR_ID'] != vid:
            return False
    if pid is not None:
        if device['ID_MODEL_ID'] != pid:
            return False
    if vendor is not None:
        if 'ID_VENDOR' not in device:
            return False
        if not device['ID_VENDOR'].startswith(vendor):
            return False
    if serial is not None:
        if 'ID_SERIAL_SHORT' not in device:
            return False
        if not device['ID_SERIAL_SHORT'].startswith(serial):
            return False
    return True

def extra_info(device):
    extra_items = []
    if 'ID_VENDOR' in device:
        extra_items.append("vendor '%s'" % device['ID_VENDOR'])
    if 'ID_SERIAL_SHORT' in device:
        extra_items.append("serial '%s'" % device['ID_SERIAL_SHORT'])
    if extra_items:
        return ' with ' + ' '.join(extra_items)
    return ''

def list_devices(vid=None, pid=None, vendor=None, serial=None, *args,
                 **kwargs):
    devs = []
    context = pyudev.Context()
    for device in context.list_devices(subsystem='tty'):
        if is_usb_serial(device, vid=vid, pid=pid, vendor=vendor,
                         serial=serial):
            devs.append([device['ID_VENDOR_ID'], device['ID_MODEL_ID'],
                            extra_info(device), device.device_node])
    return devs

def USBSockets():
    """The main program."""
    parser = argparse.ArgumentParser(
        prog="find-port.py",
        usage="%(prog)s [options] [command]",
        description="Find the /dev/tty port for a USB Serial devices",
    )
    parser.add_argument(
        "-l", "--list",
        dest="list",
        action="store_true",
        help="List USB Serial devices currently connected"
    )
    parser.add_argument(
        "-s", "--serial",
        dest="serial",
        help="Only show devices with the indicated serial number",
        default=None,
    )
    parser.add_argument(
        "-n", "--vendor",
        dest="vendor",
        help="Only show devices with the indicated vendor name",
        default=None
    )
    parser.add_argument(
        "--pid",
        dest="pid",
        action="store",
        help="Only show device with indicated PID",
        default=None
    )
    parser.add_argument(
        "-v", "--verbose",
        dest="verbose",
        action="store_true",
        help="Turn on verbose messages",
        default=False
    )
    parser.add_argument(
        "--vid",
        dest="vid",
        action="store",
        help="Only show device with indicated VID",
        default=None
    )
    args = parser.parse_args(sys.argv[1:])

    if args.verbose:
        print('pyudev version = %s' % pyudev.__version__)

    devices = list_devices(**vars(args))
    Data = my_dictionary()
    counter = 0
    text1 = "Device is "
    text2 = ", the port used is: "
    for item in devices:
        tempList = [text1,item[0],item[1], text2, item[3]]
        Data.add(counter,tempList)
        counter +=1
    return Data

    context = pyudev.Context()
    for device in context.list_devices(subsystem='tty'):
        if is_usb_serial(device, **vars(args)):
            print(device.device_node)
            return 
    sys.exit(1)

def GetSensorsFromDatabase():
    try:
        conn=sqlite3.connect(parser.get('database','connection'))
        cur=conn.cursor()       
        cur.execute("SELECT sensorType FROM Sensors")
        rows = cur.fetchall()
        conn.close()
    except Error as e:
        print("Did not connect, error: {}".format(e))
    
    try:
        conn=sqlite3.connect(parser.get('database','connection'))
        cur=conn.cursor()       
        cur.execute("SELECT id FROM Sensors")
        IDs = cur.fetchall()
        conn.close()
    except Error as e:
        print("Did not connect, error: {}".format(e))
  
    Data = my_dictionary()     
    for item in range(len(rows)):    
        Data.add(str(IDs[item]),rows[item])          
    return Data

def AssignValues(value):
    try:
        print("we got here")
        conn=sqlite3.connect(parser.get('database','connection'))
        cur=conn.cursor()       
        cur.execute("SELECT EntryID, Time, Date, Latitude_Value, Latitude_Direction, Longitude_Value, Longitude_Direction, Number_Of_Satelites, GPRMC, GPVTG, GPGGA, GPGSA, GPGSV, GPGLL FROM GPS WHERE sensor_ID = {} ORDER BY EntryID DESC LIMIT 10".format(value))
        rows = cur.fetchall()
        print(rows)
        conn.close()
        print("we also got here")
    except Error as e:
        print("Did not connect, error: {}".format(e))  
    for item in range(len(rows)):
        Data = my_dictionary() 
        Data.add(item*3,rows[item])     
        if((len(queue) >= 10)):
            queue.pop(0)
        queue.append(Data)    
        Data = {}
    return queue

def MakeQueue(NewData):
    if((len(queue) > 10)):
        queue.pop(0)
    queue.append(NewData)
    return queue

def randomValues(DicData):
    for index in range(9):
        num = randrange(1000)
        DicData.add(num*3,num)
    return DicData

@app.route("/sensorOutput")
def SensorOutput():
    return render_template('ViewOutput.html', title='Output')

@app.route("/Wifi_Setup")
def WifiConnection():
    return render_template('Wifi_Setup.html', title='Wifi Setup')

@app.route("/add_sensor")
def AddSensorPage():
    return render_template('Add_sensor.html', title='Add sensor')

@app.route("/", methods=['GET','POST'])
def StatusPage():
    if(request.method == 'GET'):
        return render_template('index_status.html', title='Home')
    else:
        pass
        


@app.route('/js/<path:path>')
def send_js(path):
    return send_from_directory('js', path)


@app.route('/latest_sensor_data/<ID>',methods=['GET'])
def GetSensorData(ID):
    queue = AssignValues(ID)
    return jsonify(queue)

@app.route('/list_of_sensors')
def GetSensors():
    myDictionary = GetSensorsFromDatabase()
    return jsonify(myDictionary)

@app.route('/usb_connections')
def SendConnections():
    deviceConnections = USBSockets()
    return deviceConnections

@app.route('/createSensor/<sensor>/<port>/<uniqueName>',methods=['GET'])
def CreateSensor(sensor, port, uniqueName):
    # print(port)
    import threading
    x = threading.Thread(target=CallRestart(sensor,port, uniqueName))
    x.start()
    # Sensor_Manager.AddSensor(sensor,port)
    # return Sensor_Manager.AddSensor(sensor,port)
    return 200
    
def CallRestart(sensor, port, uniqueName):
    import time
    time.sleep(4)
    Restart.AddRestart(sensor,port, uniqueName)

# @app.route('/displaybytes/<port>',methods=['GET'])
# def GetBytes(port):
#     import serial
    
#     print("test 2")
#     realPort = '/dev/'+port
#     with serial.Serial(realPort, 19200, timeout=1) as ser:
#         x = ser.read(100)
#         print(x)
#     return(x)

@app.route('/Wifi_Data/<connection>/<password>',methods=['GET'])
def GetWifiConnection(connection, password):
    print("Connection is {}, password is {}".format(connection, password))

if __name__ == "__main__":
    app.run()