import numpy as np
import pandas as pd

def df_concat(names1, names2) :  
    result = pd.concat([names1,names2]) 
    result.loc[5] = ['Srini','43']
    #print(result)
    #print(result.shape)
    return result;

def df_populate() :
    names1 = pd.DataFrame({'name': ['Srini', 'Sai','Murthy'],
                     'Age': ['42', '30', '40']},
                    index=[0, 1, 2])
    names2 = pd.DataFrame({'name': ['Renjith', 'Poornima' ],
                     'Age': ['49', '36']},
                    index=[3, 4])  
    names = df_concat(names1,names2)
    return names 

def df_macros():
     names = df_populate()
     print(names)
     new_names = names.drop_duplicates('name')
     print(new_names.shape)
     print(new_names.sort_values('Age'))
     print(new_names.sort_values('name'))

def df_rename_columns() :
    data = {'name': ['Jason', 'Molly', 'Tina', 'Jake', 'Amy'], 
        'year': [2012, 2012, 2013, 2014, 2014], 
        'reports': [47, 24, 31, 23, 32]}
    original = pd.DataFrame(data, index = ['1', '2', '3', '4', '5'])
    print(original)
    renamed = original.rename(columns={"name": "Name", "year": "Year"})
    print(renamed)
    
def main() :
   #df_macros()
   df_rename_columns()
   
# this means that if this script is executed, then 
# main() will be executed
if __name__ == '__main__':
    main()