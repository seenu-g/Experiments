def average(list):
   total = 0
   for x in range(len(list)):
       total = total + x
   average = total/len(list)
   print("Average of list", list, "with", len(list),"elements is", average)
  
def printList(list):
    for item in list:
        print(item)
        
def print_employee(employee_list):
    print("Employee No,  Employee Name")
    total_salary = 0
    for employee in employee_list:
        print(employee[1],employee[0],employee[2])
        total_salary = total_salary + int(employee[2])
    print("Total salary of employees :", total_salary)

def print_employee2(employee_list):
    print("Employee No  Employee Name Salary")
    total_salary = 0
    for index in range(0,len(employee_list)):
        print(employee_list[index][1],employee_list[index][0],employee_list[index][2])
        total_salary = total_salary + int(employee_list[index][2])

    print("Total salary of employees :", total_salary)
    
# List is a collection which is ordered and changeable. Allows duplicate members.
thislist = ["apple", "banana", "cherry"]
thislist.append("orange")
print(thislist)

thatlist = list(("Ray", "Eric", "Steve"))
print("list created using constructor ",thatlist)

thislist.insert(1, "guava")
print(thislist)

thislist.reverse()
print("reversed list: ", thislist)

thislist.sort()
print("sorted list: ", thislist)

thislist.sort(reverse=True)
print("sort list in reverse: ", thislist)

if "apple" in thislist:
      print("Yes, 'apple' is in the fruits list")

if "brinjal" not in thislist: 
      print("Yes, 'brinjal' is not in the fruits list")

print("Count : ",len(thislist))

popfruit = thislist.pop()
print("Did a pop: ",thislist)

thislist.remove("banana")
print(thislist)

thislist.insert(1, "avacado")
print(thislist)


thatlist = range(5,125,10)
for x in range(len(thatlist)):
    print (thatlist[x])
print(*thatlist)
average(thatlist)
printList(thatlist)
#thatlist.reverse()
#print("reversed list: ",thatlist)
#thatlist.sort()
#print("sorted list: ",thatlist)
#thatlist.sort(reverse=True)
#print("sort list in reverse: ", thatlist)

del thislist[0]
try:
    del thislist
    print(thislist)
except:
    print("Exception shown as the program tried to print empty list")
    
employees =[["Suraj",1,20000],["Naveen",2,20000],["Neha",3,20000],["Meghna",4,20000]]
#print_employee(employees)
print_employee2(employees)