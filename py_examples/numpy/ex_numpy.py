
import numpy as np
import matplotlib.pyplot as plt
def draw_3_lines() :
    x = np.arange(0., 5., 0.2)
    plt.plot(x, x**4, 'r', x, x*90, 'bs', x, x**3, 'g^')
    #prints 3 lines in different styles: a red line, blue squares, and green triangles
    plt.show()

def draw_curve() :
    x2 = np.arange(0., 5., 0.1)
    plt.subplot(212)
    plt.plot(x2,np.cos(2*np.pi*x2), 'k')
    #print 1 line
    plt.show()

def draw_2D_figure() :
    N = 100
    x = np.random.rand(N)
    y = np.random.rand(N)
    colors = np.random.rand(N)
    #if N was 3, colors can be initialized this way 
    #colors=('r','b','g') 
    #scatter object takes two sequence objects, such as arrays, of the same length and 
    #optional parameters to denote color and style attributes.
    area = np.pi * (10 * np.random.rand(N))**2 # 0 to 10 point radiuses
    plt.scatter(x, y, s=area, c=colors, alpha=0.5)
    plt.show()

def main():
   draw_3_lines()
   draw_curve() 
   draw_2D_figure()
   np.arange(1, 11)
   print (np)
   
# this means that if this script is executed, then 
# main() will be executed
if __name__ == '__main__':
    main()