import numpy as np
import komm as komm

def binarySymmetricChannel(packet, probability):
    bsc = komm.BinarySymmetricChannel(probability)
    return bsc(packet)

packet = [0, 1, 1, 1, 0, 0, 0, 0, 0, 1]
x = binarySymmetricChannel(packet, 0.1)

print(x)

