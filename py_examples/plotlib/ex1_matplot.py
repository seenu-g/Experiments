# Import matplotlib
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.decomposition import PCA as RandomizedPCA

def generate_8_8_images() :
    # Figure size (width, height) in inches
    fig = plt.figure(figsize=(6, 6))
    
    # Adjust the subplots 
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1, hspace=0.05, wspace=0.05)
    
    # For each of the 64 images
    for i in range(64):
        # Initialize the subplots: add a subplot in the grid of 8 by 8, at the i+1-th position
        ax = fig.add_subplot(8, 8, i + 1, xticks=[], yticks=[])
        # Display an image at the i-th position
        ax.imshow(digits.images[i], cmap=plt.cm.binary, interpolation='nearest')
        # Add lable for the image  equal to the target value
        ax.text(0, 7, str(digits.target[i]))
    
    # Show the plot
    plt.show()

def generate_scatterplot () :
    
    # Create a Randomized PCA model that takes two components
    randomized_pca = RandomizedPCA(n_components=2)
    # Fit and transform the data to the model
    reduced_data_pca = randomized_pca.fit_transform(digits.data)

    # Create a regular PCA model 
    pca = PCA(n_components=2)
    # Fit and transform the data to the model
    reduced_data_pca = pca.fit_transform(digits.data)

    colors = ['black', 'blue', 'purple', 'yellow', 'white', 'red', 'lime', 'cyan', 'orange', 'gray']
    for i in range(len(colors)):
        x = reduced_data_pca[:, 0][digits.target == i]
        y = reduced_data_pca[:, 1][digits.target == i]
        plt.scatter(x, y, c=colors[i])
    plt.legend(digits.target_names, bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
    plt.xlabel('First Principal Component')
    plt.ylabel('Second Principal Component')
    plt.title("PCA Scatter Plot")
    plt.show()

def main():
    generate_scatterplot()
    #generate_8_8_images()

# this means that if this script is executed, then 
# main() will be executed
if __name__ == '__main__':
    main()