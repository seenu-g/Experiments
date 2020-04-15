import os
from torch.utils.data import Dataset

class TESNamesDataset(Dataset):
    def __init__(self, data_root):
        self.samples = []

        for race in os.listdir(data_root):
            race_folder = os.path.join(data_root, race)

            for gender in os.listdir(race_folder):
                gender_filepath = os.path.join(race_folder, gender)

                with open(gender_filepath, 'r') as gender_file:
                    for name in gender_file.read().splitlines():
                        self.samples.append((race, gender, name))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        return self.samples[idx]

import os

if __name__ == '__main__':
    download_folder = '/Users/srinivasang/code/Experiments/py_examples/torch/dataset/tes-names/'
    if (os.path.isdir(download_folder)==False):
        print(download_folder," does not exist")
    else :    
        dataset = TESNamesDataset(download_folder)
        print(len(dataset))
        for i in range(10) :
            print(dataset[i])