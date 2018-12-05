#Tuple is a collection which is ordered and unchangeable. Allows duplicate members.
thistuple = ("apple", "banana", "cherry")
print(thistuple)

thattuple = tuple(("honda", "maruti", "hyundai")) 
print("tuple created using constructor ", thattuple)

print("Count : ",len(thistuple))
for x in thistuple:
      print(x)

if "cherry" in thistuple:
      print("Yes, 'cherry' is in the fruits tuple")
index = 2
print ("Item at index 2 : ",thistuple[2])
try:
    thistuple[1] = "blackcurrant"
    print(thistuple)
except:
    print("Exception shown as the program tried to modify tuple element")

try:
    del thattuple
    print(thattuple) 
except:
    print("You can delete tuple. Exception shown as the program printed deleted tuple")


