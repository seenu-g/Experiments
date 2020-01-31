# on mac machine
# $ virtualenv venv
# $ venv/bin/pip install -U pip
# pip install -U virtualenv

import torch
import numpy as np
from sklearn.datasets import load_boston
def basic_func() :
    x = torch.empty(3, 3)
    print(x)
    print("second column", x[:, 1]) # display second column
    print("second row", x[1, :]) # display second row

    print("cuda is_available: ",torch.cuda.is_available())
    x = torch.zeros(5, 3, dtype=torch.long)
    print(x)

def add() :
    x = torch.tensor([5.5, 3]) #initailize tensor using data
    print("x. size :" , x.size())
    y = torch.tensor([5.5, 3])
    print(x+y)
    result = torch.empty(1, 2)
    torch.add(x, y, out=result)
    print(result)

def load_boston_data() :
    boston = load_boston()
    boston_tensor = torch.from_numpy(boston.data)
    print("boston tensor size :",boston_tensor.size())
    print(boston_tensor[:2])

def tensor_to_numpy() :
    a = torch.ones(5)
    print("Torch value :",a)
    b = a.numpy()
    print("Numpy value :",b)
    a.add_(1) #modifies b too  
    print(a)
    print(b)

def numpy_to_tensor() :
    print ("numpy_to_tensor") 
    a = np.ones(5)
    b = torch.from_numpy(a)
    np.add(a, 1, out=a)
    print(a) # modifies b too
    print(b)
    
def main() :
    #basic_func()
    #add()
    #load_boston_data()
    tensor_to_numpy()
    numpy_to_tensor()
    
# this means that if this script is executed, then 
# main() will be executed
if __name__ == '__main__':
    main()