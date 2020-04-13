import numpy as np
import pandas as pd

# importing matplotlib
import matplotlib.pyplot as plt

def plot_line_graph() :
    height = [150,160,165,185]
    weight = [70, 80, 90, 100]

    plt.title("Relationship between height and weight")
    plt.xlabel("Height")
    plt.ylabel("Weight")

    # draw the plot
    plt.plot(height, weight)
    plt.show()
    
plot_line_graph()

def plot_multiple_line_graph() :
    calories_burnt = [150,160,165,185]
    weight = [70, 80, 90, 100]
    kms_run = [5,9,20,10]
    plt.plot(calories_burnt)
    plt.plot(weight)
    plt.plot(kms_run)
    plt.legend(labels=['Calories Burnt', 'Weight',"Run Kms"], loc='lower right')
    plt.xticks(ticks=[0,1,2,3], labels=['p1', 'p2', 'p3', 'p4']);
    plt.show()

plot_multiple_line_graph()

import os

current_folder = os.getcwd() 
print("Current Directory", current_folder) 
parent_folder = os.path.abspath(os.path.join(current_folder, os.pardir))
print(parent_folder)
fileName = parent_folder+'/pandas/big_data.csv'

def plot_bar_graph():
    if(os.path.isfile(fileName)==False) :
        print ("file does not exisit")
        return
        
    df = pd.read_csv(fileName)
    gp_outlet_size = df.groupby('Outlet_Size')
    sales_by_outlet_size = gp_outlet_size.Item_Outlet_Sales.mean()
    sales_by_outlet_size.sort_values(inplace=True)
    
    outlet_size_list = sales_by_outlet_size.index.tolist()
    outlet_mean_list = sales_by_outlet_size.values.tolist()
    
    plt.xlabel('Outlet Size')
    plt.ylabel('Sales')
   
    plt.title('Mean sales for each outlet type')
    plt.xticks(labels=outlet_size_list, ticks=np.arange(len(outlet_size_list)))
   
    plt.bar(outlet_size_list, outlet_mean_list, color=['red', 'orange', 'magenta'])
    #plt.bar(outlet_size_list, outlet_mean_list)
    plt.show()
    
plot_bar_graph()