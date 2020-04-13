# -*- coding: utf-8 -*-
"""
Created on Thu Nov 21 17:18:44 2019

@author: g.srinivasan
"""
import csv
def read_csv_file(in_file_name):
     in_file = open(in_file_name,"r")
     data = []
     for row in csv.reader(in_file):
        data.append(row)
        #print (row) # display row
     in_file.close()
     print(data) # display list
     # for item in data:
     #   print(item[0],item[1],item[2])

def write_csv_file(out_file_name):
    data =[["Suraj","21","Male"],
           ["Naveen","21","Male"],
           ["Neha","21","Female"]]
    out_file = open(out_file_name,"w+")
    for item in data:
       csv.writer(out_file).writerow(item)
    out_file.close()
    
write_csv_file("family.csv")
read_csv_file("family.csv")
