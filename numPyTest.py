import numpy as np

a = np.array([1,2,3])   #Create a rank 1 array
print(type(a))          #print "<class 'numpy.ndarray'>"
print(a.shape)          #prints "(3,)"
print(a[0], a[1], a[2]) #prints "1 2 3"
a[0] = 5                #change an element of the array
print(a)                #Prints "[5,2,3]"

b = np.array([[1,2,3],[4,5,6]]) #create a rank 2 array
print(b.shape) #pokazuje, ze to jest macierz 2 na 3
print(b[0, 0], b[0, 1], b[1, 0]) #Prints "1 2 4"
