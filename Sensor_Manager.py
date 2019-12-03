#! /usr/bin/env python3
from Sensor_Factory import sensors
from SQL_queries import Sensors_Select
import Sensor_Factory
from SQL_queries import Sensors_insert
from SQL_queries import Sensors_select_type
from SQL_queries import Sensors_select_id
from SQL_queries import Sensors_select_port
from SQL_queries import Sensors_Update
from functools import partial
from SQL_queries import SQLInsertQueries
from configparser import ConfigParser
import threading
import collections
import concurrent.futures
import queue
import time
from SQL_queries import SchemaLooper 

portsTaken = [["ttyACM0",False],["ttyACM1",False],["ttyUSB0",False],["ttyUSB1",False]]

class SensorThreader(threading.Thread):
    """
    Class to move each sensor object operations into its own thread.
    This also allows each output from the sensor to be moved into a queue which acts as a funnel to insert the outputs into a database.
    This avoids currupting the data and the need to avoid locking all threads except the one which most recently recieved data, 
    as the whole database in sqlite3 gets locked when data is inserted.
    """
    def __init__(self, name):
        super().__init__()
        self.name = name

    def sensorThread(self, queue, event, sensorObject, sensorType, sensorID):
        """
        This is a thread that will remain active until an 'end event' has been triggered.
        It will continously read data from the sensor that has been passed in, and put that data into a queue.
        """
        while not event.is_set():
            try:
                line = next(sensorObject)
                sensorData = [sensorType, line, sensorID]
                queue.put(sensorData)
            except Exception as message:
                print(message)
                print(type(message))
                

            
        print("sensorThread {} ID:{} received end event. Exiting.".format(sensorType, sensorID))

def DatabaseAccessor(queue, event):
    """
    Thread which reads the next item in the queue and sends it to the function SQLFinder which inserts it into the database.
    This thread is always active until the 'end event' is trigered, and the queue is empty.
    """
    
    while not event.is_set() or not queue.empty():
        sensorData = queue.get()
        #         sensorType     line of data   unique sensor id
        SQLFinder(sensorData[0], sensorData[1], sensorData[2])

def SQLFinder(sensor, line, sensorID):
    """
    This function searches through the implemented sql insert statements to find the one for the sensor passed in.
    If a match is found, it then inserts the line of data into the sql table.
    """
    # Check the implemented list of queries and find the one implemented for the current sensor.
    for queryIndex in range(len(SQLInsertQueries)):
        if(SQLInsertQueries[queryIndex][0] == sensor):
            newInsert = partial(SQLInsertQueries[queryIndex][1])
            newInsert(line, sensorID)
            print("Sensor {}, output {}".format(sensor,line))


def AddSensor(newSensor, port, uniqueName):
    # print("Please enter the names of the sensors you wish to record data.")
    # print("Type 'Done' once you have entered all the sensors you wish you use.")
    print("Thank you for adding this sensor")

    requestedSensor = newSensor
    requestedSensor = requestedSensor.upper()

    # Read in sensors from user and store them in the config file.
    portIndex = portFinder(port)
    if(portIndex != "nope"):
        f= open('Config.ini', 'a')
        f.write('\n\n'+'['+requestedSensor + '_' + uniqueName+']'+'\n'+'sensor = '+requestedSensor)
        f.close()

        Sensors_insert(requestedSensor, port, uniqueName)

        import os    
        import psutil
        import logging
        
        try:
            p = psutil.Process(os.getpid())
            return(p)
            # for handler in p.open_files() + p.connections():
            #     os.close(handler.fd)
        except Exception as e:
            logging.error(e)
        # python = sys.executable
        # os.execl(python, python, *sys.argv) 
    else:
        print("That port is already taken. Please check your port selection again.")
    return "Not happy"

def portFinder(port):
    for portIndex in range(len(portsTaken)):
        if(portsTaken[portIndex][1] == False):
            if(portsTaken[portIndex][0] == port):
                portsTaken[portIndex][1] = True
                return portsTaken[portIndex][0]
    return "nope"

def Main():
    """
    The main function which is run when the program starts up.
    It reads in the sensors the user requested, and sorts through approving them, and checking them against ones already set up in the database,
    in the event that the software is being restarted.
    After ensuring all the sensors are set up in the database, it sends each sensor object into its own thread to read data.
    """

    portsTaken = [["ttyACM0",False],["ttyACM1",False],["ttyUSB0",False],["ttyUSB1",False]]
    import os
    import sys
    import psutil
    import logging
    print(psutil.Process(os.getpid()))

    SchemaLooper()

    requestedSensorList = []
    configSensorTypeIndex = {'BB3':0, 'BB9':0, 'BB':0, 'NTU':0, 'GPS1':0, 'GPS_ublox7':0, 'RTK':0}

    # Get all the requested sensors in the config file into a list.
    parser = ConfigParser()
    parser.read('Config.ini')
    for each_section in parser.sections():
        if(each_section == "database" or each_section == "UserRequest"):
            pass
        elif(each_section == "sensorCounters"):
            configSensorTypeIndex['BB3'] = parser.get(each_section, 'BB3')
            configSensorTypeIndex['BB9'] = parser.get(each_section, 'BB9')
            configSensorTypeIndex['BB'] = parser.get(each_section, 'BB')
            configSensorTypeIndex['NTU'] = parser.get(each_section, 'NTU')
            configSensorTypeIndex['GPS1'] = parser.get(each_section, 'GPS1')
            configSensorTypeIndex['GPS_ublox7'] = parser.get(each_section, 'GPS_ublox7')
            configSensorTypeIndex['RTK'] = parser.get(each_section, 'RTK')
        else:
            requestedSensorList.append(parser.get(each_section, 'sensor'))

    sensorTypeList = []

    # Sort through the list of sensors to find ones which have been implemented in the software, and create objects of those sensors.
    for currentSensor in requestedSensorList:
        implementation = False
        # when making the sensors, check to see if they have been implemented in the factory pattern.
        for singleSensor in sensors:    
            # If the sensor has been implemented, then make the object, perform the first reading to instantiate it, then add it to a sensor list.
            if(currentSensor == singleSensor):
                implementation = True
                singleSensor = singleSensor.upper()
                sensorTypeList.append(singleSensor)
        if(implementation == False):
            print("The sensor {} has not been implemented yet.".format(currentSensor))
    # Get sensors that are already in the database and store them in a list for cross-refferencing.
    currentSensors = Sensors_select_type()
    newSensorList = []
    if(type(currentSensors) is 'NoneType' or not currentSensors):
        print("No sensors in database.")
    else:
        for sensor in currentSensors:
            newSensorList.append(sensor[0])
            
    # Make a copy of the sensors requested to iterate through
    # then sort through the ones made in the database compared to the ones in the config file.
    # If a sensor does exist in both then remove it from the list of approved sensors.
    # The remaining sensors will then be added to the database.
    approvedSensorsToAdd = sensorTypeList[::]
    if(len(newSensorList) == 0):
        print("There are no sensors in the database.")
    else:
        for approvedSensor in sensorTypeList:
            if(approvedSensor in newSensorList):
                newSensorList.remove(approvedSensor)
                approvedSensorsToAdd.remove(approvedSensor)
            else:
                print("{} is not in list of approved sensors.".format(approvedSensor))
                pass
    sensorPorts = Sensors_select_port()

    # Add approved sensors that are in the config file to the database.
    for eachSensorIndex in range(len(approvedSensorsToAdd)):
        Sensors_insert(approvedSensorsToAdd[eachSensorIndex], sensorPorts[eachSensorIndex])
        print("{} has been Inserted into the database.".format(approvedSensorsToAdd[eachSensorIndex]))

    FinalListOfSensors = []
    dbSensors = Sensors_Select()

    for dbSensor in range(len(dbSensors)):
        dbSensorTuple = dbSensors[dbSensor]
        for approvedSensor in range(len(sensorTypeList)):
            if(sensorTypeList[approvedSensor] == dbSensorTuple[1]):
                FinalListOfSensors.append(dbSensorTuple)
                del sensorTypeList[approvedSensor]
                break
    threadExecutor = concurrent.futures.ThreadPoolExecutor()
    pipeline = queue.Queue(maxsize=1000000)
    endEvent = threading.Event()
    threadExecutor.submit(DatabaseAccessor, pipeline, endEvent)  
    # portsTaken = [["ttyACM0",False],["ttyACM1",False],["ttyUSB0",False],["ttyUSB1",False]]

    for finalSensor in FinalListOfSensors:
        newSensor = Sensor_Factory.factory(finalSensor[1],finalSensor[2])
        portIndex = portFinder(finalSensor)
        if(portIndex != "nope"):
            sensor = newSensor.Reading()
            line = next(sensor)                   
            sensorObject = SensorThreader(finalSensor[1])
            threadExecutor.submit(sensorObject.sensorThread, pipeline, endEvent, sensor, finalSensor[1], finalSensor[0])
            print("this port is {}".format(portIndex))
            continue
        else:
            for portIndex in range(len(portsTaken)):
                if(portsTaken[portIndex][1] == False):
                    try:
                        newSensor = Sensor_Factory.factory(finalSensor[1],portsTaken[portIndex][0])
                        sensor = newSensor.Reading()
                        line = next(sensor)
                        portsTaken[portIndex][1] = True
                        sensorObject = SensorThreader(finalSensor[1])
                        threadExecutor.submit(sensorObject.sensorThread, pipeline, endEvent, sensor, finalSensor[1], finalSensor[0])
                        Sensors_Update(portsTaken[portIndex][0], finalSensor[0])
                        break
                    except Exception as error:
                        print("You have requested more sensors then there are plugged in, please check your port connections.")
                        print("Error was: {}".format(error))
                        #print("Nope. No idea. Explode!")
        
    while True:
        pass

if __name__ == "__main__":
    Main()


# [database]
# connection=/users/rsg/jkb/Documents/Monocle/sensordata.db
# type=sqlite3