import numpy as np
import pandas as pd

# drop() method has inplace=False as default

def df_drop_column() :
    old_data = {'Name': ['Jai', 'Princi', 'Gaurav', 'Anuj'], 
        'Height': [5.1, 6.2, 5.1, 5.2], 
        'Qualification': ['Msc', 'MA', 'Msc', 'Msc']} 
    old_frame = pd.DataFrame(old_data) 
    address = ['Delhi', 'Bangalore', 'Chennai', 'Patna'] 
    old_frame["Address"]= address
    print(old_frame.index) #there is no index set

    # Drop the column with label 'Qualification'  
    qualification = old_frame["Qualification"]   
    #axis = 0 indictaes rows, axis =1 indicates columns     
    #inplace= False (default value)does not drop the column     
    old_frame.drop('Qualification', axis=1, inplace=True)
    print(old_frame)
    print("Shape : ", old_frame.shape)

    old_frame['Qualification'] = qualification # adds  column
    print(old_frame)
    
    old_frame.drop(columns=['Height', 'Qualification'], axis=1, inplace=True)								
    print(old_frame) # 2 columns are dropped in one shot
    

def df_drop_row() :
    data = {'name': ['Jason', 'Molly', 'Tina', 'Jake', 'Amy'], 
        'year': [2012, 2012, 2013, 2014, 2014], 
        'reports': [47, 24, 31, 23, 32]}
    original = pd.DataFrame(data, index = ['1', '2', '3', '4', '5'])
    original.drop('3',axis=0,inplace=True) #drop third row
    print(original.index) 
    original.drop(original.head(1).index,inplace=True) #drop top 1 row
    original.drop(original.tail(1).index,inplace=True) # drop bottom 1 row
    print(original)

def df_display() :
    data = {'name': ['Jason', 'Molly', 'Tina', 'Jake', 'Amy'], 
        'year': [2012, 2012, 2013, 2014, 2014], 
        'reports': [47, 24, 31, 23, 32]}
    original = pd.DataFrame(data, index = ['1', '2', '3', '4', '5'])
    
    print(original[:-1]) #display all rows expect last row
    print(original[:-2]) #display all rows expect last 2 row2
    print(original[:2]) #display first 2 rows
    print(original.head(1))    #display top 1 row
    print(original.tail(2))    #display bottom 1 row
    
def df_set_index() : 
    old_data = {'Name': ['Jai', 'Princi', 'Gaurav', 'Anuj'], 
        'Height': [5.1, 6.2, 5.1, 5.2], 
        'Qualification': ['Msc', 'MA', 'Msc', 'Msc']} 
    old_frame = pd.DataFrame(old_data) 
    address = ['Delhi', 'Bangalore', 'Chennai', 'Patna'] 
    old_frame["Address"]= address
    print(old_frame.index) #there is no index set
    old_frame.set_index('Name', inplace = True)
    print(old_frame)
    
def df_reset_index():
    original = pd.DataFrame(data=np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]), 
                      index= [2.5, 12.6, 4.8], 
                      columns=[48, 49, 50])
    print(original)
    new = original.reset_index(level=0, drop=True) # index has been dropped
    print(new)
    new1 = original.reset_index() #index remains as column, new index is in place
    print(new1)
    
def main() :
   #df_display()
   #df_reset_index()
   #df_set_index()
   df_drop_column()
   #df_drop_row()
# this means that if this script is executed, then 
# main() will be executed
if __name__ == '__main__':
    main()