import numpy as np
import komm as komm
import time

#-----------------------------METODY--DO--SYMULACJI-----------------------------------------------------------------

def generateMessage(messageLength, packetLength):           #wygenerwoanie wiadomosci i podzielenie jej na pakiety
    numberOfPackets = int(np.ceil(messageLength/packetLength))     #liczba pakietow zaokraglona w gore do liczby calkowitej
    data = np.arange(packetLength*numberOfPackets).reshape(numberOfPackets, packetLength)
    i = 0
    j = 0
    while i < numberOfPackets:
        while j < packetLength:
            data[i][j] = np.random.randint(2)       #losowy int <0,2) czyli 0 lub 1
            j += 1
        i += 1
        j = 0
    return data


def binarySymmetricChannel(packet, probability):        # bledy pojedyncze -> Model BSC
    bsc = komm.BinarySymmetricChannel(probability)
    return bsc(packet)

def burstErrorChannel(packet, probability, lenOfSubsequence):     #bledy grupowe -> Model Gilberta
    packetLen = len(packet)
    i = 0
    while i < packetLen:
        toss = np.random.randint(100)   # losowy int <0,99>
        if(toss >= probability*100):
            i += 1
            continue
        else:
            j = 0
            while j < lenOfSubsequence:
                if(packet[i+j] == 1): packet[i+j] = 0   # negacja bitow w podciagu
                else: packet[i+j] = 1
                j += 1
                if ((j + i) == packetLen): return packet  # wykroczylismy poza pakiet
            i += j  # roznica + przejscie do kolejnego bitu
    return packet

def addParityBit(packet):   #wzgledem "1"
    counter = 0
    for x in packet:
        if x==1:
            counter+=1
    if counter%2 == 0:
        packet = np.append(packet, [0])
    else:
        packet = np.append(packet, [1])
    return packet

def checkParityBit(packet):
    parityBit = packet[len(packet)-1]   # ostatni element pakietu to bit parzystosci
    print(parityBit)
    array = np.array(packet)
    counter = 0
    #array[k:n] to indeksy: <k,n) "The result includes the start index, but excludes the end index."
    for x in array[0:(len(array)-1)]:   # slicing array
        if x == 1:
            counter += 1
    if counter % 2 == parityBit:
        return 1  #true
    else:
        return 0 #false


# W dokumentacji length to jest dlugosc calej wiadomosci po zakodowaniu a dimension do dlugosc wiadomosci przed zakodowaniem (tresci)
def generateCRCGolay():     #dlugosc pakietu -> 12
    code = komm.CyclicCode(length=23, generator_polynomial=0b101011100011)
    return code

def generateCRCSimplex():   #dlugosc pakietu -> 3
    coder = komm.CyclicCode(length=7, generator_polynomial=0b10111)
    return coder

def generateCRCHamming():   #dlugosc pakietu -> 4, Hamming podobnie jak BCH jest FEC
    coder = komm.CyclicCode(length=7, generator_polynomial=0b1011)
    return coder

def generateBCHCode(mi, tau):   # n = 2^(mi) - 1, 1<= tau <2^(mi-1), ; dlugosc pakietu (dimension) -> k>= n - mi*tau
    coder = komm.BCHCode(mi, tau)
    return coder

# ---------------------------------------------------SYMULACJE-------------------------------------

def compareData(data1, data2):               # zakladam, ze wymiary sa takie same
    numberOfPackets = data1.shape[0] # liczba pakietow
    packetLength = data1.shape[1] # dlugosc pakietu
    bitErrorCounter = 0
    i = 0
    j = 0
    while i < numberOfPackets:
        j = 0
        while j < packetLength:
            if(data1[i][j] != data2[i][j]):
                bitErrorCounter += 1
            j += 1
        i += 1
    return bitErrorCounter

def simulationBSCandParityBit(messageLength, packetLength, retransmissionMax):
    data = generateMessage(messageLength, packetLength)
    numberOfPackets = int(np.ceil(messageLength / packetLength))
    dataReceived = np.arange(packetLength*numberOfPackets).reshape(numberOfPackets, packetLength)    #
    i = 0
    start = time.time()
    for packet in data:
        retransmissionCounter = 0
        while retransmissionCounter < retransmissionMax:
            packetPB = addParityBit(packet)
            packetReceived = binarySymmetricChannel(packetPB, 0.1)
            if(checkParityBit(packetReceived)==0):
                retransmissionCounter+=1
            else:
                break
        packetReceived = np.delete(packetReceived, len(packetReceived)-1)    # obciac bit parzystosci
        dataReceived[i] = packetReceived
        i += 1
    end = time.time()
    bitErrorRate = (compareData(data,dataReceived)/messageLength)*100   # bit error rate (wyrazony w procentach)
    redundancy = (1-(packetLength/(packetLength+1)))*100                # nadmiar kodowy (wyrazony w procentach)
    timeCounter = (end-start)                                           # czas symulacji (w sekundach)
    return [bitErrorRate, redundancy, timeCounter]

def simulationBurstErrorandParityBit(messageLength, packetLength, lenOfSubsequence, retransmissionMax):
    data = generateMessage(messageLength, packetLength)
    numberOfPackets = int(np.ceil(messageLength / packetLength))
    dataReceived = np.arange(packetLength*numberOfPackets).reshape(numberOfPackets, packetLength)    #
    i = 0
    start = time.time()
    for packet in data:
        retransmissionCounter = 0
        while retransmissionCounter < retransmissionMax:
            packetPB = addParityBit(packet)
            packetReceived = burstErrorChannel(packetPB, 0.1, lenOfSubsequence)
            if(checkParityBit(packetReceived)==0):
                retransmissionCounter+=1
            else:
                break
        packetReceived = np.delete(packetReceived, len(packetReceived)-1)    # obciac bit parzystosci
        dataReceived[i] = packetReceived
        i += 1
    end = time.time()
    bitErrorRate = (compareData(data,dataReceived)/messageLength)*100   # bit error rate (wyrazony w procentach)
    redundancy = (1-(packetLength/(packetLength+1)))*100                # nadmiar kodowy (wyrazony w procentach)
    timeCounter = (end-start)                                           # czas symulacji (w sekundach)
    return [bitErrorRate, redundancy, timeCounter]

def simulationBSCandCRCGolay(messageLength, retransmissionMax):     # packetLength = 12
    packetLength = 12
    coder = generateCRCGolay()
    data = generateMessage(messageLength, packetLength)
    numberOfPackets = int(np.ceil(messageLength / packetLength))
    dataReceived = np.arange(packetLength*numberOfPackets).reshape(numberOfPackets, packetLength)    #
    i = 0
    start = time.time()
    for packet in data:
        retransmissionCounter = 0
        while retransmissionCounter < retransmissionMax:
            packetCRCGolayEncoded = coder.encode(packet)
            packetReceived = binarySymmetricChannel(packetCRCGolayEncoded, 0.1)
            packetCRCGolayDecoded = coder.decode(packetReceived)
            comparision = packet == packetCRCGolayDecoded
            if(comparision.all() == False):  # w bibliotece komm nie znalazlem metody, ktora pozwala sprawdzac poprawnosc odebranego pakietu, wiec go porownuje z poczatkowym
                retransmissionCounter+=1
            else:
                break
        dataReceived[i] = packetCRCGolayDecoded
        i += 1
    end = time.time()
    bitErrorRate = (compareData(data,dataReceived)/messageLength)*100   # bit error rate (wyrazony w procentach)
    redundancy = (1-(packetLength/(packetLength+11)))*100                # nadmiar kodowy (wyrazony w procentach) Golay -> 23 = 12 (pakiet) + 11 (nadmiar)
    timeCounter = (end-start)                                           # czas symulacji (w sekundach)
    return [bitErrorRate, redundancy, timeCounter]

def simulationBurstErrorandCRCGolay(messageLength, lenOfSubsequence, retransmissionMax):     # packetLength = 12
    packetLength = 12
    coder = generateCRCGolay()
    data = generateMessage(messageLength, packetLength)
    numberOfPackets = int(np.ceil(messageLength / packetLength))
    dataReceived = np.arange(packetLength*numberOfPackets).reshape(numberOfPackets, packetLength)    #
    i = 0
    start = time.time()
    for packet in data:
        retransmissionCounter = 0
        while retransmissionCounter < retransmissionMax:
            packetCRCGolayEncoded = coder.encode(packet)
            packetReceived = burstErrorChannel(packetCRCGolayEncoded, 0.1, lenOfSubsequence)
            packetCRCGolayDecoded = coder.decode(packetReceived)
            comparision = packet == packetCRCGolayDecoded
            if(comparision.all() == False):  # w bibliotece komm nie znalazlem metody, ktora pozwala sprawdzac poprawnosc odebranego pakietu (CRC), wiec go porownuje z poczatkowym
                retransmissionCounter+=1
            else:
                break
        dataReceived[i] = packetCRCGolayDecoded
        i += 1
    end = time.time()
    bitErrorRate = (compareData(data,dataReceived)/messageLength)*100   # bit error rate (wyrazony w procentach)
    redundancy = (1-(packetLength/(packetLength+11)))*100                # nadmiar kodowy (wyrazony w procentach) Golay -> 23 = 12 (pakiet) + 11 (nadmiar)
    timeCounter = (end-start)                                           # czas symulacji (w sekundach)
    return [bitErrorRate, redundancy, timeCounter]

def simulationBSCandBCH(messageLength, retransmissionMax):   # n = 2^(mi) - 1, 1<= tau <2^(mi-1), ; dlugosc pakietu (dimension) -> k>= n - mi*tau
    packetLength = 16   # >= n- mi*tau
    mi = 5
    tau = 3
    coder = generateBCHCode(mi, tau)   # (mi, tau)
    data = generateMessage(messageLength, packetLength)
    numberOfPackets = int(np.ceil(messageLength / packetLength))
    dataReceived = np.arange(packetLength*numberOfPackets).reshape(numberOfPackets, packetLength)
    i = 0
    start = time.time()
    for packet in data:
        retransmissionCounter = 0
        while retransmissionCounter < retransmissionMax:
            packetBCHEncoded = coder.encode(packet)
            packetReceived = binarySymmetricChannel(packetBCHEncoded, 0.1)
            packetBCHDecoded = coder.decode(packetReceived)
            comparision = packet == packetBCHDecoded
            if(comparision.all() == False):  # w bibliotece komm nie znalazlem metody, ktora pozwala sprawdzac poprawnosc odebranego pakietu, wiec go porownuje z poczatkowym
                retransmissionCounter+=1
            else:
                break
        dataReceived[i] = packetBCHDecoded
        i += 1
    end = time.time()
    bitErrorRate = (compareData(data, dataReceived)/messageLength)*100   # bit error rate (wyrazony w procentach)
    redundancy = (1-(packetLength/(2**mi -1)))*100                # nadmiar kodowy (wyrazony w procentach) BCH(5,3) -> 31 = 16 (pakiet) + 15 (nadmiar)
    timeCounter = (end-start)                                           # czas symulacji (w sekundach)
    return [bitErrorRate, redundancy, timeCounter]

def simulationBurstErrorandBCH(messageLength, lenOfSubsequence, retransmissionMax):   # n = 2^(mi) - 1, 1<= tau <2^(mi-1), ; dlugosc pakietu (dimension) -> k>= n - mi*tau
    packetLength = 16   # >= n- mi*tau
    mi = 5
    tau = 3
    coder = generateBCHCode(mi, tau)   # (mi, tau)
    data = generateMessage(messageLength, packetLength)
    numberOfPackets = int(np.ceil(messageLength / packetLength))
    dataReceived = np.arange(packetLength*numberOfPackets).reshape(numberOfPackets, packetLength)
    i = 0
    start = time.time()
    for packet in data:
        retransmissionCounter = 0
        while retransmissionCounter < retransmissionMax:
            packetBCHEncoded = coder.encode(packet)
            packetReceived = burstErrorChannel(packetBCHEncoded, 0.1, lenOfSubsequence)
            packetBCHDecoded = coder.decode(packetReceived)
            comparision = packet == packetBCHDecoded
            if(comparision.all() == False):  # w bibliotece komm nie znalazlem metody, ktora pozwala sprawdzac poprawnosc odebranego pakietu, wiec go porownuje z poczatkowym
                retransmissionCounter+=1
            else:
                break
        dataReceived[i] = packetBCHDecoded
        i += 1
    end = time.time()
    bitErrorRate = (compareData(data, dataReceived)/messageLength)*100   # bit error rate (wyrazony w procentach)
    redundancy = (1-(packetLength/(2**mi -1)))*100                # nadmiar kodowy (wyrazony w procentach) BCH(5,3) -> 31 = 16 (pakiet) + 15 (nadmiar)
    timeCounter = (end-start)                                           # czas symulacji (w sekundach)
    return [bitErrorRate, redundancy, timeCounter]


#--------------------------------------------TESTY----------------------------------------------------------------

#experiment = simulationBSCandParityBit(1200, 12, 2)
#experiment = simulationBurstErrorandParityBit(1200, 5, 4, 2)
#experiment = simulationBSCandCRCGolay(1200, 2)
#experiment = simulationBurstErrorandCRCGolay(1200, 3, 2)
experiment = simulationBSCandBCH(1600, 2)
#experiment = simulationBurstErrorandBCH(1600, 3, 2)
print(experiment[0])
print("\n")
print(experiment[1])
print("\n")
print(experiment[2])

