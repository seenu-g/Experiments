thisdict =	{
  "brand": "Ford",
  "model": "Mustang",
  "year": 1964
}
print(thisdict)

x = thisdict["model"]
print(x)
x = thisdict.get("brand")
print(x)
thisdict["year"] = 2018

print("count of elements in the dictionary", len(thisdict))

for x in thisdict:
      print(x,thisdict[x])

thisdict["color"] = "red"
for x in thisdict.values():
      print(x)

if "year" in thisdict:
      print("Yes, 'year' is key in thisdict dictionary")

thisdict["brand"] = "Honda"
thisdict.update({"model": "Jazz"})
thisdict.update({"color": "White"})
for x, y in thisdict.items():
      print(x, y)

try:
    del thisdict["model"]
    print(len(thisdict))
    print(thisdict)
    del thisdict
    print(thisdict)
except:
    print("Exception shown as the program tried to print empty dictionary")
