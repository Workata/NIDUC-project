import numpy as np
import komm as komm

def generateMessage(messageLength, packetLength):           #wygenerwoanie wiadomosci i podzielenie jej na pakiety
    numberOfPackets = int(np.ceil(messageLength/packetLength))     #liczba pakietow zaokraglona w gore do liczby calkowitej
    data = np.arange(packetLength*numberOfPackets).reshape(numberOfPackets, packetLength)
    i = 0
    j = 0
    while  i < numberOfPackets:
        while j < packetLength:
            data[i][j] = np.random.randint(2)       #losowy int <0,2) czyli 0 lub 1
            j += 1
        i += 1
        j = 0
    return data


def binarySymmetricChannel(packet, probability):
    bsc = komm.BinarySymmetricChannel(probability)
    return bsc(packet)

def addParityBit(packet):   #wzgledem "1"
    counter = 0
    for x in packet:
        if x==1:
            counter+=1
    if counter%2 == 0:
        packet.append(0)
    else:
        packet.append(1)
    return packet

def generateCRCGolay():     #dlugosc pakietu ->12
    code = komm.CyclicCode(length=23, generator_polynomial=0b101011100011)  #code = komm.CyclicCode(length=14, generator_polynomial=0b111010101)
    return code


#--------------------------------------------TESTY----------------------------------------------------------------
packet = [0, 1, 1, 1, 0, 0, 1, 0, 1, 0, 0, 1]
#y = addParityBit(packet)
#x = binarySymmetricChannel(packet, 0.1)
#print(y)
#print(x)
code = generateCRCGolay()
coded = code.encode(packet)
decoded = code.decode(coded)
#print(coded)
#print(decoded)
data = generateMessage(20, 4)
print(data)
