from PIL import Image, ImageFilter, ImageDraw, ImageFont, ImageEnhance
import requests
from io import BytesIO
import sys

path='/Users/srinivasang/code/Experiments/py_examples/pillow/'
# An image can be cropped: that is, a piece can be cut out to create a new image.
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

#An image can be rotated using the rotate() function and passing in the angle for the rotation.
def rotate_image(input_file, rotated_file, angle) :
    try:
        img = Image.open(input_file)
    except IOError:
        print("Unable to load image")
        sys.exit(1)
        
    rotated = img.rotate(angle)
    rotated.save(rotated_file) 

def rotate_image() :
    rotate_image(path+'image1.jpg', path +'rotated_90.jpg', 90)
    rotate_image(path+'image1.jpg', path +'rotated_180.jpg', 180)
    rotate_image(path+'image1.jpg', path +'rotated_270.jpg', 270)
    rotate_image(path+'image1.jpg', path +'rotated_360.jpg', 360)

#It is important to be able to resize images before modeling.
def resize_image(input_file) :
    img = Image.open(input_file)
    width, height = img.size
    print(img.size) 
    new_img = img.resize((256,256))
    new_img.save(path +'resized.jpg')
    print(new_img.size) 

def transpose_image(input) :
    img = Image.open(input)
    try :
        image_flipLR = img.transpose(Image.FLIP_LEFT_RIGHT)
        transpose_img = img.transpose(Image.TRANSPOSE)
    except Exception:
         print("error in transpose process")          
    image_flipLR.save(path +'image_flip_LR.jpg')
    transpose_img.save(path +'image_ftranspose.jpg')
    #PIL.Image.ROTATE_90, PIL.Image.ROTATE_180, PIL.Image.ROTATE_270 or PIL.Image.TRANSPOSE
    flip_imgTB = img.transpose(Image.FLIP_TOP_BOTTOM)
    flip_imgTB.save(path +'image_flip_TB.jpg')
    flip_img90 = img.transpose(Image.ROTATE_90)
    flip_img90.save(path +'image_flip_90.jpg')
    flip_img180 = img.transpose(Image.ROTATE_180)
    flip_img180.save(path +'image_flip_180.jpg')
    flip_img270 = img.transpose(Image.ROTATE_270)
    flip_img270.save(path +'image_flip_270.jpg')

def crop_image(input) :    
    image = Image.open(input)
    cropped = image.crop((100, 100, 200, 200))
    cropped.show()

def main() :
    #crop_image(path +'image0.jpg', path +'cropped.jpg')
    #resize_image(path+'image1.jpg')
    #rotate_image()
    transpose_image(path+'opera_house.jpg')
    crop_image(path+'opera_house.jpg')

    img = Image.open(path+'image0.jpg')
    enh_img = ImageEnhance.Contrast(img)
    enh_img.enhance(1.3).show("30% more contrast")



# this means that if this script is executed, then 
# main() will be executed
if __name__ == '__main__':
    main()