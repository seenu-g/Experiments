# -*- coding: utf-8 -*-
"""
Created on Sat Nov 23 13:25:10 2019

@author: g.srinivasan
"""
phones =[["srinivasan","9945503508"],
             ["Mridula","9980803508"]]
file_name = "phones.csv"
import csv

def load_phone_list():
    in_file = open(file_name,"r+")
    phones = []
    for row in csv.reader(in_file):
        phones.append(row)
        #print (row) # display row
    in_file.close()

def save_phone_list():
    out_file = open(file_name,"w+")
    for item in phones:
       csv.writer(out_file).writerow(item)
    out_file.close()
    
def edit_phone(old_phone_number,new_phone_number):
    index = find_phone(old_phone_number)
    if index >= 0 :
       phone = phones[index]
       phone[1] = new_phone_number
       print ("Changed", old_phone_number," in to ", new_phone_number)
    else:
       print (old_phone_number, " not available ")
def delete_phone(phone_number):
    index = find_phone(phone_number)
    if index >= 0 :
       del phones[index]
       print (phone_number, " deleted")
    else:
       print (phone_number, " not available ")
def find_phone(phone_number):
    if not phone_number.isdigit():
        print (phone_number, "is not a number")
        return -1
    index = 1
    found = 0 
    for phone in phones :
        if phone_number == phone[1] :
            print ("Found", phone_number)
            found = index
            return index -1
    if found == 0:
       print ("Not Found", phone_number)
       return -1
    return -1
def show_phones() :
    index = 1
    if len(phones) ==0 :
        print ("phone list is empty")
    for phone in phones :
        show_phone(phone, index)
        index = index + 1
    print()
    
def show_phone(phone, index) :
    outputstr = "{0:>3} {1:<20} {2:>16}"
    name_pos = 0
    phone_pos = 1
    print(outputstr.format(index,phone[name_pos], phone[phone_pos]))

def create_phone():
    print("Enter data for new phone")
    input_name = input("Enter name : ")
    input_number = input("Enter number : ")
    phone =[input_name, input_number]
    phones.append(phone)
    print()

def command_input():
    print("Choose one of the options")
    print("q- Exit, n - Create, d - delete, e - edit, s - show, f - find")
    choice = input("Choice:")
    if choice.lower() in ['n','d','e','s','q','f']:
         return choice.lower()
    else:
         print(choice +"?" + " invalid option")
         return None

def main_loop():
    load_phone_list()
    
    while True:
        selected_option = command_input()
        if selected_option == None:
            continue
        if selected_option =="q":
            print ("Exit")
            break
        elif selected_option == "n" :
            create_phone()
        elif selected_option =="d" :
            number = input("Enter number to delete:")
            delete_phone(number)
        elif selected_option =="s" :
            show_phones()    
        elif selected_option =="e" :
            old_number = input("Enter old number to edit:")
            new_number = input("Enter new number to edit:")
            edit_phone(old_number,new_number)
        elif selected_option =="f" :
            number = input("Enter number to find:")
            find_phone(number)
        else :
             print("Invalid Choice")
    
    save_phone_list()
    
if __name__ =='__main__':
    main_loop()
    
    
    