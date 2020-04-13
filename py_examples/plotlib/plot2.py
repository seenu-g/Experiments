import numpy as np
import pandas as pd

# importing matplotlib
import matplotlib.pyplot as plt
import os

current_folder = os.getcwd() 
print("Current Directory", current_folder) 
parent_folder = os.path.abspath(os.path.join(current_folder, os.pardir))
print(parent_folder)
fileName = parent_folder+'/pandas/big_data.csv'

def plot_item_type_mean(fileName) :
    if(os.path.isfile(fileName)==False) :
        print ("file does not exisit")
        return
        
    df = pd.read_csv(fileName)
    price_by_item = df.groupby('Item_Type').Item_MRP.mean()[:10]
    item_type_list = price_by_item.index.tolist()
    item_type_mean_list = price_by_item.values.tolist()
    
    # set figure size
    plt.figure(figsize=(14, 8))
    plt.title('Mean price for each item type')
    plt.xlabel('Item Type')
    plt.ylabel('Mean Price')
    plt.xticks(labels=item_type_list, ticks=np.arange(len(item_type_list)))

    plt.plot(item_type_list, item_type_mean_list)
    plt.show()
    
plot_item_type_mean(fileName)

def plot_multiple_graphs() :
    calories_burnt = [150,160,165,185]
    weight = [70, 80, 90, 100]
    kms_run = [5,9,20,10]
    
    # plt.legend(labels=['Calories Burnt', 'Weight',"Run Kms"], loc='lower right')
    
    fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(6,6), sharex=True, sharey=True)
    ax[0].plot(calories_burnt)
    #ax[0].plot(calories_burnt,'go') #plot dots

    ax[1].plot(weight)
    ax[0].set_title("Calories Burnt")
    ax[1].set_title("Weight")
    
    ax[0].set_xticks(ticks=[0,1,2,3])
    ax[1].set_xticks(ticks=[0,1,2,3])
    
    ax[0].set_xticklabels(labels=['p1', 'p2', 'p3', 'p4']);
    ax[1].set_xticklabels(labels=['p1', 'p2', 'p3', 'p4']);
    plt.show()

plot_multiple_graphs()