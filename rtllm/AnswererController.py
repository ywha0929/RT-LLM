import threading

from ReplyDTO import replyDTO

import SchedulerFIFO
from Answerer import Answerer
from multiprocessing  import Queue

class AnswererController(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.Answerer = Answerer()
        self.Scheduler = SchedulerFIFO.SchedulerFIFO()
        self.END = False

    def run(self):
        while self.END == False:
            inferenceRequest = self.Scheduler.getInferenceRequest()
            print('AnswererController.run : {}'.format(inferenceRequest))
            if inferenceRequest.createCacheMode == True:
                self.Answerer.createKVCache(inferenceRequest.historyFileName)
            else :
                reply = self.Answerer.ask(inferenceRequest.input,cacheFileName=inferenceRequest.cacheFilename,historyFileName=inferenceRequest.historyFileName)
                self.replyHandlerQueue.put(replyDTO(inferenceRequest.clientSocket, inferenceRequest.addr,reply,requestID=inferenceRequest.requestID))

    def setReplyHandlerQueue(self, queue:Queue):
        self.replyHandlerQueue = queue