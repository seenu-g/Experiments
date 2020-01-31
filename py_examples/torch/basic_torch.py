# on mac machine
# $ virtualenv venv
# $ venv/bin/pip install -U pip
# pip install -U virtualenv

import torch
import numpy as np
from sklearn.datasets import load_boston

x = torch.empty(3, 3)
print(x)
print(torch.cuda.is_available())

boston = load_boston()
boston_tensor = torch.from_numpy(boston.data)
boston_tensor.size()
print(boston_tensor[:2])