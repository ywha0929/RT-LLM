
import time
import threading
import csv
import sys
sys.path.insert(1, '../')
from rtllmAPI import *
def request2(index) :
    Helper1 = rtllm("127.0.1.1",10000)
    Helper1.connectToServer()
    Helper1.tryConnectionTest()
    print(Helper1.requestInference('testfile_{}'.format(index),'Explain history of Korea',0,0)," time : ",time.time_ns())
def request1(index) :
    Helper2 = rtllm("127.0.1.1",10000)
    Helper2.connectToServer()
    Helper2.tryConnectionTest()
    print(Helper2.requestInference('testfile_{}'.format(index),'where is capital of Korea?',1,1)," time : ",time.time_ns())
Helper = rtllm("127.0.1.1",10000)
Helper.connectToServer()
Helper.tryConnectionTest()

i = 0
repeat = 2
resultArr = []
while repeat != 0 : 
    Helper.createHistoryFile('testfile_{}'.format(i))
    time.sleep(1)
    Helper.createHistoryFile('testfile_{}'.format(i+1))
    time.sleep(1)
    thread1 = threading.Thread(target=request2,args=(i+1,)) # high priority
    thread2 = threading.Thread(target=request1,args=(i,)) # low priority
    start = time.time_ns()
    thread1.start()
    time.sleep(0.5)
    thread2.start()
    thread1.join()
    thread2.join()
    end = time.time_ns()
    resultArr.append((end-start)/1000000)
    i+=2
    repeat-=1

# with open("nopreemption.csv","w+") as my_csv:
#     csvWriter = csv.writer(my_csv,delimiter=',')
#     csvWriter.writerow(resultArr)