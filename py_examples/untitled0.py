# -*- coding: utf-8 -*-
"""
Created on Tue Jan 14 15:56:57 2020

@author: AdminIT
"""

from sklearn.ensemble import RandomForestClassifier

clf = RandomForestClassifier(random_state=0)
X = [[ 1,  2,  3],[11, 12, 13]]
y = [0, 1]  # classes of each sample
clf.fit(X, y)