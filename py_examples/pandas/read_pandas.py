import pandas as pd 

df = pd.read_csv('data.csv')
#print(df.head)

df = pd.read_excel('data.xlsx')
print(df.head(20)) #prints first 20 rows
#print(df.tail(20)) # prints last 20 rows

print('size',df.size)
print('shape',df.shape)

print(df.columns) #displays all columns rames
#print(df["Name"]) # displays one column
#print(df[["Name","Age","Fare"]]) #pass column name as list to display multiple columns

print(df.iloc[:5]) #display 5 rows
print(df.iloc[:-2]) #display all rows other than last 2 rows
print(df.iloc[:,:2]) # display 2 columns of all rows
print(df.iloc[:,:-2]) #display all rows other than last 2 columns

print(df[df['Sex']=='male'])
print(df[df['Sex']=='female']) #display rows that has Sex value as female

print(df[-3:]) # display last 3 rows
print(df[['Fare' ,'Cabin', 'Embarked']]) # display last 3 columns
print((df[-10:]).iloc[:,:2]) # display last 10 rows and first 2 columns

sorted_values = df.sort_values(by=['Age','Sex','Fare'],ascending=False,inplace=False)
print(sorted_values)

print(print(sorted_values.sort_index()))