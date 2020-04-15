from torch.utils.data import Dataset

class NumbersDataset(Dataset):
    def __init__(self, low, high):
        self.samples = list(range(low, high))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        return self.samples[idx]


if __name__ == '__main__':
    dataset = NumbersDataset(2821, 8295)
    print(len(dataset))
    print(dataset[100])
    print(dataset[122:361])