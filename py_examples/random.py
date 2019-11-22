# -*- coding: utf-8 -*-
"""
Created on Wed Nov 20 23:17:14 2019

@author: g.srinivasan
"""

import random

verbs =[ "meows", "roars", "barks"]
nouns =["lion", "cat","dog"]
adjectives =["mighty","happy", "young", "cute","matured"]
articles =["The", "A","this", "that"]

def sentence():
    article = random.choice(articles)
    adjective = random.choice(adjectives)
    noun = random.choice(nouns)
    verb = random.choice(verbs)
    the_sentence = article + " " + adjective + " " + noun + " " + verb
    print(the_sentence)

def poem():
    index = 0
    count = 4
    while index <count:
        article = random.choice(articles)
        adjective = random.choice(adjectives)
        noun = random.choice(nouns)
        verb = random.choice(verbs)
        the_sentence = article + " " + adjective + " " + noun + " " + verb
        print(the_sentence)
        index = index + 1

def make_random():
    numbers =[]
    for i in range(0,10):
        numbers.append(random.randint(1,100)) #use random.random() to real numbers
    return numbers

def make_same_random():
    numbers =[]
    random.seed(17)
    for i in range(0,10):
        numbers.append(random.randint(1,100)) #use random.random() to real numbers
    return numbers
    
sentence()
print(random.random())
print(random.randint(3,30))
poem()    

random_integers = make_random()
print("the list of random integers", random_integers)
random_integers = make_random()
print("the list of random integers", random_integers)


random_same = make_same_random()
print("the list of random same", random_same)
random_same = make_same_random()
print("the list of random same", random_same)

list_for_sort = random_integers
print("the list for sorting", list_for_sort)
sorted_list = list_for_sort.sort()
print("the sorted list", list_for_sort)

alpha_list = ['x','a','w','d','p']
print("the provided alpha list", alpha_list)
alpha_list.sort() #alpha_list.sort(key=str.lower)
print("the sorted alpha list", alpha_list)

