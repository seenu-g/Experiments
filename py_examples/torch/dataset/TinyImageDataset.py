import os
import pandas as pd
from torch.utils.data import Dataset
import numpy as np
from PIL import Image
from torchvision import transforms, utils

def read_val_boxes(fileName) :
       val_boxes_data = pd.read_csv(fileName, delim_whitespace=True, header=None, names=['Images', 'Class', '1', '2', '3', '4'])
       return val_boxes_data
  
def read_val_annotations(fileName) :
        val_annotation_data = pd.read_csv(fileName, delim_whitespace=True, header=None, names=['File', 'Class', '1', '2', '3', '4'])
        return val_annotation_data
    
def get_label_from_name(data, name):
    for row in data.iterrows():       
        if (row['File'] == name):
            return row['Class']  

def get_classes(download_folder):
    classes = []
    wnids = open(os.path.join(download_folder,"wnids.txt"), "r")
    for line in wnids:
        classes.append(line.strip())
    return classes

def load_train_data(download_folder,classes):
    train_data = []
    train_target = []
    train_folder = os.path.join(download_folder,'train')
    for classKey in os.listdir(train_folder):
        class_folder = os.path.join(train_folder, classKey)
        boxes_filepath = os.path.join(class_folder , classKey+'_boxes.txt')
        boxes_records = read_val_boxes(boxes_filepath)
        images_folder = class_folder + '/images/'
        for image_file in os.listdir(images_folder):
            #a = Image.open(images_folder+image_file)
            #npimg = np.asarray(a)
            #if(len(npimg.shape) ==2):
            #  npimg = np.repeat(npimg[:, :, np.newaxis], 3, axis=2)
            #train_data.append(npimg)  
            train_target.append(classes.index(classKey)) 
    return train_data,train_target

def load_val_data(download_folder):
    val_data = []
    val_labels = []
    val_folder = os.path.join(download_folder,'val')
    annotations_filepath = os.path.join(val_folder , 'val_annotations.txt')
    annotations_data = read_val_annotations(annotations_filepath)
    images_folder = val_folder + '/images/'
    for image_file in os.listdir(images_folder):
        #a = Image.open(images_folder+image_file)
        #npimg = np.asarray(a)
        #if(len(npimg.shape) ==2):
        #      npimg = np.repeat(npimg[:, :, np.newaxis], 3, axis=2)
        #val_data.append(npimg)  
        val_labels.append(get_label_from_name(annotations_data, image_file))
    return val_data,val_labels


class TintImageNetTrainDataset(Dataset):
    
    def __init__(self, data_root,classes):
        self.classes = classes
        self.train_data, self.train_target = load_train_data(data_root,classes)

    def __len__(self):
        return len(self.train_data)

    def __getitem__(self, idx):
        data = self.train_data[idx]
        target = self.train_target[idx]
        img = data
        self.transform =  transforms.Compose(
            [   
                transforms.ToTensor(),
                transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
            ])
        img = self.transform(img)
        return img,target
    
class TintImageNetValDataset(Dataset):
 
    def __init__(self, data_root, classes):
        
        self.classes = classes
        self.val_data, self.val_labels = load_val_data(data_root)

    def __len__(self):
        return len(self.val_data)

    def __getitem__(self, idx):
        data = self.val_data[idx]
        target = self.val_labels[idx]
        img = data
        self.transform =  transforms.Compose(
            [   
                transforms.ToTensor(),
                transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
            ])
        img = self.transform(img)
        return img,target
    
if __name__ == '__main__':
    download_folder = '/Users/srinivasang/code/Experiments/py_examples/torch/dataset/tiny-imagenet-200/'
    if (os.path.isdir(download_folder)==False):
        print(download_folder," does not exist")
    else :    
        classes = get_classes(download_folder)
        print(classes)
        ''' dataset = TintImageNetDataset(download_folder,classes)
        print(len(dataset))
        for i in range(10) :
            print(dataset[i])'''
        train_data, train_target = load_train_data(download_folder, classes)
        val_data, val_target = load_val_data(download_folder)


    #print(len(samples))
    #print(samples) 
    #from collections import defaultdict
    #your_dict = defaultdict(lambda : None)
    
