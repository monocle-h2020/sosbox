
from SQL_queries import BB3_select
import requests
import xml.etree.ElementTree as et
from xml.dom import minidom


url = "http://192.171.164.62:32145/api/sos_proxy/23ff13fd38f561cd3fd81c405a3d1ef5/xml/submit"

def sendRequest( url, payload):

    result = None

    headers = {
        'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'application/xml' 
    }

    try:
        r = requests.post( url, payload, headers=headers )
        try:
            result = et.fromstring( r.text )
        except Exception as err:
            print( "Error decoding response: {}".format( err ))
            print( "Response was:\n{}".format( r.text ))
            return None
    except IOError as err:
        print ("error connecting to {}, error was {}".format( url, err))
        return None
    
    return result


data = BB3_select()

basexmlString = '''
<?xml version="1.0" encoding="UTF-8"?>
<sos:InsertResult service="SOS" version="2.0.0"
    xmlns:sos="http://www.opengis.net/sos/2.0"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.opengis.net/sos/2.0 http://schemas.opengis.net/sos/2.0/sos.xsd">
    <sos:template>http://monocle-h2020.eu/demo/1/procedure/demo/template/1</sos:template>
    <sos:resultValues>1@{}/{}#{}#{}#{}#{}#{}@</sos:resultValues>
</sos:InsertResult>
'''

newRow = []
for row in data:
    newRow.append(row[0]+"T"+row[1])
    newRow.append(row[0]+"T"+row[1])
    newRow.append(row[0]+"T"+row[1])
    newRow.append(row[2])
    newRow.append(row[3])
    newRow.append(row[4])
    newRow.append(row[5])
    xmlString=basexmlString.format(newRow[0],newRow[1],newRow[2],newRow[3],newRow[4],newRow[5],newRow[6])
    print(xmlString)
    response = (sendRequest(url,xmlString))
    xmlstr = minidom.parseString(
            et.tostring( response)).toprettyxml(
                indent="\t", #
                newl=""      # newlines are already sent by sos
            )
    print(xmlstr)
