#! /usr/bin/env python3
"""
Program to read in data from the GPS.
"""

try:
    import serial
except ImportError as message:
    print("Failed to import serial, maybe it is not installed correctly? Error was: {}".format(message))

try:
    import time
except ImportError as message:
    print("Failed to import time, maybe it is not installed correctly? Error was: {}".format(message))

from dummy_sensors import DummyGPS


def RemoveGPTXT(lines): 
    """
    Remove all the GPTXT (device descriptive) lines
    """
    linesToRemove = lines.count("$GPTXT")
    for r in range(linesToRemove):
        firstRemoveIndex = lines.find("$GPTXT")
        secondRemoveIndex = lines.find("\n", firstRemoveIndex+1)        
        lines = lines[:firstRemoveIndex] + lines[secondRemoveIndex:]
    return (lines)

def FindLeftOverData(all_lines):
    """
    Find any data that is part of the next "line" of data and temporarily store it for when the rest comes through.
    """
    start = all_lines.rfind("$GPRMC")              
    leftoverData = all_lines[start:]          
    all_lines = all_lines[:start]
    return(all_lines, leftoverData)

def OrderData(splitData, listOfData, NMEA_TAGS, GPRMC):
    """
    Go through the data entered, and sort it into a list that is appropriate for sending to the sensor manager.
    Extract the important data into the first few elements, then store the raw lines into their own elements, sorted by type of NMEA tag.
    """
    for lineOfData in splitData:
        code = lineOfData[:6]
        code = code[1:]
        lineOfData = lineOfData.split(",") 
        for x in range(len(NMEA_TAGS)):
            if(code == "GPRMC"):
                listOfData[2] = lineOfData[3]
                listOfData[3] = lineOfData[4]
                listOfData[4] = lineOfData[5]
                listOfData[5] = lineOfData[6]
                listOfData[0] = lineOfData[1]
                listOfData[1] = lineOfData[9]
                listOfData[7] = GPRMC + ",".join(lineOfData)
            elif(NMEA_TAGS[x][0] == code):
                listOfData[x+8] = listOfData[x+8] + ",".join(lineOfData)
                                   
    return(listOfData)

class GPS_UBLOX7:
    """
    The GPS sensor class to read in data live while in-situ.

    Reads in a line of data, then after checking a certain number of times to see if there is data, adjust a waiting timer.

    The waiting timer is adjusted to avoid unnecessary CPU usage on the Raspberry Pi.
    """
    def __init__(self, port):
        self.port = port


    def Reading(self):
        """
        Generator function to read in data from the GPS.
        
        Uses a time taken per line read formula to adjust the time to wait between making checks.

        Reads in all the data in the buffer, then splits it up into lines, and processs them individually.
        
        """
        # Initialise values
        leftoverData = ""
        lineOfData = b''
        bitOfData = b''
        numberOfChecksToMake = 10
        timeToSleep = 1
        targetChecksPerLine = 1.3
        targetLinesPerCheck = 1/targetChecksPerLine
        # print(self.port)
        try:
            myPort = '/dev/'+self.port
            ser = serial.Serial(myPort, 19200, timeout = None)
            #ser = DummyGPS()
            # Read data from the sensor continously in this loop.
            while True:  
                lineCount = 0     
                # The number of checks to make 
                for i in range(numberOfChecksToMake):
                    time.sleep(timeToSleep)
                    # Check if there is anything in the buffer to be collected.
                    if ser.in_waiting != 0:
                        bitOfData = ser.read(ser.in_waiting)
                        lineOfData = lineOfData + bitOfData
                        bitOfData = ""
                        # Checking if there are two $GPRMC tags in the line, as that is used to signal the start and end of a reading.
                        if(lineOfData.count(b"$GPRMC") >= 2):
                            
                            # Sort the data so it is ready to be processed by decoding it, adding any missing data, removing excess data.
                            all_lines = lineOfData.decode('utf-8')                           
                            all_lines = leftoverData + all_lines                          
                            all_lines = RemoveGPTXT(all_lines)
                            all_lines, leftoverData = FindLeftOverData(all_lines)

                            # Split up data into single readings by the start and end NMAE tags in the block of data.
                            lineStarts = all_lines.count("$GPRMC")
                            lineEnds = all_lines.count("$GPGLL")
                            lineDifference = lineStarts - lineEnds
                            if(lineDifference > 0):
                                lineIterations = lineDifference
                            else:
                                lineIterations = lineStarts
                            
                            # for each reading in the datablock, process it and yield it back to the sensor manager.
                            for f in range(lineIterations):    
                                firstIndex = all_lines.find("$GPRMC")
                                secondIndex = all_lines.find("$GPRMC", firstIndex+1)
                                dataGroup = all_lines[:secondIndex] 
                                lineCount += 1
                              
                                splitData = dataGroup.split()

                                # set up a case select/switch statement to sort the NMEA data by its tag
                                GPRMC = ""
                                GPVTG = ""
                                GPGGA = ""
                                GPGSA = ""
                                GPGSV = ""
                                GPGLL = ""                 
                                NMEA_TAGS = [
                                    ["GPVTG",GPVTG],
                                    ["GPGGA",GPGGA],
                                    ["GPGSA",GPGSA],
                                    ["GPGSV",GPGSV],
                                    ["GPGLL",GPGLL]
                                ]

                                #             currentTime   currentDate  latitudeValue  latitudeDirection    longitudeValue     longitudeDirection    numberOfSatelites     GPRMC    GPVTG   GPGGA  GPGSA  GPGSV  GPGLL
                                listOfData = [0,            0,           0,             "",                  0,                 "",                   0,                    "",      "",     "",    "",    "",    ""]

                                Data = OrderData(splitData, listOfData, NMEA_TAGS, GPRMC)

                                yield(Data)
                                
                                # remove the recently inserted row of data from the datablock.
                                all_lines = all_lines[secondIndex:]                                       
                            lineOfData = b""
                
                try:
                    #print( "Time of {}s gave us {} lines per check".format(timeToSleep, linesPerCheck ))
                    linesPerCheck = lineCount / numberOfChecksToMake
                    #Formula for the timer on how long to wait between checks.
                    newtimeToSleep = timeToSleep * ( targetLinesPerCheck / linesPerCheck )
                except:
                    print("the error is here smart boi")

                timeToSleep = newtimeToSleep
                if(numberOfChecksToMake < 100):
                    numberOfChecksToMake += 10
          
        except ValueError as message:
            print("Did not manage to connect to sensor properly, check your settings. Error was: {}".format(message))
        except serial.SerialException as message:
            print("Did not read data from sensor properly, check your settings. Error was: {}".format(message))

# gps = GPS2()

# while True:
#     gps.Reading()