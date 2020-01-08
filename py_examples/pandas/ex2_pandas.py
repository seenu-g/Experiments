
import numpy as np
import pandas as pd

def data_frame_samples():
   my_series = pd.Series({ "India":"New Delhi",
                          "Belgium":"Brussels", 
                          "United Kingdom":"London", 
                          "United States":"Washington"})
   print(pd.DataFrame(my_series))
   
   data = np.array([['','Col1','Col2'],
                   ['Row1',1,2],
                   ['Row2',3,4]])
   print(pd.DataFrame(data=data[1:,1:],
                  index=data[1:,0],
                  columns=data[0,1:]))

   my_2darray = np.array([[1, 2, 3],
                          [4, 5, 6]])
   print(pd.DataFrame(my_2darray))
  
   random = np.random.randn(4,4)	#Create a random sequence with numpy
   dates_m = pd.date_range('20300101', periods=4, freq='M')
   df = pd.DataFrame(data=random,
                     index=dates_m,
                     columns=['Chennai','bangalore','Hyderabad','Pune'])
   print(df)
   print("dimensions of DataFrame", df.shape) # width and the height 
   print(len(df.index)) # len with index gives you the height

def display_df_index():
   random = np.random.randn(4,4)	#Create a random sequence with numpy
   dates_m = pd.date_range('20300101', periods=4, freq='M')
   df = pd.DataFrame(data=random,
                     index=dates_m,
                     columns=['Chennai','bangalore','Hyderabad','Pune'])
   print(df)
   print(df.index) # display datecolumn as index
   
   #.iloc[] works on the positions in your index
   print(df.iloc[0][0])
   print(df.iloc[0][3])
   print(df.iloc[2]) # displays values present in single row coresponding to column
   print(df.iloc[:2]) # displays values present in first 2 rows
   
   # .loc[] works on labels of your index
   # .loc[] will go and look at the values that are at label 
   print()
   print(df.loc['2030-04-30'])
   print(df.loc[df.index[1]])

def main():
    #data_frame_samples()    
    display_df_index()
   
# this means that if this script is executed, then 
# main() will be executed
if __name__ == '__main__':
    main()