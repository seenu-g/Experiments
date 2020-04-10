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

student_marks = {
      "Srini":{
      "Maths": 66,
      "Science": 65,
      "Social": 76,
      "English":88
      },
      "Guru":{
      "Maths": 96,
      "Science": 95,
      "Social": 86,
      "English":88
      },
      "Balaji":{
      "Maths": 96,
      "Science": 95,
      "Social": 96,
      "English":98
      }
}
student_marks["GN"] = {
      "Maths": 96,
      "Science": 55,
      "Social": 78,
      "English":98
      }
student_marks.update({
      "Haritha":{
      "Maths": 96,
      "Science": 95,
      "Social": 86,
      "English":88
      },
      "Yamini":{
      "Maths": 96,
      "Science": 95,
      "Social": 96,
      "English":98
      }
})
print("Marks of Balaji",student_marks["Balaji"])

print("\n",student_marks)
del student_marks["Srini"]
print("\n After deletion",student_marks)

print("\n marks in Science")
for name in student_marks:
      print(name,(student_marks[name])["Science"])