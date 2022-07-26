import os 
import sys
max_i = int(sys.argv[1])
test = sys.argv[2]

i = 0 

while i < max_i: 
    os.system("python2 simulator.py {} {} {}".format(i, i + 1, test))
    i += 1