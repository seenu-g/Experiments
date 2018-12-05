import datetime
class student:
        def __init__(self, roll, name):
                self.r = roll
                self.n = name
               # print ((self.n)) 
                 
stud1 = student(1, "Alex")
stud2 = student(2, "Karlos")

print ("Data successfully stored in variables")


future_date = datetime.datetime(2020, 5, 17)
print(future_date)

x = datetime.datetime.now()
print(x)
print("Month: " +x.strftime("%B"))
print(x.year)
print("Weekday : " +x.strftime("%A"))
print("Hour : "  + x.strftime("%H"))

