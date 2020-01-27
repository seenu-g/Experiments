"Being a strong man includes being kind and there's nothing weak about kindness and compassion" - Barack Obama
With our modern lives saturated with transactional interactions, kindness is the opposite. When you see someone today, remember to be kind; you never know how much one small true gift may mean in that moment. - Ameeta
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 14 15:56:57 2020

@author: AdminIT
"""
from sklearn import datasets
import numpy as np
from sklearn.preprocessing import scale

def display_summary() :
    # Load in the `digits` data
    # datasets module contains  methods to load & fetch popular reference datasets
    data = datasets.load_digits()
    # Print the `digits` data 
    print(data)

def display_details() :
    data = datasets.load_digits()
# To see which keys you have available to already get to know your data, 
# Get the keys of the `digits` data
    print("kyes of the data", data.keys())

# Print out the target values
    print("target values of the data data", data.target)
    data_target = data.target
# Inspect the shape
    print("Inspect the shape of data.target",data_target.shape)

# Print the number of unique labels
# data actually contains numpy arrays
    number_labels = len(np.unique(data.target))
    print("number of unique labels",number_labels)

# Isolate the `images` section
    data_images = data.images
# Inspect the shape
    print("Inspect the shape of data.shape",data_images.shape)

# Print out the description of the `digits` data
    #print("Description of the data", data.DESCR)

# Isolate the `data` section
    print("data of the data data",data.data)
# Isolate the `digits` data
    data_data = data.data
# Inspect the shape
    print("Inspect the shape of data_data",data_data.shape)
#import pandas as pd

# Load in the data with `read_csv()`
    #digits = pd.read_csv("http://archive.ics.uci.edu/ml/machine-learning-databases/optdigits/optdigits.tra", header=None)
# Print out `digits`
    #print(digits)


def main():
    #display_summary()
    #display_details()

# this means that if this script is executed, then 
# main() will be executed
if __name__ == '__main__':
    main()