import sys
sys.path.insert(1, '../')
from rtllmAPI import *
import time
import threading
HelperList = []
def inference(helperIndex,sessionName,input,requestID,priority):
    start = time.time_ns()
    # print('requestID : {} - Priority : {}'.format(sessionName,priority))
    HelperList[helperIndex].requestInference(sessionName,input,requestID,priority)
    end = time.time_ns()
    print('requestID : {} - Priority : {} - time : {}'.format(sessionName,priority,(end-start)/1000000))

def HighInference() :
    for i in range(0,100):
        inference(i,'test_{}'.format(i),highPriorityInput,i,rtllmPriorityMode.HIGH)

def MidInference() :
    for i in range (110,130):
        inference(i,'test_{}'.format(i),midPriorityInput,i,rtllmPriorityMode.MID)

def LowInference() :
    for i in range(100,110):
        inference(i,'test_{}'.format(i),lowPriorityInput,i,rtllmPriorityMode.LOW)


for i in range(130) :
    Helper = rtllm("127.0.1.1",10000)
    Helper.connectToServer()
    Helper.tryConnectionTest()
    Helper.createHistoryFile('test_{}'.format(i),i)
    HelperList.append(Helper)

time.sleep(10)


highPriorityInput = 'Where is capital of Korea?'
midPriorityInput = 'Explain capitals of United States'
lowPriorityInput = 'Explain History of Korea'

print('--------------------start--------------------')
HighInference()
LowInference()
MidInference()


# for i in range(110):
#     if i % 10 == 9: 
#         threading.Thread(target=inference,args=(i,'test_{}'.format(i),
#                                                                  highPriorityInput,
#                                                                  (i),rtllmPriorityMode.HIGH)).start()
        
#     else :
#         threading.Thread(target=inference,args=(i,'test_{}'.format(i),
#                                                                  lowPriorityInput,
#                                                                  i,rtllmPriorityMode.LOW)).start()


