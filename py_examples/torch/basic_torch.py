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

    x = torch.zeros(5, 3, dtype=torch.long)
    print(x)

def gradient_func() :
    a = torch.ones((2,2), requires_grad=True)
    print(a)
    
    b = a + 5  #added 5 to all the elements of this tensor 
    c = b.mean() #  mean of that tensor
    print(b)
    print(c)
    
    # back propagating
    c.backward() 
    # # computing gradients
    print("Gradient of a",a.grad)

def basic_operations():
    a = torch.zeros((3,3))
    print(a)
    print(a.shape)
    # random.randn() function returns random numbers that follow a standard normal distribution. 
    a = torch.randn(3,3)
    print(a)
    print("type:",type(a))
    # transpose
    b = torch.t(a)
    print("Transpose \n",b)

    print("Add \n", torch.add(a,b))
    print("Sub \n", torch.sub(a,b))
    print("Mul \n", torch.mul(a,b))
    print("Div \n", torch.div(a,b))

def concat() :
    a = torch.tensor([[1,2],[3,4]])
    b = torch.tensor([[5,6],[7,8]])
    # concatenating vertically // add as rows
    row_merge = torch.cat((a,b))
    print(row_merge, row_merge.shape)
    # concatenating horizontally // add as columns
    col_merge = torch.cat((a,b),dim=1)
    print(col_merge,col_merge.shape)

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
    use_cuda = torch.cuda.is_available()
    print("use_cuda = torch.cuda.is_available() :", use_cuda)
    gradient_func()
    #basic_func()
    #basic_operations()
    #concat()
    #add()
    #load_boston_data()
    #tensor_to_numpy()
    #numpy_to_tensor()
    
# this means that if this script is executed, then 
# main() will be executed
if __name__ == '__main__':
    main()