def my_function():
      print("Hello from a function")

my_function()

def my_message(fname="Srinivasan"):
      print(fname + " Refresh")

my_message("Mridula")
my_message("Mrinalini")
my_message()

def my_add(x,y):
    return y + x

def my_mult(x,y):
    return y * x
def my_dvision(x,y):
    return y / x

my1 = myfunc(1)
my2 = myfunc(2)
my3 = myfunc(3)
my4 = myfunc(4)
my5 = myfunc(5)
my6 = myfunc(6)
my7 = myfunc(7)
my8 = myfunc(8)
my9 = myfunc(9)
my10 = myfunc(10)

def multiply_table1(n):
    print("1 * "+ str(n) + " = " + str(my1(n)))
    print("2 * "+ str(n) + " = " + str(my2(n)))
    print("3 * "+ str(n) + " = " + str(my3(n)))
    print("4 * "+ str(n) + " = " + str(my4(n)))
    print("5 * "+ str(n) + " = " + str(my5(n)))
    print("6 * "+ str(n) + " = " + str(my6(n)))
    print("7 * "+ str(n) + " = " + str(my7(n)))
    print("8 * "+ str(n) + " = " + str(my8(n)))
    print("9 * "+ str(n) + " = " + str(my9(n)))
    print("10 * "+ str(n) + " = " + str(my10(n)))

def multiply_table(n):
    for x in range(11):
        print(str(x) +" * "+ str(n) + " = " + str(my_mult(x,n)))

def factorial(n):
    if n == 0:
        return 1
    else:
        recurse = factorial(n-1)
        result = n * recurse
        return result

import math
def distance(x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    dsquared = dx**2 + dy**2
    result = math.sqrt(dsquared)
    return result

def fibonacci (n):
    if n == 0 or n == 1:
        return 1
    else:
        return fibonacci(n-1) + fibonacci(n-2)

def log_to_base(n, base_number):
    return math.log(n)/math.log(base_number)

def printMultTable(n, maxVal):
    i = 1
    print("Table ", n)
    print("-----------")
    while i <= maxVal:
        print (n*i, '\t',)
        i = i + 1
    print("-----------")

def printMultTables(upTo):
    i = 1
    while i <= upTo:
        printMultTable(i, 10)
        i = i + 1
    
#The power of lambda is better shown when you use them as an anonymous function inside another function.
def myfunc(n):
      return lambda a : a * n

def main():
#A lambda function is a small anonymous function.
#A lambda function can take any number of arguments, but can only have one expression.
#The expression is executed and the result is returned:
    x = lambda a : a + 10
    print(x(5))
    x = lambda a, b : a * b
    print(x(5, 6))
    x = lambda a, b, c : a * b * c
    print(x(5, 6, 2))
    
    #multiply_table(11)
    #multiply_table(16) 
    print("3+5 = ",my_add(3,5))
    print("25 *25 = ",my_mult(25,25))
    print("500/25 = ",my_dvision(25,500))
    print("factorial of 5 is ", factorial(5))
    print ("Distance between(2,4) and (7,9) is",distance(2,4,7,9))
    print("log_to_base(8,2) ",log_to_base(8,2))
    print("log_to_base(81,3 ",log_to_base(81,3))
    print("20th fibonacci value :", fibonacci(20))
    printMultTables(8)

# this means that if this script is executed, then 
# main() will be executed
if __name__ == '__main__':
    main()