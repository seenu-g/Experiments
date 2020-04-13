import pandas as pd
import numpy as np

def simple_func(data_frame) :
    # drop the null values
    data_frame = data_frame.dropna(how="any")
    # reset index after dropping
    data_frame = data_frame.reset_index(drop=True)
    # view the top results
    print(df.head())

    print("data_frame.apply(lambda x: x[0])")
    print(data_frame.apply(lambda x: x[0])) ##access first row

    print(data_frame.apply(lambda x: x, axis=1)) #access column wise
    print(data_frame.apply(lambda x: x[9], axis=1)) # access ninth column
    print(data_frame.apply(lambda x: x["Name"], axis=1))

def top_price(value):
    if value > 50 :
        value = 50
    return value

def label_encode(sex):
    if sex == 'male':
        label = 'M'
    elif sex == 'female':
        label = 'F'
    else:
        label = 'None'
    return label

# read the dataset
df = pd.read_csv('data.csv')

#simple_func(df)

print ("\nApply top price \n")
#top_tickets = df["Fare"].apply(lambda x: top_price(x))[:5] # print 5 rows
top_tickets = df["Fare"].apply(lambda x: top_price(x)) # print all rows
print(top_tickets)

encoded_values = df["Sex"].apply(lambda x: label_encode(x))
print(encoded_values)




