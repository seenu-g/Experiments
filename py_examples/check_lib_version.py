# -*- coding: utf-8 -*-
"""
Created on Wed Nov 27 18:14:05 2019

@author: g.srinivasan
"""

import sys
import scipy
import numpy
import matplotlib
import pandas
import sklearn
# Runs in spyder
def main():
    print('Python: {}'.format(sys.version))
    print('scipy: {}'.format(scipy.__version__))
    print('numpy: {}'.format(numpy.__version__))
    print('matplotlib: {}'.format(matplotlib.__version__))
    print('pandas: {}'.format(pandas.__version__))
    print('sklearn: {}'.format(sklearn.__version__))

# this means that if this script is executed, then 
# main() will be executed
if __name__ == '__main__':
    main()