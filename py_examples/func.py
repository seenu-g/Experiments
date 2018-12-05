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
print("3+5 = ",my_add(3,5))

def my_mult(x,y):
    return y * x
def my_dvision(x,y):
    return y / x

print("25 *25 = ",my_mult(25,25))
print("500/25 = ",my_dvision(25,500))

#A lambda function is a small anonymous function.
#A lambda function can take any number of arguments, but can only have one expression.
#The expression is executed and the result is returned:
x = lambda a : a + 10
print(x(5))
x = lambda a, b : a * b
print(x(5, 6))
x = lambda a, b, c : a * b * c
print(x(5, 6, 2))

#The power of lambda is better shown when you use them as an anonymous function inside another function.

def myfunc(n):
      return lambda a : a * n

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

multiply_table(11)
multiply_table(16)

