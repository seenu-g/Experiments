import os
import requests
from zipfile import ZipFile 
from io import StringIO

def download_images(download_folder,url, fileName):
    if(os.path.isfile(fileName)==False) :
          print ('Downloading ' + url )
          try:
                r = requests.get(url, stream=True)
                with open(fileName,'wb') as f: 
                  f.write(r.content) 
          except :
                print ("Exception to download file",fileName)
                return False
    else:
        print (fileName, " already exists in ",os. getcwd()) 
    
def extract_zipfile(download_folder,fileName):
    
    if (os.path.isdir(download_folder)==False):
        print(download_folder," does not exist")
        return    
    if(os.path.isfile(fileName)==False) :
        print(fileName," from which to extract does not exist")
        return
    
    os.chdir(download_folder)
    extracted_folder = download_folder + fileName.split('.')[0]
    
    if (os.path.isdir(extracted_folder)==True):
        print ('Images seems to be downloaded and extracted already... to',extracted_folder)
        return

    with ZipFile(fileName, 'r') as zip: 
         try:
              #zip.printdir() 
              print('Extracting file ' + fileName + ' now... to ',extracted_folder) 
              zip.extractall() 
              print('File Extraction Done!') 
              return 
         except:
              print ("Exception to Unzip file",fileName)
              return 
          
IMAGES_URL = 'http://cs231n.stanford.edu/tiny-imagenet-200.zip'
fileName = "tiny-imagenet-200.zip"
download_folder = "/Users/srinivasang/code/school_of_ai/chap12/"

#download_images(IMAGES_URL)
extract_zipfile(download_folder,fileName)

