# from multiprocessing  import Queue
from StructClass import InferenceRequest
from queue import Queue
import sys
class SchedulerFIFO:
    def __init__(self):
        self.inferenceQueue = Queue()

    def insertInferenceRequest(self, request: InferenceRequest):

        print('SchedulerFIFO - insertInferenceRequest : ',request.input)
        self.inferenceQueue.put(request,block=True)

    def getInferenceRequest(self) -> InferenceRequest:
        # print('SchedulerFIFO - getInferenceRequest')
        nextRequest = self.inferenceQueue.get(block=True)
        print('SchedulerFIFO - getInferenceRequest : ', nextRequest.input)
        # print(nextRequest.requestID)
        return nextRequest