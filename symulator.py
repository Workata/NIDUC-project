import numpy as np
import komm as komm

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

#testy
packet = [0, 1, 1, 1, 0, 0, 1, 0, 0, 1]
y = addParityBit(packet)
#x = binarySymmetricChannel(packet, 0.1)
print(y)
#print(x)

