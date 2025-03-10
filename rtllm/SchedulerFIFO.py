from multiprocessing  import Queue
import InferenceRequest
class SchedulerFIFO:
    def __init__(self):
        self.inferenceQueue = Queue()

    def insertInferenceRequest(self, request:InferenceRequest):
        self.inferenceQueue.put(request)

    def getInferenceRequest(self) -> InferenceRequest:
        return self.inferenceQueue.get()