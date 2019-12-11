# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 17:07:10 2019

@author: g.srinivasan
"""

class MyClass:
    variable = "class variable"

    def function(self):
        print("This is a message inside the class.")

class Education:
    degree = "degree"
    institution = "institution"
    year_of_passing ="year"
    def __init__(self, degree, institution,year):
        self.degree = degree
        self.institution = institution
        self.year_of_passing = year
        
class Employee:
    company_name   = "World"
    position       = "Human"
    educations     = []
    def __init__(self, name, number,salary):
        self.name = name
        self.number = number
        self.salary = salary
    def setEducation(self,degree, institution, year):
        self.educations.append(Education(degree, institution, year))
    def printEmployee(self):
        print (str(self.name) + ', ' + str(self.salary),sep =' ')
        for item in self.educations :
            print(item.degree, item.institution, item.year_of_passing,sep =' ')      
    def instance(self):
        return self

def printEmployee(p):
        print (str(p.name) + ', ' + str(p.salary),sep =' ')
        
def sameEmployee(p1, p2) :
       return (p1.name == p2.name) and (p1.number == p2.number)    

def main():
     e1 = Employee("Ram",1,1000)  
     e1.setEducation("Masters","CEG",1998)
     e2 = Employee("Rahim",2,1000)  
     e2.setEducation("Bachelors","BE",1999)
     print(e1.printEmployee())
     print(printEmployee(e2.instance()))

     print(e2.company_name) #insitalized to class variable
     e1.company_name = "Village" #variable in specific instance changed
     print(e1.company_name,e2.company_name)

     print("SameEmployee e1,e2 :",sameEmployee(e1,e2))
     print("SameEmployee e1,e1 :",sameEmployee(e1,e1))

     myobjectx = MyClass()
     print(myobjectx.variable)
     myobjectx.variable = "Programming"
     print(myobjectx.variable)
     myobjectx.function()

if __name__ =='__main__':
    main()