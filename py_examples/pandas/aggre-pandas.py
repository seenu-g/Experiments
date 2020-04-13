import pandas as pd
import numpy as np
def simple_func() :
    # read the dataset
    df = pd.read_csv('data.csv')
    #print(df)
    gp = df.groupby('Embarked')
    print(gp.first())
    gp = df.groupby('Age')
    print(gp.first())
    gp = df.groupby('Sex')
    print(gp.first())
    print(gp.Fare.mean())

df = pd.read_csv('big_data.csv')

gp_item_type = df.groupby('Item_Type')
print(gp_item_type.first())
print("Mean MPR grouped by Item type \n",gp_item_type.Item_MRP.mean())

#group on multiple columns
gp = df.groupby(['Item_Type','Item_Fat_Content'])
print(gp.first())
gp = df.groupby(['Item_Fat_Content','Item_Type'])
print(gp.first())

gp_location_type = df.groupby('Outlet_Location_Type')
print(gp_location_type.first())

gp_outlet_size = df.groupby('Outlet_Size')
print(gp_outlet_size.first())

gp_outlet_type = df.groupby('Outlet_Type')
print(gp_outlet_type.first())

gp_outlet_type_tier = pd.crosstab(df["Outlet_Type"],df["Outlet_Location_Type"],margins=True)
gp_outlet_type_tier.sum(axis=1)
gp_outlet_type_tier.sum(axis=0)
print (gp_outlet_type_tier)

gp_outlet_size_tier = pd.crosstab(df["Outlet_Size"],df["Outlet_Location_Type"],margins=True)
gp_outlet_size_tier.sum(axis=1)
gp_outlet_size_tier.sum(axis=0)
print (gp_outlet_size_tier)

print(pd.pivot_table(df, index=['Outlet_Establishment_Year'], values= "Item_Outlet_Sales"))
print(pd.pivot_table(df, index=['Outlet_Location_Type'], values= "Item_Outlet_Sales"))

print(pd.pivot_table(df, index=['Outlet_Establishment_Year', 'Outlet_Location_Type', 'Outlet_Size'], values= "Item_Outlet_Sales"))
print(pd.pivot_table(df, index=['Outlet_Establishment_Year', 'Outlet_Location_Type', 'Outlet_Size','Outlet_Type'], values= "Item_Outlet_Sales"))