from queue import PriorityQueue
from StructClass import InferenceRequest


class SchedulerPriorityQ:
    def __init__(self):
        self.inferenceQueue = PriorityQueue()
        self.prevPriority = -1

    def insertInferenceRequest(self, request: InferenceRequest, priority:int=0):
        self.inferenceQueue.put((priority,request))

    def getInferenceRequest(self) -> InferenceRequest:
        request = self.inferenceQueue.get()
        self.prevPriority = request[0]
        return request[1]