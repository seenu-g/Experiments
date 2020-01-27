from PIL import Image, ImageFilter, ImageDraw, ImageFont
import requests
from io import BytesIO

path='/Users/srinivasang/code/Experiments/py_examples/pillow/'

def load_imageURL(imageURL) : 
    try:
        response = requests.get(imageURL)
        img = Image.open(BytesIO(response.content))
        #img.show()# comment this line and image till not be displayed
        print(img.format, img.size, img.mode)
    except IOError:
        print("Unable to load image")    
    return img;

def save_image(img, file_name, file_type) :
    try:
        img.save(file_name, file_type)    
    except IOError:
        print("Unable to save image")  

def load_image(file_name) :
    try:
        img = Image.open(file_name)    
        #img.show()
        print(img.format, img.size, img.mode)
    except IOError:
        print("Unable to open image")  
    return img

def draw_rectangle() :
    img = Image.new('RGBA', (200, 200), 'white')    
    idraw = ImageDraw.Draw(img)
    idraw.rectangle((10, 10, 100, 100), fill='blue')
    idraw.rectangle((110, 110, 120, 120), fill='green')

    img.save(path + 'rectangle.png')
    img.show()

def create_thumbnail_image(input_file) :
    img = load_image(input_file)
    print(img.format, img.size, img.mode,img.palette)
    size = (128, 128)
    try :
        img.thumbnail(size)
    except Exception:
         print("error in thumbnail process")        
    finally:
        save_image(img, path + 'thumbnail.png','png')

def create_watermark_image(input_file) :
    img = load_image(input_file)
    print(img.format, img.size, img.mode)
    try :
        idraw = ImageDraw.Draw(img)
        text = "Learn Python"
        #font = ImageFont.FreeTypeFont
        #idraw.text((10, 10), text, font=font)
        idraw.text((1, 1), text)
    except Exception:
         print("error in watermark process")        
    finally:
        save_image(img, path + 'watermarked.png','png')

def main() :

   #draw_rectangle()

   url_image = load_imageURL('https://i.ytimg.com/vi/vEYsdh6uiS4/maxresdefault.jpg')
   save_file_as = path + 'sid.jpg'
   save_file_type = 'jpeg'    
   save_image(url_image,save_file_as,save_file_type)

   grayscale = url_image.convert('L')
   #grayscale.show()

   img = load_image(save_file_as)
   #With the save() method, we can convert an image to a different format.
   try :
        blurred = img.filter(ImageFilter.BLUR)
        blurred.save(path + 'blurred.png')
   except IOError:
        print("Unable to save image sid.jpg as blurred.png")  

   create_watermark_image(path + 'blurred.png')
   create_thumbnail_image(path + 'blurred.png')

# this means that if this script is executed, then 
# main() will be executed
if __name__ == '__main__':
    main()