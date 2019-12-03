import datetime
import random     
#import functools
from functools import reduce
import time
import math

class DummySensor:

    """
    base class for all dummy sensors, contains the data types for possible config values
    """

    TYPE_FUNC     = 0
    TYPE_CONST    = 1
    TYPE_DATETIME = 2
    TYPE_RAND_UNIFORM = 3

    ENCODING_STRING = 'UTF-8'
    
    valid_types = [ 
        TYPE_FUNC,
        TYPE_CONST,
        TYPE_DATETIME,
        TYPE_RAND_UNIFORM
        ]

   
    def createElementFromConfig( self, elem, prev ):
        """
        utility function to turn a specificied return value's config into a string
        
        uses a dictionary of functions for the conversion
        """
        lookup = {
            DummySensor.TYPE_FUNC: lambda x,y: x['value'](y),
            DummySensor.TYPE_CONST: lambda x,_: x['value'],
            DummySensor.TYPE_DATETIME: lambda x,_: x['value']().strftime( x['format'] ),
            DummySensor.TYPE_RAND_UNIFORM: lambda x,_: random.randint( x['min'], x['max'] )
        }
        if elem['type'] not in lookup:
            raise Exception( "Out of bounds effor for element type"+ str( elem['type'] ) )
        else:
            return str(lookup[elem['type']](elem,prev))

    @staticmethod
    def _pairwise( xs ):
        """
        utility function to turn a list into a list of pairs
        where [ x1, x2, x3, x4, ... ]
        becomes [ (x1, x2), (x3, x4), ... ]

        Note: requires even number of elements in xs
        """
        it = iter( xs )
        return zip( it, it )

    @staticmethod
    def _bytesToBytePairs( xs ):
        pairs = DummySensor._pairwise( xs )
        return pairs
  
class DummyByteSensor( DummySensor ):
    """
    parent class for all simple byte based output sensors

    contains methods for simulating the behaviour of real sensors

    exact sensor definitions should go in the child class

    child classes are required to provide the following properties

    delim: token used between individual values
    eol:   token used to mark the end of a line
    data:  a list of dictionaries that describe the values and how to fudge them
    """

    # optimal value for polling sensors in seconds
    line_generation_time = 1.5

    # object storage for current readings to allow accurate reporting of availble bytes in in_waiting

    def __init__(self):
        self.last_read = None
        self.currentOutput = []
        self.firstLineOffset = 0
        self.last_read = time.time()
    
    def _genLine(self):
        """ 
        internal method to generate a line based on our lovely data definitions
        """
        listElements = []
        for elem in self.data:
            listElements.append(self.createElementFromConfig( elem, listElements ))

        returnString = self.delim.join( listElements ) + self.eol

        # store last read time for more life like simulation
        return bytes( returnString, DummySensor.ENCODING_STRING )

    def _getUnreadLineCount(self):
        return (time.time() - self.last_read) / self.line_generation_time
            
    def _createOutput(self):
        """
        internal method to generate a chunk of output
        """
        linesWeShouldHave = self._getUnreadLineCount()
        linesWeAreShort   = math.ceil(linesWeShouldHave - len( self.currentOutput ))
        for i in range( linesWeAreShort ):
            self.currentOutput.append( self._genLine() )
            
        return( linesWeAreShort )
        
    def __getattr__(self, name):
        if name == 'in_waiting':
            return self._getInWaiting()
        elif hasattr(super(), "__getattr__"):
            # if the parent has one, that might know what this is about
            return super().__getattr__(attr)
        # nope, no idea, explode
        raise AttributeError(str(name) + " is not a property of " + self.__class__.__name__)

    def _getInWaiting(self):
        """ 
        internal method to calculate the available bytes
        """
        lines = self._getUnreadLineCount()
        self._createOutput()
        waitingCount = 0 
        for n in range(0, (math.ceil( lines ) - 1)):
            waitingCount += len( self.currentOutput[n] )
        if lines >= 1:
            lastLine = math.ceil(lines) - 1
        else:
            lastLine = 0
        # get the number of charactes that represent the left over fraction of this line
        waitingCount += math.floor( len(self.currentOutput[lastLine]) * (lines - math.floor(lines)))
        return waitingCount
        
    def read( self, num_bytes ):
        """
        here we generate our byte string based on how much data was requested
        """
        orig_num_bytes = num_bytes
        outputBytes = b""
        self._createOutput() # might not be necessary if the consumer is well behaved?
        newOffset = 0
        currentOffset = self.firstLineOffset
        if currentOffset > 0:
            thisLine = self.currentOutput[0]
            if ( num_bytes + currentOffset ) < len( thisLine ):
                outputBytes = thisLine[(currentOffset):(num_bytes+currentOffset)]
                newOffset = currentOffset + num_bytes
                num_bytes = 0
            else:
                outputBytes += thisLine[(currentOffset):]
                self.currentOutput.pop(0)
                num_bytes = num_bytes - len( outputBytes )
                
        while( num_bytes > 0 ):
            if len( self.currentOutput ) < 1:
                self._createOutput()

            thisLine = self.currentOutput[0]
            if len( thisLine ) <= num_bytes:
                # reading full line, update the particulars then remove
                outputBytes += thisLine
                num_bytes -= len(thisLine)
                self.currentOutput.pop(0)
            else:
                # partial line
                outputBytes += thisLine[:num_bytes]
                newOffset = num_bytes 
                break
        self.firstLineOffset = newOffset
        self.last_read = time.time()
        
        # Remove a trailing comma for multi-line outputs.
        outputBytes = outputBytes.decode('utf-8')
        outputBytes = outputBytes.replace(",\n\r","\n\r")
        outputBytes = outputBytes.encode('utf-8')

        return outputBytes


class DummyBB3Sensor( DummyByteSensor ):
    """
    Dummy sensor class for pretenting to be a WetLabs BB3 sensor
    """

    delim = '\t'
    eol   = '\r\n'
    data  = [
        {
            'name': 'date',
            'type': DummySensor.TYPE_DATETIME,
            'format': "%m/%d/%y",
            'value': datetime.datetime.now
        },
        {
            'name': 'time',
            'type': DummySensor.TYPE_DATETIME,
            'format': "%H:%M:%S",
            'value': datetime.datetime.now
        },
        {
            'name': 'blue',
            'type': DummySensor.TYPE_CONST,
            'value': 470
        },
        {
            'name': 'blue val',
            'type': DummySensor.TYPE_RAND_UNIFORM,
            'max': 4130,
            'min': 0
        },
        {
            'name': 'green',
            'type': DummySensor.TYPE_CONST,
            'value': 532
        },
        {
            'name': 'green val',
            'type': DummySensor.TYPE_RAND_UNIFORM,
            'max': 4130,
            'min': 0
        },
        {
            'name': 'red',
            'type': DummySensor.TYPE_CONST,
            'value': 700
        },
        {
            'name': 'red val',
            'type': DummySensor.TYPE_RAND_UNIFORM,
            'max': 4130,
            'min': 0
        },
        {
            'name': 'temp',
            'type': DummySensor.TYPE_RAND_UNIFORM,
            'max': 540,
            'min': 500
        }
    ]


class DummyGPS (DummyByteSensor):
    """
    Dummy sensor class for pretending to be a GPS.
    """

   

    @staticmethod
    def LatitudeMover(self):
        self.Latitude -= 0.004
        return self.Latitude


    @staticmethod
    def LongitudeMover(self):
        self.Longitude += 0.006
        return self.Longitude

    delim = ','
    eol = '\r\n'
    
    def __init__(self):

        super().__init__()
        
        self.Latitude = 50180
        self.Longitude = 4090
        
        self.data = [

            {
                'name': 'GPRMC',
                'type': DummySensor.TYPE_CONST,
                'value': '$GPRMC'
            },
            {
                'name': 'time',
                'type': DummySensor.TYPE_CONST,
                'value': '133408.00'
            },
            {
                'name': 'Navigation receiver warning',
                'type': DummySensor.TYPE_CONST,
                'value': 'A'
            },
            {
                'name': 'Latitude',
                'type': DummySensor.TYPE_FUNC,
                'value': lambda _: DummyGPS.LatitudeMover(self)
                #'value': '5021.96960'
            },
            {
                'name': 'LatitudeDirection',
                'type': DummySensor.TYPE_CONST,
                'value': 'N'
            },
            {
                'name': 'Longitude',
                'type': DummySensor.TYPE_FUNC,
                'value': lambda _: DummyGPS.LongitudeMover(self)
                #'value': '00408.86047'
            },
            {
                'name': 'LongitudeDirection',
                'type': DummySensor.TYPE_CONST,
                'value': 'W'
            },
            {
                'name': 'Speed',
                'type': DummySensor.TYPE_CONST,
                'value': ''
            },
            {
                'name': 'True course',
                'type': DummySensor.TYPE_CONST,
                'value': 231
            },
            {
                'name': 'date',
                'type': DummySensor.TYPE_CONST,
                'value': '260919'
            },
            {
                'name': 'temp',
                'type': DummySensor.TYPE_CONST,
                'value': ''
            },
            {
                'name': 'Magneticvariation',
                'type': DummySensor.TYPE_CONST,
                'value': ''
            },
            {
                'name': 'GPRMCchecksum',
                'type': DummySensor.TYPE_CONST,
                'value': 'A*6C'
            },
            # {
            #     'name': 'GPRMCLineBreak',
            #     'type': DummySensor.TYPE_CONST,
            #     'value': '\n\r'
            # },
            {
                'name': 'GPVTG',
                'type': DummySensor.TYPE_CONST,
                'value': '\n\r$GPVTG'
            },
            {
                'name': 'TrueTrackMadeGood',
                'type': DummySensor.TYPE_CONST,
                'value': ''
            },
            {
                'name': 'TrueTrackMadeGoodTrue',
                'type': DummySensor.TYPE_CONST,
                'value': 'T'
            },
            {
                'name': 'MagneticTrackMadeGood',
                'type': DummySensor.TYPE_CONST,
                'value': ''
            },
            {
                'name': 'MTMadeGood',
                'type': DummySensor.TYPE_CONST,
                'value': 'M'
            },
            {
                'name': 'GroundSpeedKnots',
                'type': DummySensor.TYPE_CONST,
                'value': '0.247'
            },
            {
                'name': 'knots',
                'type': DummySensor.TYPE_CONST,
                'value': 'N'
            },
            {
                'name': 'SppedKMPH',
                'type': DummySensor.TYPE_CONST,
                'value': '0.457'
            },
            {
                'name': 'KilometersPerHour',
                'type': DummySensor.TYPE_CONST,
                'value': 'K'
            },
            {
                'name': 'GPVTGchecksum',
                'type': DummySensor.TYPE_CONST,
                'value': 'A*24'
            },
            # {
            #     'name': 'GPVTGLineBreak',
            #     'type': DummySensor.TYPE_CONST,
            #     'value': '\n\r'
            # },
            {
                'name': 'GPGGA',
                'type': DummySensor.TYPE_CONST,
                'value': '\n\r$GPGGA'
            },
            {
                'name': 'currentTime',
                'type': DummySensor.TYPE_CONST,
                'value': '133408.00'
            },
            {
                'name': 'GPGGALatitude',
                'type': DummySensor.TYPE_CONST,
                'value': '5021.96960'
            },
            {
                'name': 'GPGGALatitudeDirection',
                'type': DummySensor.TYPE_CONST,
                'value': 'N'
            },
            {
                'name': 'GPGGALongitude',
                'type': DummySensor.TYPE_CONST,
                'value': '00408.86047'
            },
            {
                'name': 'GPGGALongitudeDirection',
                'type': DummySensor.TYPE_CONST,
                'value': 'W'
            },
            {
                'name': 'FixQuality',
                'type': DummySensor.TYPE_CONST,
                'value': 1
            },
            {
                'name': 'NumberOfSatelites',
                'type': DummySensor.TYPE_CONST,
                'value': '08'
            },
            {
                'name': 'HDOP',
                'type': DummySensor.TYPE_CONST,
                'value': 2.11
            },
            {
                'name': 'Altitude',
                'type': DummySensor.TYPE_CONST,
                'value': 29.8
            },
            {
                'name': 'AltitudeMeters',
                'type': DummySensor.TYPE_CONST,
                'value': 'M'
            },
            {
                'name': 'HeightAboveEllipsoid',
                'type': DummySensor.TYPE_CONST,
                'value': '50.4'
            },
            {
                'name': 'Meters',
                'type': DummySensor.TYPE_CONST,
                'value': 'M'
            },
            {
                'name': 'DGPsReferenceStationID',
                'type': DummySensor.TYPE_CONST,
                'value': ''
            },
            {
                'name': 'GPGGAchecksum',
                'type': DummySensor.TYPE_CONST,
                'value': '*7C'
            },
            # {
            #     'name': 'GPGGALineBreak',
            #     'type': DummySensor.TYPE_CONST,
            #     'value': '\n\r'
            # },
            {
                'name': 'GPGSA',
                'type': DummySensor.TYPE_CONST,
                'value': '\n\r$GPGSA'
            },
            {
                'name': 'ModeOne',
                'type': DummySensor.TYPE_CONST,
                'value': 'A'
            },
            {
                'name': 'ModeTwo',
                'type': DummySensor.TYPE_CONST,
                'value': '3'
            },
            {
                'name': 'SVIDOne',
                'type': DummySensor.TYPE_CONST,
                'value': '01'
            },
            {
                'name': 'SVIDTwo',
                'type': DummySensor.TYPE_CONST,
                'value': '31'
            },
            {
                'name': 'SVIDThree',
                'type': DummySensor.TYPE_CONST,
                'value': '22'
            },
            {
                'name': 'SVIDFour',
                'type': DummySensor.TYPE_CONST,
                'value': '17'
            },
            {
                'name': 'SVIDFive',
                'type': DummySensor.TYPE_CONST,
                'value': '03'
            },
            {
                'name': 'SVIDSix',
                'type': DummySensor.TYPE_CONST,
                'value': '12'
            },
            {
                'name': 'SVIDSeven',
                'type': DummySensor.TYPE_CONST,
                'value': '06'
            },
            {
                'name': 'SVIDEight',
                'type': DummySensor.TYPE_CONST,
                'value': '19'
            },
            {
                'name': 'SVIDNine',
                'type': DummySensor.TYPE_CONST,
                'value': ''
            },
            {
                'name': 'SVIDTen',
                'type': DummySensor.TYPE_CONST,
                'value': ''
            },
            {
                'name': 'SVIDEleven',
                'type': DummySensor.TYPE_CONST,
                'value': ''
            },
            {
                'name': 'SVIDTwelve',
                'type': DummySensor.TYPE_CONST,
                'value': ''
            },
            {
                'name': 'PD0P',
                'type': DummySensor.TYPE_CONST,
                'value': '3.53'
            },
            {
                'name': 'HD0P',
                'type': DummySensor.TYPE_CONST,
                'value': '2.11'
            },
            {
                'name': 'VD0P',
                'type': DummySensor.TYPE_CONST,
                'value': '2.83'
            },
            {
                'name': 'GPGSAchecksum',
                'type': DummySensor.TYPE_CONST,
                'value': '*07'
            },
            {
                'name': 'GPGSV1',
                'type': DummySensor.TYPE_CONST,
                'value': '\n\r$GPGSV'
            },
            {
                'name': 'NumberOfMessages',
                'type': DummySensor.TYPE_CONST,
                'value': '4'
            },
            {
                'name': 'MessageNumber',
                'type': DummySensor.TYPE_CONST,
                'value': '1'
            },
            {
                'name': 'TotalNumberOfSVsInView',
                'type': DummySensor.TYPE_CONST,
                'value': '14'
            },
            {
                'name': 'SVPRNNumber',
                'type': DummySensor.TYPE_CONST,
                'value': '01'
            },
            {
                'name': 'ElevationInDegrees',
                'type': DummySensor.TYPE_CONST,
                'value': '28'
            },
            {
                'name': 'AzimuthDegreesFromTrueNorth',
                'type': DummySensor.TYPE_CONST,
                'value': '130'
            },
            {
                'name': 'SNR',
                'type': DummySensor.TYPE_CONST,
                'value': '22'
            },
            {
                'name': 'InfoAboutSecondSV01',
                'type': DummySensor.TYPE_CONST,
                'value': '03'
            },
            {
                'name': 'InfoAboutSecondSV02',
                'type': DummySensor.TYPE_CONST,
                'value': '63'
            },
            {
                'name': 'InfoAboutSecondSV03',
                'type': DummySensor.TYPE_CONST,
                'value': '068'
            },
            {
                'name': 'InfoAboutSecondSV04',
                'type': DummySensor.TYPE_CONST,
                'value': '43'
            },
            {
                'name': 'InfoAboutThirdSV01',
                'type': DummySensor.TYPE_CONST,
                'value': '06'
            },
            {
                'name': 'InfoAboutThirdSV02',
                'type': DummySensor.TYPE_CONST,
                'value': '38'
            },
            {
                'name': 'InfoAboutThirdSV03',
                'type': DummySensor.TYPE_CONST,
                'value': '303'
            },
            {
                'name': 'InfoAboutThirdSV04',
                'type': DummySensor.TYPE_CONST,
                'value': '39'
            },
            {
                'name': 'InfoAboutForthSV01',
                'type': DummySensor.TYPE_CONST,
                'value': '09'
            },
            {
                'name': 'InfoAboutForthSV02',
                'type': DummySensor.TYPE_CONST,
                'value': '09'
            },
            {
                'name': 'InfoAboutForthSV03',
                'type': DummySensor.TYPE_CONST,
                'value': '36'
            },
            {
                'name': 'InfoAboutForthSV04',
                'type': DummySensor.TYPE_CONST,
                'value': '197'
            },
            {
                'name': 'GPGSV1checksum',
                'type': DummySensor.TYPE_CONST,
                'value': '*7B'
            },
            {
                'name': 'GPGSV2',
                'type': DummySensor.TYPE_CONST,
                'value': '\n\r$GPGSV'
            },
            {
                'name': 'NumberOfMessages2',
                'type': DummySensor.TYPE_CONST,
                'value': '4'
            },
            {
                'name': 'MessageNumber2',
                'type': DummySensor.TYPE_CONST,
                'value': '2'
            },
            {
                'name': 'TotalNumberOfSVsInView2',
                'type': DummySensor.TYPE_CONST,
                'value': '14'
            },
            {
                'name': 'SVPRNNumber2',
                'type': DummySensor.TYPE_CONST,
                'value': '11'
            },
            {
                'name': 'ElevationInDegrees2',
                'type': DummySensor.TYPE_CONST,
                'value': '12'
            },
            {
                'name': 'AzimuthDegreesFromTrueNorth2',
                'type': DummySensor.TYPE_CONST,
                'value': '153'
            },
            {
                'name': 'SNR2',
                'type': DummySensor.TYPE_CONST,
                'value': '14'
            },
            {
                'name': 'InfoAboutSecondSV012',
                'type': DummySensor.TYPE_CONST,
                'value': '12'
            },
            {
                'name': 'InfoAboutSecondSV022',
                'type': DummySensor.TYPE_CONST,
                'value': '07'
            },
            {
                'name': 'InfoAboutSecondSV032',
                'type': DummySensor.TYPE_CONST,
                'value': '327'
            },
            {
                'name': 'InfoAboutSecondSV042',
                'type': DummySensor.TYPE_CONST,
                'value': '31'
            },
            {
                'name': 'InfoAboutThirdSV012',
                'type': DummySensor.TYPE_CONST,
                'value': '14'
            },
            {
                'name': 'InfoAboutThirdSV022',
                'type': DummySensor.TYPE_CONST,
                'value': '03'
            },
            {
                'name': 'InfoAboutThirdSV032',
                'type': DummySensor.TYPE_CONST,
                'value': '038'
            },
            {
                'name': 'InfoAboutThirdSV042',
                'type': DummySensor.TYPE_CONST,
                'value': ''
            },
            {
                'name': 'InfoAboutForthSV012',
                'type': DummySensor.TYPE_CONST,
                'value': '17'
            },
            {
                'name': 'InfoAboutForthSV022',
                'type': DummySensor.TYPE_CONST,
                'value': '46'
            },
            {
                'name': 'InfoAboutForthSV032',
                'type': DummySensor.TYPE_CONST,
                'value': '244'
            },
            {
                'name': 'InfoAboutForthSV042',
                'type': DummySensor.TYPE_CONST,
                'value': '13'
            },
            {
                'name': 'GPGSV1checksum2',
                'type': DummySensor.TYPE_CONST,
                'value': '*72'
            },
            ##########################
            {
                'name': 'GPGSV3',
                'type': DummySensor.TYPE_CONST,
                'value': '\n\r$GPGSV'
            },
            {
                'name': 'NumberOfMessages3',
                'type': DummySensor.TYPE_CONST,
                'value': '4'
            },
            {
                'name': 'MessageNumber3',
                'type': DummySensor.TYPE_CONST,
                'value': '3'
            },
            {
                'name': 'TotalNumberOfSVsInView3',
                'type': DummySensor.TYPE_CONST,
                'value': '14'
            },
            {
                'name': 'SVPRNNumber3',
                'type': DummySensor.TYPE_CONST,
                'value': '18'
            },
            {
                'name': 'ElevationInDegrees3',
                'type': DummySensor.TYPE_CONST,
                'value': '04'
            },
            {
                'name': 'AzimuthDegreesFromTrueNorth3',
                'type': DummySensor.TYPE_CONST,
                'value': '131'
            },
            {
                'name': 'SNR3',
                'type': DummySensor.TYPE_CONST,
                'value': '12'
            },
            {
                'name': 'InfoAboutSecondSV013',
                'type': DummySensor.TYPE_CONST,
                'value': '19'
            },
            {
                'name': 'InfoAboutSecondSV023',
                'type': DummySensor.TYPE_CONST,
                'value': '48'
            },
            {
                'name': 'InfoAboutSecondSV033',
                'type': DummySensor.TYPE_CONST,
                'value': '270'
            },
            {
                'name': 'InfoAboutSecondSV043',
                'type': DummySensor.TYPE_CONST,
                'value': '38'
            },
            {
                'name': 'InfoAboutThirdSV013',
                'type': DummySensor.TYPE_CONST,
                'value': '22'
            },
            {
                'name': 'InfoAboutThirdSV023',
                'type': DummySensor.TYPE_CONST,
                'value': '42'
            },
            {
                'name': 'InfoAboutThirdSV033',
                'type': DummySensor.TYPE_CONST,
                'value': '080'
            },
            {
                'name': 'InfoAboutThirdSV043',
                'type': DummySensor.TYPE_CONST,
                'value': '39'
            },
            {
                'name': 'InfoAboutForthSV013',
                'type': DummySensor.TYPE_CONST,
                'value': '23'
            },
            {
                'name': 'InfoAboutForthSV023',
                'type': DummySensor.TYPE_CONST,
                'value': '65'
            },
            {
                'name': 'InfoAboutForthSV033',
                'type': DummySensor.TYPE_CONST,
                'value': '157'
            },     
            {
                'name': 'GPGSV1checksum3',
                'type': DummySensor.TYPE_CONST,
                'value': '*79'
            },
            ##############################
            {
                'name': 'GPGSV4',
                'type': DummySensor.TYPE_CONST,
                'value': '\n\r$GPGSV'
            },
            {
                'name': 'NumberOfMessages4',
                'type': DummySensor.TYPE_CONST,
                'value': '4'
            },
            {
                'name': 'MessageNumber4',
                'type': DummySensor.TYPE_CONST,
                'value': '4'
            },
            {
                'name': 'TotalNumberOfSVsInView4',
                'type': DummySensor.TYPE_CONST,
                'value': '14'
            },
            {
                'name': 'SVPRNNumber4',
                'type': DummySensor.TYPE_CONST,
                'value': '25'
            },
            {
                'name': 'ElevationInDegrees4',
                'type': DummySensor.TYPE_CONST,
                'value': '00'
            },
            {
                'name': 'AzimuthDegreesFromTrueNorth4',
                'type': DummySensor.TYPE_CONST,
                'value': '004'
            },
            {
                'name': 'SNR4',
                'type': DummySensor.TYPE_CONST,
                'value': ''
            },
            {
                'name': 'InfoAboutSecondSV014',
                'type': DummySensor.TYPE_CONST,
                'value': '31'
            },
            {
                'name': 'InfoAboutSecondSV024',
                'type': DummySensor.TYPE_CONST,
                'value': '16'
            },
            {
                'name': 'InfoAboutSecondSV034',
                'type': DummySensor.TYPE_CONST,
                'value': '044'
            },
            {
                'name': 'InfoAboutSecondSV044',
                'type': DummySensor.TYPE_CONST,
                'value': '32'
            }, 
            {
                'name': 'GPGSV1checksum4',
                'type': DummySensor.TYPE_CONST,
                'value': '*7B'
            },
            {
                'name': 'GPGLL',
                'type': DummySensor.TYPE_CONST,
                'value': '\n\r$GPGLL'
            }, 
            {
                'name': 'GPGLLLatitude',
                'type': DummySensor.TYPE_CONST,
                'value': '5021.96960'
            }, 
            {
                'name': 'GPGLLLatitudeDirection',
                'type': DummySensor.TYPE_CONST,
                'value': 'N'
            }, 
            {
                'name': 'GPGLLLongitude',
                'type': DummySensor.TYPE_CONST,
                'value': '00408.86047'
            }, 
            {
                'name': 'GPGLLLongitudeDirection',
                'type': DummySensor.TYPE_CONST,
                'value': 'W'
            }, 
            {
                'name': 'FixTaken',
                'type': DummySensor.TYPE_CONST,
                'value': '133408.00'
            }, 
            {
                'name': 'DataValid',
                'type': DummySensor.TYPE_CONST,
                'value': 'A'
            }, 
            {
                'name': 'ChecksumGPGLL',
                'type': DummySensor.TYPE_CONST,
                'value': 'A*71\n\r'
            }, 
    ]



    


    def checksumString(self, elems):
        pass


class DummyBB9Sensor( DummyByteSensor ):
    """
    Dummy sensor class for pretenting to be a WetLabs BB3 sensor
    """
    SERIAL_NUMBER = 1
    delim = '\t'
    eol   = '\r\n'
    
    @staticmethod
    def recordCounter(self):
        self.recordCount += 1
        return self.recordCount

    def checksumString(self, elems):
        #print( elems )
        #return 13
        # getString representation of the line leading up to this point
        line = reduce(lambda x,y: str(x) + self.delim + str(y), elems, "" )
        # now reduce wasn't a perfect choice due to our inital value
        # so we still need to move the \t from the begining to the end
        #line = line[1:] + "\t" ## actually we don't as addition is commuatble
        stringList = list( line )
        byteList   = list( map( ord, stringList ))
        hexList = list(map( lambda x: hex(x), byteList ))
        checkSum = reduce(lambda x,y: x + y, byteList, 0)
        hexSum = "{:x}".format(checkSum)
        return hexSum

    def __init__(self):

        # firstly we autogen our serial number
        # guaranteed to be (not thread safe) unique
        headerValue = DummyBB9Sensor.SERIAL_NUMBER
        # increment the serial for the next BB9
        DummyBB9Sensor.SERIAL_NUMBER += 1
        strHeaderValue = str(headerValue)
        strHeaderValue = strHeaderValue.zfill(4)
        header = "WETA_BB9" + strHeaderValue

        self.recordCount = 0 # this sensor numbers it's output lines

        self.data  = [
            {
                'name': 'header',
                'type': DummySensor.TYPE_CONST,
                'value': header
            },
            {
                'name': 'number of columns',
                'type': DummySensor.TYPE_CONST,
                'value': 21
            },
            {
                'name': 'packet version',
                'type': DummySensor.TYPE_CONST,
                'value': 1
            },
            {
                'name': 'record counter',
                'type': DummySensor.TYPE_FUNC,
                'value': lambda _: DummyBB9Sensor.recordCounter(self)
            }
        ]
        # measurement section
        # using code because it'd be tedious to write these out by hand
        wavelengths = [412,440,488,510,532,555,650,676,715]
        for w in wavelengths:
            self.data.extend(
                [
                    {
                        'name': str(w) + "nm wavelength",
                        'type': DummySensor.TYPE_CONST,
                        'value': w
                    },
                    {
                        'name': str(w) + "nm signal",
                        'type': DummySensor.TYPE_RAND_UNIFORM,
                        'max': 4120, # sensor max
                        'min': 0
                    }
                ]
            )

        # add checksum!
        self.data.append(
            {
                'name': "checksum",
                'type': DummySensor.TYPE_FUNC,
                'value': lambda x: DummyBB9Sensor.checksumString(self,x)
            }
        )
        super().__init__()
            
class DummyBBSensor( DummyByteSensor ):
    """
    Dummy sensor class for pretenting to be a WetLabs BB sensor
    """
    delim = '\t'
    eol   = '\r\n'
    data  = [
        {
            'name': 'date',
            'type': DummySensor.TYPE_DATETIME,
            'format': "%m/%d/%y",
            'value': datetime.datetime.now
        },
        {
            'name': 'time',
            'type': DummySensor.TYPE_DATETIME,
            'format': "%H:%M:%S",
            'value': datetime.datetime.now
        },
        {
            'name': 'scattering reference',
            'type': DummySensor.TYPE_RAND_UNIFORM,
            'max': 1800,
            'min': 0
        },
        {
            'name': 'scattering signal',
            'type': DummySensor.TYPE_RAND_UNIFORM,
            'max': 1300,
            'min': 0
        },
        {
            'name': 'Thermistor',
            'type': DummySensor.TYPE_RAND_UNIFORM,
            'max': 600,
            'min': 500
        }
    ]

          
class DummyNTUSensor( DummyByteSensor ):
    """
    Dummy sensor class for pretenting to be a WetLabs NTU sensor
    """
    delim = '\t'
    eol   = '\r\n'
    data  = [
        {
            'name': 'date',
            'type': DummySensor.TYPE_DATETIME,
            'format': "%m/%d/%y",
            'value': datetime.datetime.now
        },
        {
            'name': 'time',
            'type': DummySensor.TYPE_DATETIME,
            'format': "%H:%M:%S",
            'value': datetime.datetime.now
        },
        {
            'name': 'lambda',
            'type': DummySensor.TYPE_CONST,
            'value': 700
        },
        {
            'name': 'NTU signal',
            'type': DummySensor.TYPE_RAND_UNIFORM,
            'max': 100,
            'min': 50
        },
        {
            'name': 'N/U',
            'type': DummySensor.TYPE_CONST,
            'value': 700
        },
        {
            'name': 'Thermistor',
            'type': DummySensor.TYPE_RAND_UNIFORM,
            'max': 600,
            'min': 500
        }
    ]

class DummyEXAMPLESensor( DummyByteSensor ):
    """
    Dummy sensor class for pretenting to be a WetLabs BB3 sensor
    """
    delim = '\t'
    eol   = '\r\n'
    data  = [
        {
            'name': 'date',
            'type': DummySensor.TYPE_DATETIME,
            'format': "%m/%d/%y",
            'value': datetime.datetime.now
        },
        {
            'name': 'time',
            'type': DummySensor.TYPE_DATETIME,
            'format': "%H:%M:%S",
            'value': datetime.datetime.now
        },
        {
            'name': 'Constant Value',
            'type': DummySensor.TYPE_CONST,
            'value': 470
        },
        {
            'name': 'Random Value',
            'type': DummySensor.TYPE_RAND_UNIFORM,
            'max': 4130,
            'min': 0
        }
    ]