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
        threading.Thread(target=inference,args=(i,'test_{}'.format(i),
                            highPriorityInput,
                            (i),rtllmPriorityMode.HIGH)).start()
        time.sleep(1)
def MidInference() :
    for i in range (110,130):
        threading.Thread(target=inference,args=(i,'test_{}'.format(i),
                            midPriorityInput,
                            i,rtllmPriorityMode.MID)).start()
        time.sleep(5)
def LowInference() :
    for i in range(100,110):
        threading.Thread(target=inference,args=(i,'test_{}'.format(i),
                            lowPriorityInput,
                            i,rtllmPriorityMode.LOW)).start()
        time.sleep(11)

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
threading.Thread(target=LowInference,args=()).start()
threading.Thread(target=MidInference,args=()).start()
threading.Thread(target=HighInference,args=()).start()
# for i in range(110):
#     if i % 10 == 9: 
#         threading.Thread(target=inference,args=(i,'test_{}'.format(i),
#                                                                  highPriorityInput,
#                                                                  (i),rtllmPriorityMode.HIGH)).start()
        
#     else :
#         threading.Thread(target=inference,args=(i,'test_{}'.format(i),
#                                                                  lowPriorityInput,
#                                                                  i,rtllmPriorityMode.LOW)).start()


