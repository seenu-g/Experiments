from PIL import Image, ImageFilter, ImageDraw, ImageFont, ImageEnhance
import requests
from io import BytesIO
import sys

path='/Users/srinivasang/code/Experiments/py_examples/pillow/'
# An image can consist of one or more bands of data.
# For example, a PNG image might have ‘R’, ‘G’, ‘B’, and ‘A’ bands for the red, green, blue, and alpha transparency values. 
# Many operations act on each band separately, e.g., histograms. 
# It is often useful to think of each pixel as having one value per band.

#the paste method can also take a transparency mask as an optional argument. 
#value 255 indicates that the pasted image is opaque in that position (that is, the pasted image should be used as is). 
#value 0 means that the pasted image is completely transparent.
def copy_paste_img(input) :

    box = (100, 100, 400, 400)
    im = Image.open(input)
    region = im.crop(box)
    region = region.transpose(Image.ROTATE_180)
    im.paste(region, box)
    im.show()

    r, g, b = im.split()
    im = Image.merge("RGB", (b, g, r))
    im.show()

def main() :
   copy_paste_img(path+'opera_house.jpg')


# this means that if this script is executed, then 
# main() will be executed
if __name__ == '__main__':
    main()