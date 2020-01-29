import threading 
import os
  
def print_cube(num): 
    print("Cube: {}".format(num * num * num)) 
  
def print_square(num): 
    print("Square: {}".format(num * num)) 

def task1(): 
    print("Task 1 assigned to : {}".format(threading.current_thread().name)) 
    print("ProcessID running task 1: {}".format(os.getpid())) 
  
def task2(): 
    print("Task 2 assigned to thread: {}".format(threading.current_thread().name)) 
    print("ProcessID running task 2: {}".format(os.getpid())) 
  

def main() :
    print("Main thread name: {}".format(threading.main_thread().name)) 

    # creating thread 
    t1 = threading.Thread(target=print_square, args=(10,)) 
    t2 = threading.Thread(target=print_cube, args=(10,)) 
  
    t1.start() 
    t2.start() 
  
    t1.join() #wait until thread 1 is completely executed 
    t2.join() 
    print("Done!")

    th1 = threading.Thread(target=task1, name='th1')
    th2 = threading.Thread(target=task2, name='th2')   
  
    th1.start() 
    th2.start()  

if __name__ == "__main__": 
    main()