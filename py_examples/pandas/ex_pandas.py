
import numpy as np
import pandas as pd
#A series is a one-dimensional data structure. cannot have multiple columns
#Data: can be a list, dictionary or scalar value
def create_series() :
    a = pd.Series([1., 2., 3.])			
    b = pd.Series([1,2,np.nan])
    print(a)
    print(b)

#A data frame is a tabular data, with rows to store the information and 
#                                     columns to name the information
def create_simple_data_frame() :
    dic = {'Name': ["John", "Smith"], 'Age': [30, 40]}
    df1 = pd.DataFrame(data=dic)		
    print(df1)
    
    dates_d = pd.date_range('20300101', periods=6, freq='D')
    print('Day:', dates_d)

    dates_m = pd.date_range('20300101', periods=6, freq='M')
    print('Month:', dates_m)
    
def populate_data_frame() :
    random = np.random.randn(6,4)	#Create a random sequence with numpy
    dates_m = pd.date_range('20300101', periods=6, freq='M')
    
    df = pd.DataFrame(random,index=dates_m,columns=list('ABCD'))
    dfhead = df.head(3) # display tope 3 rows
    print(dfhead)
    print()
    dftail = df.tail(3) # display bottom 3 rows
    print(dftail)
    
    print()
    print(df['A'])
    print(df[['A', 'C']]) # display columns A and C
    print(df[0:3]) # display first 3 rows
    print(df.describe()) # apply formulas
    print(df.loc[:,['A','C']])	#same as above ones.

def main():
   #create_series()
   #create_simple_data_frame() 
   populate_data_frame()
  
   
# this means that if this script is executed, then 
# main() will be executed
if __name__ == '__main__':
    main()