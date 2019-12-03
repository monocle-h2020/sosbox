
import time
import re

def generateFletcherChecksum(byteArray):
    try:
        CK_A = 0
        CK_B = 0
        for I in byteArray:
            CK_A = CK_A + I
            CK_A &= 0xFF 
            CK_B = CK_B + CK_A    
            CK_B &= 0xFF
    except:
        pass
        #print(byteArray)
    return (CK_A, CK_B) 


f = open("/local1/data/scratch/jkb/UBX3.txt", "r")
data = f.read()
f.close()

lineData = data.split("b562")
for lineIndex in range(len(lineData)-1):
    byteArray = str(lineData[lineIndex])    
    byteArray = re.findall('..', byteArray)
    base16Data = [int(x, 16) for x in byteArray]
    lineData[lineIndex] = bytearray(base16Data)


UBX_NAV_RELPOSNED = 0
UBX_NAV_PVT = 0
unknown = []

for line in lineData:
    if(len(line) > 5):
        #print(list(line))
        
        checkSumA, checkSumB = generateFletcherChecksum(line[:-2])

        # print(line[0],line[1])
        # time.sleep(0.5)
        if(checkSumA == line[-2] and checkSumB == line[-1]):
            if(line[0] == 1 and line[1] == 60):
                UBX_NAV_RELPOSNED += 1
            elif(line[0] == 1 and line[1] == 7):
                UBX_NAV_PVT += 1
            else:
                unknown.append(line)

print(unknown)           
print("UBX_NAV_RELPOSNED {}".format(UBX_NAV_RELPOSNED))
print("UBX_NAV_PVT {}".format(UBX_NAV_PVT))