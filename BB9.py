#!/bin/python

"""
REPLACE WITH DESCRIPTION

Author : jkb (Jaime Kershaw Brown)
Date : 21/10/2019

"""

#! /usr/bin/env python3

try:
    import serial 
except ImportError as message:
    print("Failed to import serial reader, maybe it is not installed correctly? Error was: {}".format(message))

try: 
    import datetime
except ImportError as message:
    print("Failed to import datetime, maybe it is not installed correctly? Error was: {}".format(message))

try:
    import time
except ImportError as message:
    print("Failed to import time, maybe it is not installed correctly? Error was: {}".format(message))

try:
    from BBX_Sensors import BBX
except ImportError as message:
    print("Failed to import BBX from BBX_Sensors, maybe file is missing? Error was: {}".format(message))

try:
    from dummy_sensors import DummyBB9Sensor
except ImportError as message:
    print("Failed to import DummyBB9Sensor from dummy_sensors, maybe file is missing? Error was: {}".format(message))

try:
    from functools import reduce
except ImportError as message:
    print("Failed to import reduce from functools. Error message was {}.".format(message))


class BB9(BBX):
    """
    The BB9 class to read in data live while in-situ

    Uses a time taken per line read formula to adjust the time to wait between making checks.

    Reads in all the data in the buffer, then splits it up into lines, and processes them individually.
    """

    def __init__(self, port):
        self.port = port

    def CreateChecksum(self, currentLine):

        """
        calculates the checksum based off the rest of the data bassed in.
                    
        :param self: DESCRIBE PARAMETERE
        :param type: PARAMTER TYPE

        :param  currentLine: DESCRIBE PARAMETERE
        :param type: PARAMTER TYPE
        """
        delim = '\t'
        line = reduce(lambda x,y: str(x) + delim + str(y), currentLine, "" )
        # now reduce wasn't a perfect choice due to our inital value
        # so we still need to move the \t from the begining to the end
        #line = line[1:] + "\t" ## actually we don't as addition is commuatble
        stringList = list( line )
        byteList   = list( map( ord, stringList ))
        #hexList = list(map( lambda x: hex(x), byteList ))
        checkSum = reduce(lambda x,y: x + y, byteList, 0)
        hexSum = "{:x}".format(checkSum)
        return hexSum

    def Reading(self):

        """
        Generator function to read in data from the sensor.

        Uses a time taken per line read formula to adjust the time to wait between making checks.

        Reads in all the data in the buffer, then splits it up into lines, and processes them individually.   
        """

        #Initialise values
        leftoverData = ""
        lineOfData = b''
        bitOfData = b''
        numberOfChecksToMake = 10
        timeToSleep = 1
        targetCheckPerLine = 1.3
        targetLinePerCheck = 1 / targetCheckPerLine

        try:
            myPort = '/dev/'+self.port
            serialReader = serial.Serial(myPort,self.baudRate,timeout=self.timeoutLength)
            #serialReader = DummyBB9Sensor()

            # Constantly run the loop to read data from the sensor.
            while True:
                lineCount = 0
                # The number of checks to make
                for i in range(numberOfChecksToMake):
                    time.sleep(timeToSleep)
                    
                    # If there is any data in the buffer continue
                    if serialReader.in_waiting != 0:
                        bitOfData = serialReader.read(serialReader.in_waiting)
                        lineOfData = lineOfData + bitOfData
                        bitOfData = b""
                        
                        # If there is a full line in the data taken out of the buffer
                        if(b"\r\n" in lineOfData):
                            stringLine = lineOfData.decode('utf-8')
                            listOfLines = stringLine.split("\r\n")
                            
                            # Check if there is any data from the next line stored, if so put it on the next item.
                            if(len(listOfLines) > 1):
                                listOfLines[0] = leftoverData + listOfLines[0]
                                leftoverData = listOfLines[-1]
                                del listOfLines[-1]
                            
                            # For each line of data stored (one or more), yield it off to the sensor manager.
                            if(len(listOfLines) > 0):
                                for singleLine in listOfLines:
                                    lineCount += 1
                                    stringLine = singleLine.split()
                                    checkSum = self.CreateChecksum(stringLine[0:len(stringLine)-1])
                                    if(stringLine[-1] == checkSum):
                                        HeaderAndMeterType = stringLine[0].split("_")
                                        stringLine.inserialReadert(0, HeaderAndMeterType[0])
                                        stringLine.inserialReadert(1, HeaderAndMeterType[1])
                                        del stringLine[2]
                                        yield (stringLine)
                                    else:
                                        print("Line of data is currupted.")
                                lineOfData = b""
                        else:
                            pass
                
                # Calculate the time needed to wait between checking the buffer, and adjust accordingly
                linesPerCheck = lineCount / numberOfChecksToMake
                print("Time of {}s gave us {} lines per check".format(timeToSleep, linesPerCheck))
                newTimeToSleep = timeToSleep * (targetLinePerCheck / linesPerCheck)
                timeToSleep = newTimeToSleep
                if(numberOfChecksToMake < 100):
                    numberOfChecksToMake += 10

        except ValueError as message:
            print("Did not manage to connect to sensor properly, check your settings. Error was: {}".format(message))
        except serialReader.serialReaderialException as message:
            print("Did not read data from sensor properly, check your settings. Error was: {}".format(message))
