#! /usr/bin/env python3
"""
Program to read in data from the BB3 wetlabs sensor.
"""

try:
    import serialReader
except ImportError as message:
    print("Failed to import serialReaderial, maybe it is not installed correctly? Error was: {}".format(message))

try:
    import datetime
except ImportError as message:
    print("Failed to import datetime, maybe it is not installed correctly? Error was: {}".format(message))

try:
    import time
except ImportError as message:
    print("Failed to import time, maybe it is not installed correctly? Error was: {}".format(message))

try:
    from dummy_sensors import DummyEXAMPLESensor
except ImportError as message:
    print("Failed to import DummyBB3Sensor from dummy_sensors, check your files. Error was: {}".format(message))


class ExampleSensor:
    """ 
    The EXAMPLE sensor class to read in data live while in-situ.

    Reads in a line of data, then after checking a certain number of times to see if there is data, adjust a waiting timer.

    The waiting timer is adjusted to avoid unnecessary CPU usage on the Raspberry Pi.
    """

    def Reading(self):
        """
        Generator function to read in data from the sensor.
        
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

        try:
            #serialReader = serialReaderial.serialReaderial(self.USB_PORT,self.baudRate,timeout=self.timeoutLength)
            serialReader = DummyEXAMPLESensor()

            while True:  

                lineCount = 0          
                # The number of checks to make 
                for i in range(numberOfChecksToMake):
                    time.sleep(timeToSleep)
                    
                    # This if statement is specific for this sensor, everything else here can be used with other sensors.
                    if serialReader.in_waiting != 0:
                        bitOfData = serialReader.read(serialReader.in_waiting)
                        lineOfData = lineOfData + bitOfData
                        bitOfData = ""
                        
                        # Checking if there is a carrage return and new line in the line, as that is used to signal the end of a reading.
                        if(b"\r\n" in lineOfData):                                 
                            #break up by /r/n              
                            stringLine = lineOfData.decode('utf-8')
                            listOfLines = stringLine.split("\r\n")
                            
                            # If there is more than one item in the list, it may not be full so store the last bitOfData and add it on to the next reading
                            if(len(listOfLines) > 1):
                                listOfLines[0] = leftoverData + listOfLines[0]
                                leftoverData = listOfLines[-1]                  
                                del listOfLines[-1]
                            
                            # If there is something in the list yield the line back to sensor manager
                            if(len(listOfLines) > 0):
                                for singleLine in listOfLines:
                                    lineCount += 1
                                    stringLine = singleLine.split()
                                    yield (stringLine)
                                lineOfData = b"" 
                        else:
                            pass
                
                linesPerCheck = lineCount / numberOfChecksToMake           
                print( "Time of {}s gave us {} lines per check".format(timeToSleep, linesPerCheck ))
                #Formula for new timer.
                newtimeToSleep = timeToSleep * ( targetLinesPerCheck / linesPerCheck )

                # Increment number of checks to make.
                timeToSleep = newtimeToSleep
                if(numberOfChecksToMake < 100):
                    numberOfChecksToMake += 10
        
        except ValueError as message:
            print("Did not manage to connect to sensor properly, check your settings. Error was: {}".format(message))
        except serialReaderial.serialReaderialException as message:
            print("Did not read data from sensor properly, check your settings. Error was: {}".format(message))