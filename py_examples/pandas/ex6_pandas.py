import numpy as np
import pandas as pd

def df_from_dictionary() :
    dic = {'Name': ["Sai", "Srini"], 'Age': [30, 40]}
    df = pd.DataFrame(data=dic)	
    print('Data Frame:', df)

def df_numpy():
    h = [[1,2],[3,4]] 
    df = pd.DataFrame(h)
    print('Data Frame:', df)
   
    numpy1 = np.array(df)
    print('Numpy array numpy1:', numpy1)
    
    numpy1  = np.array([(1,2,),(4,5,),(7,8,),(10,11)]) 
    df = pd.DataFrame(numpy1)
    print('Data Frame:', df)

    numpy2 = np.array(df)
    print('Numpy array numpy2:', numpy2)

def df_date():
    dates_d = pd.date_range('20300101', periods=6, freq='D')
    print('Day:', dates_d)
    months_m = pd.date_range('20300101', periods=6, freq='M')
    print('Month:', months_m)
    years_y = pd.date_range('20300101', periods=6, freq='Y')
    print('Month:', years_y)
    
    # Convert data frame to numpy array
    numpy2 = np.array(years_y)
    print('Numpy array numpy2:', numpy2)

def main() :
    #df_numpy()
    #df_from_dictionary()
    df_date()
# this means that if this script is executed, then 
# main() will be executed
if __name__ == '__main__':
    main()
