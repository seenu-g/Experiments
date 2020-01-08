
import numpy as np
import pandas as pd

def add_row(df) :
    # There's no index labeled `2`, so you will change the index at position `2`
    # use .loc to insert rows in your DataFrame
    # .ix has been deprecated
    df.loc[2] = [60, 50, 40]
    return df

def add_index_as_column(df) :
    df[51] = df.index
    return df

def add_column(df,label) :
    new_col = [12.5,22.6,14.8,12.0]
    df[label] = new_col 
    return df

def add_column_value(df,label, col_values) :
    new_col = col_values
    df[label] = new_col 
    return df

def main():
    original = pd.DataFrame(data=np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]), 
                      index= [2.5, 12.6, 4.8], 
                      columns=[48, 49, 50])
    print(original)
    new = add_row(original)
    
    print(new)
    print ("index ", new.index)
    
    new = add_index_as_column(new)
    print(new)
    
    new = add_column(new,52)
    print(new)
    
    old_data = {'Name': ['Jai', 'Princi', 'Gaurav', 'Anuj'], 
        'Height': [5.1, 6.2, 5.1, 5.2], 
        'Qualification': ['Msc', 'MA', 'Msc', 'Msc']} 
    old_frame = pd.DataFrame(old_data) 
    address = ['Delhi', 'Bangalore', 'Chennai', 'Patna'] 
    new_frame = add_column_value(old_frame,"Address", address)
    print(new_frame)

# this means that if this script is executed, then 
# main() will be executed
if __name__ == '__main__':
    main()