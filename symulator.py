import numpy as np
import komm as komm

#-----------------------------METODY--DO--SYMULACJI-----------------------------------------------------------------

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
        packet = np.append(packet, [0])   #packet.append(0)    #
    else:
        packet = np.append(packet, [1])  #packet.append(1)        #
    return packet

def checkParityBit(packet):
    parityBit = packet[len(packet)-1]   # ostatni element pakietu to bit parzystosci
    print(parityBit)
    array = np.array(packet)
    counter = 0
    #print(array[0:(len(array)-1)])      #array[k:n] to indeksy: <k,n) "The result includes the start index, but excludes the end index."
    for x in array[0:(len(array)-1)]:   # slicing array
        if x == 1:
            counter += 1
    if counter % 2 == parityBit:
        #print("bez zmian")
        return 1  # true
    else:
        #print("zmiana")
        return 0  # false


# W dokumentacji length to jest dlugosc calej wiadomosci po zakodowaniu a dimension do dlugosc wiadomosci przed zakodowaniem (tresci)
def generateCRCGolay():     #dlugosc pakietu -> 12
    code = komm.CyclicCode(length=23, generator_polynomial=0b101011100011)  #code = komm.CyclicCode(length=14, generator_polynomial=0b111010101)
    return code

def generateCRCSimplex():   #dlugosc pakietu -> 3
    coder = komm.CyclicCode(length=7, generator_polynomial=0b10111)
    return coder

def generateCRCHamming():   #dlugosc pakietu -> 4, Hamming podobnie jak BCH jest FEC; Jak inne? Co z CRC16?
    coder = komm.CyclicCode(length=7, generator_polynomial=0b1011)
    return coder

def generateBCHCode(mi, tau):   # n = 2^(mi) - 1, 1<= tau <2^(mi-1), ; dlugosc pakietu (dimension) -> k>= n - mi*tau
    coder = komm.BCHCode(mi, tau)
    return coder

#---------------------------------------------------SYMULACJE-------------------------------------

def simulationBSCandParityBit(messageLength, packetLength, retransmissionMax):
    data = generateMessage(messageLength, packetLength)
    numberOfPackets = int(np.ceil(messageLength / packetLength))
    dataReceived = np.arange(packetLength*numberOfPackets).reshape(numberOfPackets, packetLength)    #
    i = 0
    for packet in data:
        retransmissionCounter = 0
        while retransmissionCounter < retransmissionMax:
            packetPB = addParityBit(packet)
            packetReceived = binarySymmetricChannel(packetPB, 0.1)
            if(checkParityBit(packetReceived)==0):
                retransmissionCounter+=1
            else:
                break
        packetReceived = np.delete(packetReceived,len(packetReceived)-1)    # obciac bit parzystosci
        dataReceived[i] = packetReceived
        i += 1
    return [data, dataReceived]


#--------------------------------------------TESTY----------------------------------------------------------------
packet = [0, 1, 1, 1, 0, 0, 1, 0, 1, 0, 0, 1]
packet2 = [0, 1, 0]
packet3 = [0, 1, 0, 1]
packet4 = [0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 1, 1, 0, 1]
#y = addParityBit(np.array(packet))
#x = binarySymmetricChannel(packet, 0.1)
#print(y)
#print(x)
#coder = generateCRCGolay()
#coder = generateCRCSimplex()
#coder = generateCRCHamming()
coder = generateBCHCode(5, 3)
coded = coder.encode(packet4)
decoded = coder.decode(coded)
#print(coded)
#print(decoded)
#y = addParityBit(packet)
#checkParityBit(y)
#data = generateMessage(20, 4)
#print(data)

experiment = simulationBSCandParityBit(20,4,2)
print(experiment[0])
print("\n")
print(experiment[1])
