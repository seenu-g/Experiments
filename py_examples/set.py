# A set is a collection which is unordered and unindexed. 
# In Python sets are written with curly brackets.

thisset = {"C++", "NodeJs", "GoLang"}
print(thisset)

for x in thisset:
      print(x)

#Once a set is created, you cannot change its items, but you can add new items.

thisset.add("Rust")
print(thisset)
thisset.update(["solidity", "Ruby", "SmallTalk"])
print(thisset)

thisset.remove("SmallTalk")
print(thisset)

if "SmallTalk" in thisset:
      print("Yes, 'SmallTalk' is in the list")
else:
      print("No, 'SmallTalk' is not in the list")

