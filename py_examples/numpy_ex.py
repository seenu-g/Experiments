# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 17:29:59 2019

@author: g.srinivasan
"""

import numpy as geek
 
b = geek.empty(2, dtype = int)
print("Matrix b : \n", b)
 
a = geek.empty([2, 2], dtype = int)
print("\nMatrix a : \n", a)
 
c = geek.empty([3, 3])
print("\nMatrix c : \n", c)

array = geek.arange(8)
print("Original array : \n", array)
 
# shape array with 2 rows and 4 columns
array = geek.arange(8).reshape(2, 4)
print("\narray reshaped with 2 rows and 4 columns : \n", array)
 
# shape array with 4 rows and 2 columns
array = geek.arange(8).reshape(4 ,2)
print("\narray reshaped with 4 rows and 2 columns : \n", array)
 
# Constructs 3D array
array = geek.arange(8).reshape(2, 2, 2)
print("\nOriginal array reshaped to 3D : \n", array)