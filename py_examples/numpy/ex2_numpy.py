
import numpy as np
def arrange() :
    arr1 = np.arange(1, 11) #arrnage from start to stop separated by default step(1) 
    print (arr1)
    b= np.arange(1, 14, 4)	# to change default step, add 3rd paramter.		
    print(b)
    b1 = np.linspace(1, 14, 5, 9)
    print(b1)
    print("minimum ",np.min(arr1))
    print("maximum ",np.max(arr1))
    print("mean ",np.mean(arr1))
    print("median ",np.median(arr1))
    print("std ",np.std(arr1))
    
def ones_zeroes() :
    #display 10 zeros in 1 row
    c= np.zeros((10))
    print(c)    
    #display 5 rows of 3 zeros
    c= np.zeros((5, 3))
    print(c)    
    d = np.ones((1,2,3), dtype=np.int16)			
    print(d)    
    d = np.ones((2,2,3), dtype=np.float32)			
    print(d)

def reshape() :
    original  = np.array([(1,2,3), (4,5,6),(7,8,9),(10,11,12)]) # (4,3) shape
    print("before reshape")
    print(original)
    new = original.reshape(3,4)
    print("after reshape")
    print(new)
    print("second row: ",new[1]) #print second row
    print("third column: ", new[:,2])	#print 3rd column
    print("2nd row, 3rd column ", new[1,2])		
    print("values of 2 row, up to 3rd column", new[2, :3])			


def play_matrix() :
    A = np.matrix(np.ones((4,4)))
    # You canot change the value in matrix
    np.array(A)[2]=2
    print(A)
    # you create new matric with change as follows. 
    np.asarray(A)[3,3]=2
    # np.asarray(A)[3]=2 // will change entire 3rd row to 2
    print(A)

def matrix_multiply() :
    first = np.array([1,2,3])
    second = np.array([4,5,6])
    ### 1*4+2*5
    result = np.dot(first, second)
    
    try :
        a = np.array([(1,2,3), (4,5,6)])  # 2 *3 matrix
        b = np.array([(7,8,9), (10,11,12)]) # 2 *3 matrix
        result = np.dot(a, b)
    except ValueError :
        print(" raise valueError when we multiply 2 * 3 matrix with 2 * 3 matrix")
    
    a1 = np.array([(1,2,3), (4,5,6)])  # 2 *3 matrix
    b1 = np.array([(7,8),(9,10),(11,12)]) # 3 *2 matrix
    result = np.dot(a1, b1)
    print(result)
    
    a2 = np.array([(1,2,3), (4,5,6)])  # 2 *3 matrix
    b2 = np.array([(7,8),(9,10),(11,12)]) # 3 *2 matrix
    np.matmul(a2, b2, result)
    print(result)

def main():
    matrix_multiply()
    #arrange()
    #play_matrix()
    #reshape()

# this means that if this script is executed, then 
# main() will be executed
if __name__ == '__main__':
    main()
