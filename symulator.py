import numpy as np
import komm as komm
import time
import xlsxwriter as excelWriter

# -----------------------------METODY--DO--SYMULACJI-----------------------------------------------------------------

def generateMessage(messageLength, packetLength):                   #wygenerwoanie wiadomosci i podzielenie jej na pakiety
    numberOfPackets = int(np.ceil(messageLength/packetLength))      #liczba pakietow zaokraglona w gore do liczby calkowitej
    data = np.arange(packetLength*numberOfPackets).reshape(numberOfPackets, packetLength)
    i = 0
    j = 0
    while i < numberOfPackets:
        while j < packetLength:
            data[i][j] = np.random.randint(2)                        #losowy int <0,2) czyli 0 lub 1
            j += 1
        i += 1
        j = 0
    return data


def binarySymmetricChannel(packet, probability):                  # bledy pojedyncze -> Model BSC
    bsc = komm.BinarySymmetricChannel(probability)
    return bsc(packet)

def burstErrorChannel(packet, probability, lenOfSubsequence):     # bledy grupowe -> Model Gilberta
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
                if(packet[i+j] == 1): packet[i+j] = 0       # negacja bitow w podciagu
                else: packet[i+j] = 1
                j += 1
                if ((j + i) == packetLen): return packet    # wykroczylismy poza pakiet
            i += j                                          # dodanie roznicy + przejscie do kolejnego bitu
    return packet

def addParityBit(packet):   #dodajemy bit parzystosci wzgledem "1"
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
        return 1     #true
    else:
        return 0    #false


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
# metoda porownujaca dane przed wyslaniem z danymi po wyslaniu
def compareData(data1, data2):               # zakladam, ze wymiary sa takie same
    numberOfPackets = data1.shape[0]         # liczba pakietow
    packetLength = data1.shape[1]            # dlugosc pakietu
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

def simulationBSCandParityBit(messageLength, packetLength, retransmissionMax, channelErrorProbability):
    data = generateMessage(messageLength, packetLength)
    numberOfPackets = int(np.ceil(messageLength / packetLength))
    dataReceived = np.arange(packetLength*numberOfPackets).reshape(numberOfPackets, packetLength)    #
    i = 0
    numberOfRetransmissions = 0
    start = time.time()
    for packet in data:
        retransmissionCounter = 0
        while retransmissionCounter < retransmissionMax:
            packetPB = addParityBit(packet)
            packetReceived = binarySymmetricChannel(packetPB, channelErrorProbability)
            if(checkParityBit(packetReceived)==0):
                retransmissionCounter+=1
                numberOfRetransmissions+=1
            else:
                break
        packetReceived = np.delete(packetReceived, len(packetReceived)-1)    # obciecie bitu parzystosci
        dataReceived[i] = packetReceived
        i += 1
    end = time.time()
    bitErrorRate = (compareData(data,dataReceived)/messageLength)*100   # bit error rate (wyrazony w procentach)
    codeRedundancy = (1-(packetLength/(packetLength+1)))*100                # nadmiar kodowy (wyrazony w procentach)
    redundancy = ((numberOfRetransmissions*(packetLength+1)+numberOfPackets*1)/((numberOfRetransmissions+ numberOfPackets)*(packetLength+1)))*100
    allBits = (numberOfPackets+numberOfRetransmissions)*(packetLength+1)
    aValue = allBits/messageLength
    timeCounter = (end-start)                                           # czas symulacji (w sekundach)
    return [bitErrorRate, aValue, timeCounter, channelErrorProbability] #[bitErrorRate, codeRedundancy, redundancy, timeCounter, channelErrorProbability]

def simulationBurstErrorandParityBit(messageLength, packetLength, lenOfSubsequence, retransmissionMax, channelErrorProbability):
    data = generateMessage(messageLength, packetLength)
    numberOfPackets = int(np.ceil(messageLength / packetLength))
    dataReceived = np.arange(packetLength*numberOfPackets).reshape(numberOfPackets, packetLength)
    i = 0
    numberOfRetransmissions = 0
    start = time.time()
    for packet in data:
        retransmissionCounter = 0
        while retransmissionCounter < retransmissionMax:
            packetPB = addParityBit(packet)
            packetReceived = burstErrorChannel(packetPB, channelErrorProbability, lenOfSubsequence)
            if(checkParityBit(packetReceived)==0):
                retransmissionCounter+=1
                numberOfRetransmissions+=1
            else:
                break
        packetReceived = np.delete(packetReceived, len(packetReceived)-1)    # obciecie bitu parzystosci
        dataReceived[i] = packetReceived
        i += 1
    end = time.time()
    bitErrorRate = (compareData(data,dataReceived)/messageLength)*100   # bit error rate (wyrazony w procentach)
    codeRedundancy = (1-(packetLength/(packetLength+1)))*100                # nadmiar kodowy (wyrazony w procentach)
    redundancy = ((numberOfRetransmissions*(packetLength+1)+numberOfPackets*1)/((numberOfRetransmissions+ numberOfPackets)*(packetLength+1)))*100
    allBits = (numberOfPackets+numberOfRetransmissions)*(packetLength+1)
    aValue = allBits/messageLength
    timeCounter = (end-start)                                           # czas symulacji (w sekundach)
    return [bitErrorRate, aValue, timeCounter, channelErrorProbability]  #[bitErrorRate, codeRedundancy, redundancy, timeCounter, channelErrorProbability]


# packetLength = 12, stala dlugosc pakietu
def simulationBSCandCRCGolay(messageLength, retransmissionMax, channelErrorProbability):
    packetLength = 12
    coder = generateCRCGolay()
    data = generateMessage(messageLength, packetLength)
    numberOfPackets = int(np.ceil(messageLength / packetLength))
    dataReceived = np.arange(packetLength*numberOfPackets).reshape(numberOfPackets, packetLength)    #
    i = 0
    numberOfRetransmissions = 0
    start = time.time()
    for packet in data:
        retransmissionCounter = 0
        while retransmissionCounter < retransmissionMax:
            packetCRCGolayEncoded = coder.encode(packet)
            packetReceived = binarySymmetricChannel(packetCRCGolayEncoded, channelErrorProbability)
            packetCRCGolayDecoded = coder.decode(packetReceived)
            comparision = packet == packetCRCGolayDecoded
            if(comparision.all() == False):  # w bibliotece komm nie znalazlem metody, ktora pozwala sprawdzac poprawnosc odebranego pakietu, wiec go porownuje z poczatkowym
                retransmissionCounter+=1
                numberOfRetransmissions+=1
            else:
                break
        dataReceived[i] = packetCRCGolayDecoded
        i += 1
    end = time.time()
    bitErrorRate = (compareData(data,dataReceived)/messageLength)*100   # bit error rate (wyrazony w procentach)
    codeRedundancy = (1-(packetLength/(packetLength+11)))*100                # nadmiar kodowy (wyrazony w procentach) Golay -> 23 = 12 (pakiet) + 11 (nadmiar)
    redundancy = ((23*numberOfRetransmissions+numberOfPackets*11)/((numberOfRetransmissions+ numberOfPackets)*(23)))*100
    allBits = (numberOfPackets+numberOfRetransmissions)*(packetLength+11)
    aValue = allBits/messageLength
    timeCounter = (end-start)                                           # czas symulacji (w sekundach)
    return [bitErrorRate, aValue, timeCounter, channelErrorProbability]  #[bitErrorRate, codeRedundancy, redundancy, timeCounter, channelErrorProbability]

def simulationBurstErrorandCRCGolay(messageLength, lenOfSubsequence, retransmissionMax, channelErrorProbability):     # packetLength = 12
    packetLength = 12
    coder = generateCRCGolay()
    data = generateMessage(messageLength, packetLength)
    numberOfPackets = int(np.ceil(messageLength / packetLength))
    dataReceived = np.arange(packetLength*numberOfPackets).reshape(numberOfPackets, packetLength)    #
    i = 0
    numberOfRetransmissions = 0
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
                numberOfRetransmissions+=1
            else:
                break
        dataReceived[i] = packetCRCGolayDecoded
        i += 1
    end = time.time()
    bitErrorRate = (compareData(data,dataReceived)/messageLength)*100   # bit error rate (wyrazony w procentach)
    codeRedundancy = (1-(packetLength/(packetLength+11)))*100                # nadmiar kodowy (wyrazony w procentach) Golay -> 23 = 12 (pakiet) + 11 (nadmiar)
    redundancy = ((23 * numberOfRetransmissions + numberOfPackets*11) / ((numberOfRetransmissions + numberOfPackets)*(23)))*100
    allBits = (numberOfPackets+numberOfRetransmissions)*(packetLength+11)
    aValue = allBits/messageLength
    timeCounter = (end-start)                                           # czas symulacji (w sekundach)
    return [bitErrorRate, aValue, timeCounter, channelErrorProbability]  #[bitErrorRate, codeRedundancy, redundancy, timeCounter, channelErrorProbability]

def simulationBSCandBCH(messageLength, retransmissionMax, channelErrorProbability):   # n = 2^(mi) - 1, 1<= tau <2^(mi-1), ; dlugosc pakietu (dimension) -> k>= n - mi*tau
    packetLength = 16   # >= n- mi*tau
    mi = 5
    tau = 3
    coder = generateBCHCode(mi, tau)   # (mi, tau)
    data = generateMessage(messageLength, packetLength)
    numberOfPackets = int(np.ceil(messageLength / packetLength))
    dataReceived = np.arange(packetLength*numberOfPackets).reshape(numberOfPackets, packetLength)
    i = 0
    numberOfRetransmissions = 0
    start = time.time()
    for packet in data:
        retransmissionCounter = 0
        while retransmissionCounter < retransmissionMax:
            packetBCHEncoded = coder.encode(packet)
            packetReceived = binarySymmetricChannel(packetBCHEncoded, channelErrorProbability)
            packetBCHDecoded = coder.decode(packetReceived)
            comparision = packet == packetBCHDecoded
            if(comparision.all() == False):  # w bibliotece komm nie znalazlem metody, ktora pozwala sprawdzac poprawnosc odebranego pakietu, wiec go porownuje z poczatkowym
                retransmissionCounter+=1
                numberOfRetransmissions +=1
            else:
                break
        dataReceived[i] = packetBCHDecoded
        i += 1
    end = time.time()
    bitErrorRate = (compareData(data, dataReceived)/messageLength)*100   # bit error rate (wyrazony w procentach)
    codeRedundancy = (1-(packetLength/(2**mi -1)))*100                # nadmiar kodowy (wyrazony w procentach) BCH(5,3) -> 31 = 16 (pakiet) + 15 (nadmiar)
    redundancy = ((31*numberOfRetransmissions + numberOfPackets*15) / ((numberOfRetransmissions + numberOfPackets) * (31))) * 100
    allBits = (numberOfPackets+numberOfRetransmissions)*(packetLength+15)
    aValue = allBits/messageLength
    timeCounter = (end-start)                                           # czas symulacji (w sekundach)
    return [bitErrorRate, aValue, timeCounter, channelErrorProbability]  #[bitErrorRate, codeRedundancy, redundancy, timeCounter, channelErrorProbability]

def simulationBurstErrorandBCH(messageLength, lenOfSubsequence, retransmissionMax, channelErrorProbability):   # n = 2^(mi) - 1, 1<= tau <2^(mi-1), ; dlugosc pakietu (dimension) -> k>= n - mi*tau
    packetLength = 16   # >= n- mi*tau
    mi = 5
    tau = 3
    coder = generateBCHCode(mi, tau)   # (mi, tau)
    data = generateMessage(messageLength, packetLength)
    numberOfPackets = int(np.ceil(messageLength / packetLength))
    dataReceived = np.arange(packetLength*numberOfPackets).reshape(numberOfPackets, packetLength)
    i = 0
    numberOfRetransmissions = 0
    start = time.time()
    for packet in data:
        retransmissionCounter = 0
        while retransmissionCounter < retransmissionMax:
            packetBCHEncoded = coder.encode(packet)
            packetReceived = burstErrorChannel(packetBCHEncoded, channelErrorProbability, lenOfSubsequence)
            packetBCHDecoded = coder.decode(packetReceived)
            comparision = packet == packetBCHDecoded
            if(comparision.all() == False):  # w bibliotece komm nie znalazlem metody, ktora pozwala sprawdzac poprawnosc odebranego pakietu, wiec go porownuje z poczatkowym
                retransmissionCounter += 1
                numberOfRetransmissions += 1
            else:
                break
        dataReceived[i] = packetBCHDecoded
        i += 1
    end = time.time()
    bitErrorRate = (compareData(data, dataReceived)/messageLength)*100   # bit error rate (wyrazony w procentach)
    codeRedundancy = (1-(packetLength/(2**mi -1)))*100                      # nadmiar kodowy (wyrazony w procentach) BCH(5,3) -> 31 = 16 (pakiet) + 15 (nadmiar)
    redundancy = ((31 * numberOfRetransmissions + numberOfPackets * 15) / ((numberOfRetransmissions + numberOfPackets) * (31))) * 100
    allBits = (numberOfPackets+numberOfRetransmissions)*(packetLength+15)
    aValue = allBits/messageLength
    timeCounter = (end-start)                                           # czas symulacji (w sekundach)
    return [bitErrorRate, aValue, timeCounter, channelErrorProbability]  # [bitErrorRate, codeRedundancy, redundancy, timeCounter, channelErrorProbability]

# ------------------------------------------- EKSPERYMENTY --------------------------------------------

def writeInExcel(rowIndex, columnIndex, data, worksheet):
    for value in data:
        worksheet.write(rowIndex, columnIndex, value)
        columnIndex += 1
    return


def experimentBSCandParityBit(workbook):
    rowIndex = 0
    messageLength = 1200 # zakladam, ze jest stale
    retransmissionMax = 2 # zakladam, ze jest stale
    maxNumInSeries = 20
    numInSeries = 0
    worksheet = workbook.add_worksheet("BSC and ParityBit")
    data = ["Bit error rate [%]", "'a' Value [M = a*N]", "Time of simulation [s]","Channel error probability "] # ["Bit error rate [%]", "Code redundancy [%]","Redundancy (with retransmissions)[%]", "Time of simulation [s]","Channel error probability "]
    writeInExcel(rowIndex, 0, data,  worksheet)
    rowIndex +=1
    channelErrorProbability = 0.1
    packetLength = 12
    while numInSeries < maxNumInSeries: # pierwsza seria pomiarów dla channelErrorProbability = 0.1 i packetLength = 12 n = 12+1 (parity bit)
        experiment = simulationBSCandParityBit(messageLength, packetLength, retransmissionMax, channelErrorProbability)
        writeInExcel(rowIndex, 0, experiment,  worksheet)
        rowIndex += 1
        numInSeries += 1
    numInSeries = 0 # wyzerowanie licznika serii
    channelErrorProbability = 0.15
    packetLength = 5
    while numInSeries < maxNumInSeries: # druga seria pomiarów dla channelErrorProbability = 0.15 i packetLength = 5 n = 5+1 (parity bit)
        experiment = simulationBSCandParityBit(messageLength, packetLength, retransmissionMax, channelErrorProbability)
        writeInExcel(rowIndex, 0, experiment,  worksheet)
        rowIndex += 1
        numInSeries += 1
    numInSeries = 0     # wyzerowanie licznika serii
    channelErrorProbability = 0.05
    packetLength = 15
    while numInSeries < maxNumInSeries: # trzecia seria pomiarów dla channelErrorProbability = 0.05 i packetLength = 5 n = 15+1 (parity bit)
        experiment = simulationBSCandParityBit(messageLength, packetLength, retransmissionMax, channelErrorProbability)
        writeInExcel(rowIndex, 0, experiment,  worksheet)
        rowIndex += 1
        numInSeries += 1

    return

def experimentBurstErrorandParityBit(workbook):
    rowIndex = 0
    messageLength = 1200 # zakladam, ze jest stale
    lenOfSubsequence = 4
    retransmissionMax = 2 # zakladam, ze jest stale
    maxNumInSeries = 20
    numInSeries = 0
    worksheet = workbook.add_worksheet("BurstError and ParityBit")
    data = ["Bit error rate [%]", "'a' Value [M = a*N]", "Time of simulation [s]","Channel error probability "] #["Bit error rate [%]", "Code redundancy [%]","Redundancy (with retransmissions)[%]", "Time of simulation [s]","Channel error probability "]
    writeInExcel(rowIndex, 0, data,  worksheet)
    rowIndex +=1
    channelErrorProbability = 0.1
    packetLength = 12
    while numInSeries < maxNumInSeries:
        experiment = simulationBurstErrorandParityBit(messageLength, packetLength, lenOfSubsequence, retransmissionMax, channelErrorProbability)
        writeInExcel(rowIndex, 0, experiment, worksheet)
        rowIndex +=1
        numInSeries +=1
    numInSeries = 0  # wyzerowanie licznika serii
    channelErrorProbability = 0.15
    packetLength = 5
    while numInSeries < maxNumInSeries:
        experiment = simulationBurstErrorandParityBit(messageLength, packetLength, lenOfSubsequence, retransmissionMax, channelErrorProbability)
        writeInExcel(rowIndex, 0, experiment, worksheet)
        rowIndex +=1
        numInSeries +=1
    numInSeries = 0  # wyzerowanie licznika serii
    channelErrorProbability = 0.05
    packetLength = 15
    while numInSeries < maxNumInSeries:
        experiment = simulationBurstErrorandParityBit(messageLength, packetLength, lenOfSubsequence, retransmissionMax, channelErrorProbability)
        writeInExcel(rowIndex, 0, experiment, worksheet)
        rowIndex +=1
        numInSeries +=1
    return

def experimentBSCandCRCGolay(workbook):
    rowIndex = 0
    messageLength = 1200 # zakladam, ze jest stale
    retransmissionMax = 2 # zakladam, ze jest stale
    maxNumInSeries = 20
    numInSeries = 0
    worksheet = workbook.add_worksheet("BSC and CRC Golay")
    data = ["Bit error rate [%]", "'a' Value [M = a*N]", "Time of simulation [s]","Channel error probability "] #["Bit error rate [%]", "Code redundancy [%]","Redundancy (with retransmissions)[%]", "Time of simulation [s]","Channel error probability "]
    writeInExcel(rowIndex, 0, data,  worksheet)
    rowIndex +=1
    channelErrorProbability = 0.1
    while numInSeries < maxNumInSeries:
        experiment = simulationBSCandCRCGolay(messageLength, retransmissionMax, channelErrorProbability) # packetLength = 12 staly
        writeInExcel(rowIndex, 0, experiment, worksheet)
        rowIndex +=1
        numInSeries +=1
    numInSeries = 0
    channelErrorProbability = 0.15
    while numInSeries < maxNumInSeries:
        experiment = simulationBSCandCRCGolay(messageLength, retransmissionMax, channelErrorProbability) # packetLength = 12 staly
        writeInExcel(rowIndex, 0, experiment, worksheet)
        rowIndex +=1
        numInSeries +=1
    numInSeries = 0
    channelErrorProbability = 0.05
    while numInSeries < maxNumInSeries:
        experiment = simulationBSCandCRCGolay(messageLength, retransmissionMax, channelErrorProbability) # packetLength = 12 staly
        writeInExcel(rowIndex, 0, experiment, worksheet)
        rowIndex +=1
        numInSeries +=1
    return

def experimentBurstErrorandCRCGolay(workbook):
    rowIndex = 0
    messageLength = 1200 # zakladam, ze jest stale
    lenOfSubsequence = 3
    retransmissionMax = 2 # zakladam, ze jest stale
    maxNumInSeries = 20
    numInSeries = 0
    worksheet = workbook.add_worksheet("BurstError and CRC Golay")
    data = ["Bit error rate [%]", "'a' Value [M = a*N]", "Time of simulation [s]","Channel error probability "] #["Bit error rate [%]", "Code redundancy [%]","Redundancy (with retransmissions)[%]", "Time of simulation [s]","Channel error probability "]
    writeInExcel(rowIndex, 0, data,  worksheet)
    rowIndex +=1
    channelErrorProbability = 0.1
    while numInSeries < maxNumInSeries:
        experiment = simulationBurstErrorandCRCGolay(messageLength, lenOfSubsequence, retransmissionMax, channelErrorProbability) #  packetLength = 12
        writeInExcel(rowIndex, 0, experiment, worksheet)
        rowIndex += 1
        numInSeries += 1
    numInSeries = 0
    channelErrorProbability = 0.15
    while numInSeries < maxNumInSeries:
        experiment = simulationBurstErrorandCRCGolay(messageLength, lenOfSubsequence, retransmissionMax, channelErrorProbability) #  packetLength = 12
        writeInExcel(rowIndex, 0, experiment, worksheet)
        rowIndex += 1
        numInSeries += 1
    numInSeries = 0
    channelErrorProbability = 0.05
    while numInSeries < maxNumInSeries:
        experiment = simulationBurstErrorandCRCGolay(messageLength, lenOfSubsequence, retransmissionMax, channelErrorProbability) #  packetLength = 12
        writeInExcel(rowIndex, 0, experiment, worksheet)
        rowIndex += 1
        numInSeries += 1
    return

def experimentBSCandBCH(workbook):
    rowIndex = 0
    messageLength = 1200 # zakladam, ze jest stale
    retransmissionMax = 2 # zakladam, ze jest stale
    maxNumInSeries = 20
    numInSeries = 0
    worksheet = workbook.add_worksheet("BSC and BCH")
    data = ["Bit error rate [%]", "'a' Value [M = a*N]", "Time of simulation [s]","Channel error probability "] #["Bit error rate [%]", "Code redundancy [%]","Redundancy (with retransmissions)[%]", "Time of simulation [s]","Channel error probability "]
    writeInExcel(rowIndex, 0, data,  worksheet)
    rowIndex +=1
    channelErrorProbability = 0.1
    while numInSeries < maxNumInSeries:
        experiment = simulationBSCandBCH(messageLength, retransmissionMax, channelErrorProbability) # packetLength = 16 staly
        writeInExcel(rowIndex, 0, experiment, worksheet)
        rowIndex += 1
        numInSeries += 1
    numInSeries = 0
    channelErrorProbability = 0.05
    while numInSeries < maxNumInSeries:
        experiment = simulationBSCandBCH(messageLength, retransmissionMax, channelErrorProbability) # packetLength = 16 staly
        writeInExcel(rowIndex, 0, experiment, worksheet)
        rowIndex += 1
        numInSeries += 1
    numInSeries = 0
    channelErrorProbability = 0.15
    while numInSeries < maxNumInSeries:
        experiment = simulationBSCandBCH(messageLength, retransmissionMax, channelErrorProbability) # packetLength = 16 staly
        writeInExcel(rowIndex, 0, experiment, worksheet)
        rowIndex += 1
        numInSeries += 1
    return

def experimentBurstErrorandBCH(workbook):
    rowIndex = 0
    messageLength = 1200 # zakladam, ze jest stale
    lenOfSubsequence = 3
    retransmissionMax = 2 # zakladam, ze jest stale
    maxNumInSeries = 20
    numInSeries = 0
    worksheet = workbook.add_worksheet("BurstError and BCH")
    data = ["Bit error rate [%]", "'a' Value [M = a*N]", "Time of simulation [s]", "Channel error probability "]  # ["Bit error rate [%]", "Code redundancy [%]","Redundancy (with retransmissions)[%]", "Time of simulation [s]","Channel error probability "]
    writeInExcel(rowIndex, 0, data,  worksheet)
    rowIndex +=1
    channelErrorProbability = 0.1
    while numInSeries < maxNumInSeries:
        experiment = simulationBurstErrorandBCH(messageLength, lenOfSubsequence, retransmissionMax, channelErrorProbability) #  packetLength = 16
        writeInExcel(rowIndex, 0, experiment, worksheet)
        rowIndex +=1
        numInSeries +=1
    numInSeries = 0
    channelErrorProbability = 0.05
    while numInSeries < maxNumInSeries:
        experiment = simulationBurstErrorandBCH(messageLength, lenOfSubsequence, retransmissionMax, channelErrorProbability) #  packetLength = 16
        writeInExcel(rowIndex, 0, experiment, worksheet)
        rowIndex +=1
        numInSeries +=1
    numInSeries = 0
    channelErrorProbability = 0.15
    while numInSeries < maxNumInSeries:
        experiment = simulationBurstErrorandBCH(messageLength, lenOfSubsequence, retransmissionMax, channelErrorProbability) #  packetLength = 16
        writeInExcel(rowIndex, 0, experiment, worksheet)
        rowIndex +=1
        numInSeries +=1
    return
#--------------------------------------------TESTY----------------------------------------------------------------

workbook = excelWriter.Workbook('Pomiary.xlsx')

# simulationBSCandParityBit(messageLength, packetLength, retransmissionMax, channelErrorProbability):
#experiment = simulationBSCandParityBit(1200, 12, 2, 0.1) # return [bitErrorRate, codeRedundancy, redundancy, timeCounter, channelErrorProbability]
experimentBSCandParityBit(workbook)

# simulationBurstErrorandParityBit(messageLength, packetLength, lenOfSubsequence, retransmissionMax, channelErrorProbability):
#experiment = simulationBurstErrorandParityBit(1200, 5, 4, 2) # return [bitErrorRate, codeRedundancy, redundancy, timeCounter, channelErrorProbability]
experimentBurstErrorandParityBit(workbook)

# simulationBSCandCRCGolay(messageLength, retransmissionMax, channelErrorProbability):
#experiment = simulationBSCandCRCGolay(1200, 2) # return [bitErrorRate, codeRedundancy, redundancy, timeCounter, channelErrorProbability]
experimentBSCandCRCGolay(workbook)

# simulationBurstErrorandCRCGolay(messageLength, lenOfSubsequence, retransmissionMax, channelErrorProbability)
#experiment = simulationBurstErrorandCRCGolay(1200, 3, 2) # return [bitErrorRate, codeRedundancy, redundancy, timeCounter, channelErrorProbability]
experimentBurstErrorandCRCGolay(workbook)

# simulationBSCandBCH(messageLength, retransmissionMax, channelErrorProbability)
#experiment = simulationBSCandBCH(1600, 2) # return [bitErrorRate, codeRedundancy, redundancy, timeCounter, channelErrorProbability]
experimentBSCandBCH(workbook)

# simulationBurstErrorandBCH(messageLength, lenOfSubsequence, retransmissionMax, channelErrorProbability)
#experiment = simulationBurstErrorandBCH(1600, 3, 2) # return [bitErrorRate, codeRedundancy, redundancy, timeCounter, channelErrorProbability]
experimentBurstErrorandBCH(workbook)

workbook.close()

# print("Bit error rate: ", experiment[0], "%")
# print("Redundancy: ",experiment[1], "%")
# print("Time of simulation: ",experiment[2],"s")