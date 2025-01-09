
from AnACor import preprocess_lite
from AnACor import mp_lite
import pdb
import os
import sys
import inspect

def run():
    preprocess_lite.main()
    #then here we have the gui
    # select the dataset, and they will create the yaml file and the correspond log file 
    # run mp_lite in a for loop
    mp_lite.main()
    

if __name__ == '__main__' :
    main( )

