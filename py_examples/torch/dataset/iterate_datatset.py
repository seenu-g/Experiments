import os
import torch
import pandas as pd
from skimage import io, transform
import numpy as np
import matplotlib.pyplot as plt
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, utils
from FaceLandmarksDataset import FaceLandmarksDataset
from transform_image import Rescale,RandomCrop,ToTensor

# Helper function to show a batch
def show_landmarks_batch(sample_batched):
    """Show image with landmarks for a batch of samples."""
    images_batch, landmarks_batch = sample_batched['image'], sample_batched['landmarks']
    batch_size = len(images_batch)
    im_size = images_batch.size(2)
    grid_border_size = 2

    grid = utils.make_grid(images_batch)
    plt.imshow(grid.numpy().transpose((1, 2, 0)))

    for i in range(batch_size):
        plt.scatter(landmarks_batch[i, :, 0].numpy() + i * im_size + (i + 1) * grid_border_size,
                    landmarks_batch[i, :, 1].numpy() + grid_border_size,
                    s=10, marker='.', c='r')

        plt.title('Batch from dataloader')

    
if __name__ == "__main__":
    transformed_face_dataset = FaceLandmarksDataset(csv_file='faces/face_landmarks.csv',
                                            root_dir='faces/',
                                            transform=transforms.Compose([
                                                Rescale(256),
                                                RandomCrop(224),
                                                ToTensor()
                                            ]))

    for i in range(len(transformed_face_dataset)):
        sample = transformed_face_dataset[i]
        print(i, sample['image'].size(), sample['landmarks'].size())
        if i == 3:
            break
        
    dataloader = DataLoader(transformed_face_dataset, batch_size=4,shuffle=True, num_workers=4)
    for i_batch, sample_batched in enumerate(dataloader):
        print(i_batch, sample_batched['image'].size(),sample_batched['landmarks'].size())

        # observe 4th batch and stop.
        if i_batch == 3:
            plt.figure()
            show_landmarks_batch(sample_batched)
            plt.axis('off')
            plt.ioff()
            plt.show()
            break

'''data_transform = transforms.Compose([
        transforms.RandomSizedCrop(224),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225])
    ])
    hymenoptera_dataset = datasets.ImageFolder(root='hymenoptera_data/train',transform=data_transform)
    dataset_loader = torch.utils.data.DataLoader(hymenoptera_dataset,batch_size=4, shuffle=True,num_workers=4)
    '''
