from PIL import Image
from numpy import asarray

from matplotlib import image
from matplotlib import pyplot
import os

path='/Users/srinivasang/code/Experiments/py_examples/pillow/'

# using Matplotlib library
# imread() function that loads the image an array of pixels directly 
# and the imshow() function that will display an array of pixels as an image.
# load image as pixel array
def show_image_matplot() :
    data = image.imread(path+'opera_house.jpg')
    print(data.dtype,data.shape)
    # display the array of pixels as an image
    pyplot.imshow(data)
    pyplot.show()

def pillow_numpy() :
    image = Image.open(path+'opera_house.jpg')
    print(image.format,image.mode,image.size) #Format is printed as JPEG
    # loads the photo as a Pillow Image object and converts it to a NumPy array
    data = asarray(image)
    print("shape :", data.shape)

    #then converts it back to an Image object again(create Pillow image)
    image2 = Image.fromarray(data)
    print(image2.format,image2.mode,image2.size) #Format is printed as None
    image2.show()

# load all images in a directory
def load_images() :
    loaded_images = list()
    cwd = os.getcwd() + '/pillow'
    print(cwd + "\n")
    loaded_images = list()

    for filename in os.listdir(cwd) :
        if filename.endswith('.jpg') :
	         img_data = image.imread(path + filename)
	         loaded_images.append(img_data)
	         print('> loaded %s %s' % (filename, img_data.shape))

def main() :
    #show_image_matplot()
    #pillow_numpy()
    load_images()
# this means that if this script is executed, then 
# main() will be executed
if __name__ == '__main__':
    main()