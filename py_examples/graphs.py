
import matplotlib.pyplot as plt
def draw_line_graph():
    plt.plot([1, 2, 3, 4])
    # assume sequence of y values
    plt.plot([1, 2, 3, 4], [1, 3, 6, 9]) 
    # assume sequence of s values and y val
    plt.plot([1, 2, 3, 4], [1, 4, 9, 16], 'g^')
    plt.ylabel('some numbers')
    plt.show()

def draw_rectangle() :
    # bottom left hand corner, length, breath
    rectangle = plt.Rectangle((10, 10), 100, 100, fc='r')
    plt.gca().add_patch(rectangle)
    plt.show()
    
def draw_bar_graph():
    names = ['male', 'female', 'transgender']
    values = [20, 10, 5]
    plt.figure(figsize=(9, 3))
    plt.subplot(131)
    plt.bar(names, values)
    plt.title("Persons VS Count")
    plt.show()
def draw_multiple_bar_graph():

    plt.figure(figsize=(9, 3))
    plt.suptitle('Categorical Plotting')    
    #draw bar grpahs
    names = ['male', 'female', 'transgender']
    values = [20, 10, 5]
    plt.subplot(131)
    plt.bar(names, values)
    plt.title("Persons VS Count")
    # plot dots
    names1 = ['Chennai', 'Bangalore', 'Mumbai']
    cities = [20, 10, 5]
    plt.subplot(132)
    plt.scatter(names1, cities)
    plt.title("Persons VS Cities")

    # draw line graph
    names2 = ['Chennai', 'Bangalore', 'Mumbai']
    stretches = [60, 50, 55]
    plt.subplot(133)
    plt.plot(names2, stretches)
    plt.title("Cities VS stretches")
    
    plt.show()

def draw_axes_circle() :
    plt.axes()
    # circle center coordinates, radius
    circle = plt.Circle((0, 0), radius=0.75, fc='y')
    plt.gca().add_patch(circle)
    
    plt.axis('scaled')
    plt.show()

def draw_circle():
    plt.axes()
    circle = plt.Circle((5, 5), radius=2.5, fc='g')
    plt.gca().add_patch(circle)
    plt.axis('scaled')
    plt.show()

