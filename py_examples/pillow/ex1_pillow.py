from PIL import Image, ImageFilter, ImageDraw, ImageFont
import requests
from io import BytesIO
import sys

path='/Users/srinivasang/code/Experiments/py_examples/pillow/'

def crop_image(input_file, cropped_file) :
    try:
        img = Image.open(input_file)
        #print(img.format, img.size, img.mode,img.palette)
    except IOError:
        print("Unable to load image")
        sys.exit(1)
    #The crop() method takes a 4-tuple defining the left, upper, right, and lower pixel coordinates.
    cropped = img.crop((100, 100, 350, 350))
    cropped.save(cropped_file)

def rotate_image(input_file, rotated_file, angle) :
    try:
        img = Image.open(input_file)
    except IOError:
        print("Unable to load image")
        sys.exit(1)
        
    rotated = img.rotate(angle)
    rotated.save(rotated_file) 

def main() :
    #crop_image(path +'image0.jpg', path +'cropped.jpg')
    #rotate_image(path +'image1.jpg', path +'rotated_90.jpg', 90)
    #rotate_image(path +'image1.jpg', path +'rotated_180.jpg', 180)
    #rotate_image(path +'image1.jpg', path +'rotated_270.jpg', 270)
    #rotate_image(path +'image1.jpg', path +'rotated_360.jpg', 360)

    img = Image.open(path+'image1.jpg')
    width, height = img.size
    print(img.size) 
    new_img = img.resize((256,256))
    new_img.save(path +'resized.jpg')
    print(new_img.size) 

    img = Image.open(path+'image0.jpg')
    try :
        new_img = img.transpose(Image.FLIP_LEFT_RIGHT)
        transpose_img = img.transpose(Image.TRANSPOSE)
    except Exception:
         print("error in transpose process")          
    new_img.save(path +'image_flip_LR.jpg')
    transpose_img.save(path +'image_ftranspose.jpg')

   
    #PIL.Image.ROTATE_90, PIL.Image.ROTATE_180, PIL.Image.ROTATE_270 or PIL.Image.TRANSPOSE

# this means that if this script is executed, then 
# main() will be executed
if __name__ == '__main__':
    main()