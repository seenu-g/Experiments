# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 14:45:24 2019

@author: g.srinivasan
"""
import matplotlib.pyplot as plt
import numpy as np

def draw_histogram_with_axis_labels() :
    mu, sigma = 100, 15
    x = mu + sigma * np.random.randn(10000)
    # the histogram of the data
    n, bins, patches = plt.hist(x, 50, density=1, facecolor='g', alpha=0.75)

    #plt.xlabel('Smarts')
    #plt.ylabel('Probability')
    #plt.title('Histogram of IQ')
    #matplotlib accepts TeX equation expressions in any text expression
    plt.text(60, .025, r'$\mu=100,\ \sigma=15$') 
    plt.axis([40, 160, 0, 0.03])
    
    plt.grid(True)
    plt.show()
    
def annotate_text() :
    t = np.arange(0.0, 5.0, 0.01)
    s = np.cos(2*np.pi*t)
    line, = plt.plot(t, s, lw=2)
    #plt.annotate('local max', xy=(2, 1), xytext=(3, 1.5),
    #             arrowprops=dict(facecolor='black', shrink=0.05),)
    plt.ylim(-2, 2)
    plt.show()
    
data = {'Naveen': 109438.50,
        'Suraj': 103569.59,
        'Neha': 112214.71,
        'Murugan': 212591.43,
        'Sai': 100934.30,
        'Maran': 103660.54,
        'Renjith': 137351.96,
        'Durena': 143381.38,
        'Poornima': 185841.99,
        'Somona': 104437.60}

def draw_bar_graph() :
    group_data = list(data.values())
    group_names = list(data.keys())
    group_mean = np.mean(group_data)
    
    plt.rcParams.update({'figure.autolayout': True})
    
    fig, ax = plt.subplots()
    ax.barh(group_names, group_data)
    
    # adds vertical line to mark mean
    ax.axvline(group_mean, ls='--', color='r')

    labels = ax.get_xticklabels()
    plt.setp(labels, rotation=45, horizontalalignment='right')
    
def main():
    #draw_histogram_with_axis_labels()
    #annotate_text()
    #draw_bar_graph()
    a=np.arange(60).reshape(3,4,5)
    print(a)

# this means that if this script is executed, then 
# main() will be executed
if __name__ == '__main__':
    main()