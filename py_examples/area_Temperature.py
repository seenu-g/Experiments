def areatriangle(b,h):
    area = .5*b*h
    print("The area of a triangle of breadth", b,"and height", h,"is", area)

def areacircle(radius):
    """ Computes the area of a circle of the given radius """
    area = 3.14*radius**2
    print("The area of a circle of radius",radius,"is", area)

def name():
    """ Input first and last name, combine to one string and print """
    fname = input("Enter your first name: ")
    lname = input("Enter your last name: ")
    fullname = fname + " " + lname

    print("Your name is:", fullname)

def area(type_, x):
    if type_ == "circle":
        area = 3.14*x**2
        print("Area of ",type_," is ", area)
    elif type_ == "square":
        area = x**2
        print("Area of ",type_," is ", area)
    else:
        print("I don't know that structure ",type_," to calculate area.")

def fahrenheit_to_celsius(): 
    temp_str = input("Enter a Fahrentheit temperature: ")
    if temp_str:
        if temp_str.isdigit():  
            temp = int(temp_str)
            newTemp = 5*(temp-32)/9
            print("The Fahrenheit temperature",temp,"is equivalent to ",end='')
            print(newTemp,"degrees Celsius")
        else:
            print("You must enter a number. Bye")  
    else:
            print("Empty. You did not enter a value. Bye") 

def celsius_to_fahrenheit(): 
    temp_str = input("Enter a celsius temperature: ")
    if temp_str:
        if temp_str.isdigit():  
            temp = int(temp_str)
            newTemp = (9/5 * temp) + 32
            print("The celsius temperature",temp,"is equivalent to ",end='')
            print(newTemp,"degrees Fahrenheit")
        else:
            print("You must enter a number. Bye")  
    else:
            print("Empty. You did not enter a value. Bye") 
            
def inches_to_feet(inches):
    extra_inches = inches % 12  # division by integer with fraction thrown away
    feet = (inches - extra_inches)/12
    print(inches," inches = ",feet," feet and ",extra_inches,"inches") 

def countdown():
   # for ct in range(10,0,-1):
   #     print("\n",ct,end=' ')
   # print("\n BLASTOFF")
    
    ct =10
    while ct >0:
        print("\n",ct,end=' ')
        ct = ct -1
    print("\n BLASTOFF")
    
"""
#%%
def forever():
    while True:
        pass
#%%
"""

"""
areatriangle(10,5)
areacircle(10)
area("circle", 10)
area("square", 10)
area("rectangle", 10)
fahrenheit_to_celsius() 
inches_to_feet(125)

"""
countdown()
celsius_to_fahrenheit()