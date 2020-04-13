#merge() is used to combine dataframes on the basis of values of common columns
import pandas as pd

df_a = pd.DataFrame({
        'subject_id': ['1', '2', '3', '4', '5'],
        'first_name': ['Ram', 'Shyam', 'Srini', 'Roshan', 'Aparna'], 
        'last_name': ['V', 'F', 'M', 'S', 'U']})

df_b = pd.DataFrame({
        'subject_id': ['4', '5', '6', '7', '8'],
        'first_name': ['Ram', 'Shyam', 'Srini', 'Roshan', 'Aparna'], 
        'last_name': ['V', 'F', 'M', 'S', 'U']})

df_c = pd.DataFrame({
        'subject_id': ['1', '2', '3', '4', '5', '6','7', '8', '9', '10', '11'],
        'test_id': [51, 15, 15, 61, 16, 14, 15, 1, 61, 16,41]})

df_d = pd.DataFrame({
        'subject_id': ['1', '2', '3', '4', '5','6', '7', '8', '9', '10', '11'],
        'subject_name': ['Tamil','English', 'Math','Eco', 'Science', 'Psychology', 'Physics', 'Biology', 'Design', "Chemistry", 'Hindi']})

print(pd.merge(df_c, df_d, on='subject_id'))
print(pd.merge(df_a, df_c, on='subject_id'))

#Inner join produces only the set of records that match in both Table A and Table B.
print("inner merge")
print(pd.merge(df_a, df_b, on='subject_id', how='inner')) # intersection
#Full outer join produces the set of all records in Table A and Table B, with matching records from both sides where available.
print("outer merge")
print(pd.merge(df_a, df_b, on='subject_id', how='outer')) # union