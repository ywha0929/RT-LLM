from queue import Queue
from StructClass import InferenceRequest
from StructClass.rtllmPriorityMode import rtllmPriorityMode
import threading as _threading

class SchedulerPriorityQNoLock:
    def __init__(self,modeCount):
        self.queues = []
        for i in range(modeCount):
            self.queues.append(Queue())
        self.mutex = _threading.Lock()
        self.not_empty = _threading.Condition(self.mutex)
        self.not_full = _threading.Condition(self.mutex)

    def checkHighestPriority(self):
        if not self.queues[0].empty():
            return rtllmPriorityMode.HIGH
        elif not self.queues[1].empty():
            return rtllmPriorityMode.MID
        elif not self.queues[2].empty():
            return rtllmPriorityMode.LOW
        else : #every queue empty
            return rtllmPriorityMode.EMPTY


    def insertInferenceRequest(self, request: InferenceRequest):
        self.not_full.acquire()
        if request.priority == rtllmPriorityMode.HIGH :
            self.queues[0].put(request)
        elif request.priority == rtllmPriorityMode.MID :
            self.queues[1].put(request)
        else :
            self.queues[2].put(request)
        self.not_empty.notify()

        print('insertInferenceRequest queues inserted')
        self.not_full.release()
    def insertPausedInferenceRequest(self, request: InferenceRequest):
        self.not_full.acquire()
        if request.priority == rtllmPriorityMode.HIGH :
            self.queues[0].queue.insert(0,request)
        elif request.priority == rtllmPriorityMode.MID :
            self.queues[1].queue.insert(0,request)
        else :
            self.queues[2].queue.insert(0,request)
        self.not_empty.notify()
        self.not_full.release()



    def getInferenceRequest(self) -> InferenceRequest:
        self.not_empty.acquire()
        for i in range(len(self.queues)):
            if not self.queues[i].empty():
                request = self.queues[i].get()
                self.not_full.notify()
                self.not_empty.release()
                print('request : ', request)
                return request
            if i == len(self.queues)-1 and self.queues[i].empty():
                self.not_empty.wait()
        for i in range(len(self.queues)):
            if not self.queues[i].empty():
                request = self.queues[i].get()
                self.not_full.notify()
                self.not_empty.release()
                print('request : ', request)
                return request
        self.not_empty.release()

