x = {"apple", "banana", "cherry"}
y = {"google", "microsoft", "apple"}

#The union() method returns a set that contains all items from the original set, and all items from the specified sets.
z = x.union(y) 
print(z)

p = {"1", "b", "3"}
q = {"f", "d", "1"}
r = {"3", "d", "e"}

#You can specify as many sets you want, separated by commas.
#If an item is present in more than one set, the result will contain only one appearance of this item.
result = p.union(q, r) 
print(result)

#The returned set contains only items that exist in both sets, or in all sets if the comparison is done with more than two sets.
i = x.intersection(y) 
print(i)

x = {"a", "b", "c"}
y = {"f", "e", "d", "c", "b", "a"}
#The issubset() method returns True if all items in the set exists in the specified set, otherwise it retuns False.
if x.issubset(y): 
    print("X is subset of Y")
else:
    print("Y is subset of X")
# The issuperset() method returns True if all items in the specified set exists in the original set, otherwise it retuns False.
if y.issuperset(x):
    print("Y is superset of x" )
else:
    print("Y is not superset of X" )



#The returned set contains items that exist only in the first set, and not in both sets.
z = x.difference(y) 
print(z)
x = {"apple", "banana", "cherry"}
y = {"google", "microsoft", "apple"}
z = y.difference(x) 
print(z)
z = x.difference(y) 
print(z)

x = {"apple", "banana", "cherry"}
y = {"google", "microsoft", "apple"}
# isdisjoint() method returns True if none of the items are present in both sets, otherwise it returns False.
# if interestion is empty, it returns true.
if x.isdisjoint(y) is True:  # Do not perform if flag == True:
    z = x.intersection(y)
    print ("X intersection Y", z)
else:
    z = x.intersection(y)
    print ("Disjoint set: X intersection Y", z)