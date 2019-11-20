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
    print(article)
    adjective = random.choice(adjectives)
    noun = random.choice(nouns)
    verb = random.choice(verbs)
    the_sentence = article + " " + adjective + " " + noun + " " + verb
    print(the_sentence)

sentence()    
print(random.random())
print(random.randint(3,30))