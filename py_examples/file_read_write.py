# -*- coding: utf-8 -*-
"""
Created on Thu Nov 21 16:25:39 2019

@author: g.srinivasan
"""

def read_file(in_file_name):
    in_file = open(in_file_name,"r")
    for line in in_file :
        print (line)
    in_file.close()
    
def write_file(out_file_name,name, age,location):
    outfile = open(out_file_name,"a+")
    outfile.write("My name is " + name + " \n")
    outfile.write("My age is " + age + " \n")
    outfile.write("My location is " + location + " \n")
    outfile.close()

def copy_file(in_file_name, out_file_name):
    infile = open(in_file_name)
    outfile = open(out_file_name)
    
    for line in infile:
        outfile.write(line)
    
    infile.close()
    outfile.close()

write_file("output.txt","Suraj","21","Bangalore")
write_file("output.txt","Aditya","22","Bihar")
write_file("output.txt","Poornima","33","Chennai")
read_file("output.txt")

"""
'r'	Opens file for reading.
'w'	Opens file for writing.
    file  not exist,creates a new file.file exists, truncates the file.
'a'	Open file in append mode.file not exist,creates a new file.
'+'	open file for reading and writing (+updating)
"""