import multiprocessing
import threading

import Scheduler.SchedulerPriorityQ
from StructClass.ReplyDTO import replyDTO

from Scheduler import SchedulerFIFO
from Answerer import Answerer
from multiprocessing  import Queue
from StructClass.InferenceRequest import InferenceRequest
import threading
import json
import torch
from transformers import AutoTokenizer, DynamicCache
import threading as _threading
from multiprocessing import Process
import copy
from _thread import *

from StructClass.rtllmPriorityMode import rtllmPriorityMode


# preemptionFlag = False
class AnswererPreemptionController(multiprocessing.Process):
    def __init__(self,insertSchedulerQueue):
        multiprocessing.Process.__init__(self)

        self.Tokenizer = None
        self.Answerer = None
        self.END = False
        self.preemptionFlag = False
        self.prevPriority = 0
        self.kvCacheDir = '/home/ywha/RT-LLM/kvCaches/'
        self.mutex = _threading.Lock()
        self.needCheck = _threading.Condition(self.mutex)
        self.inferenceFinished = False
        self.insertSchedulerQueue = insertSchedulerQueue
        self.Scheduler = Scheduler.SchedulerPriorityQ.SchedulerPriorityQ(3,self.needCheck)

    def insertSchedulerQueueHandler(self):
        while True:
            inferenceRequest = self.insertSchedulerQueue.get()
            print('inserting request to scheduler queue -\n{}'.format(inferenceRequest.toString()))
            self.Scheduler.insertInferenceRequest(inferenceRequest)
    def setReplyHandlerQueue(self, queue:Queue):
        self.replyHandlerQueue = queue

    def run(self):
        start_new_thread(self.insertSchedulerQueueHandler, ())
        self.Answerer = Answerer("meta-llama/Llama-3.2-1B-Instruct", "meta-llama/Llama-3.2-1B-Instruct")
        self.Tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3.2-1B-Instruct", torch_dtype=torch.float16)
        # global preemptionFlag
        print('AnswererPreemptionController started')
        inferenceRequest = self.Scheduler.getInferenceRequest()
        print('inference request : ', inferenceRequest)


        while self.END == False:
            # print('AnswererController.run : {}'.format(inferenceRequest.requestID))
            if inferenceRequest.createCacheMode == True:
                print('AnswererPreemptionController : creating cache - {}'.format(inferenceRequest.historyFileName))
                # print('AnswererController.run : {}'.format('createCacheMode'))

                history = [{"role": "assistant", "content": "You are a chatbot who answers my question."}]
                with open(self.kvCacheDir+inferenceRequest.historyFileName+'.json', "w", encoding="utf-8") as f:  # 쓰기 모드(w)나 추가 모드(a)로 열기
                    json.dump(history, f)
                f.close()
                # del f
                encoded_input = self.Tokenizer.apply_chat_template(history, return_dict=True, return_tensors='pt').to('cuda')
                kvCache = DynamicCache()
                self.Answerer.createKVCache(encoded_input,kvCache)
                torch.save(kvCache,self.kvCacheDir+inferenceRequest.historyFileName+'.pt')
                inferenceRequest = self.Scheduler.getInferenceRequest()
            else :

                # print('AnswererController.run : {}'.format('normalInferenceMode'))

                # inferenceThreadID = start_new_thread(self.makeInferenceAndSendReply, (inferenceRequest,))
                inferenceThread = threading.Thread(target=self.makeInferenceAndSendReply,args=(inferenceRequest.__copy__(),))
                self.prevPriority = inferenceRequest.priority

                inferenceThread.start() # inference start

                # check next inferenceRequest
                # print('try next step : ',self.Scheduler.inferenceQueue.empty())
                nextPriority = self.Scheduler.checkHighestPriority()

                while self.prevPriority <= nextPriority: # no need preemption
                    print('AnswerPremptionController wait')
                    # self.needCheck.acquire()
                    # self.needCheck.wait()
                    # self.needCheck.release()
                    print('AnswerPremptionController notified')
                    # check if higher priority in queue or inferenceThread ended
                    if self.inferenceFinished == True:
                        self.inferenceFinished = False
                        break
                    else:
                        nextPriority = self.Scheduler.checkHighestPriority()
                # self.needCheck.release()
                nextInferenceRequest = self.Scheduler.getInferenceRequest()
                # print('nextInferenceRequest : ',nextInferenceRequest.input)
                if self.prevPriority <= nextInferenceRequest.priority: # no preemption
                    # print('non preemption')

                    inferenceThread.join()
                    # print('AnswererController.run : join checkpoint')
                    inferenceRequest = nextInferenceRequest
                    # del inferenceThread
                    continue
                else :
                    print('preemption {} -> {}'.format(inferenceRequest.requestID, nextInferenceRequest.requestID))
                    self.preemptionFlag = True
                    self.Answerer.model.preemptionFlag = True
                    # self.Answerer.model.setPreemptionFlag(True)

                    # prepare higher priority request
                    # newInferenceThread = threading.Thread(target=self.makeInferenceAndSendReply,args=(inferenceRequest,))
                    # self.prevPriority = inferenceRequest.priority
                    # join previous request
                    inferenceThread.join()
                    # print('AnswererController.run : join checkpoint')
                    # del inferenceThread
                    self.preemptionFlag = False
                    # start higher priority request
                    self.Answerer.model.setPreemptionFlag(False)
                    inferenceRequest = nextInferenceRequest
                    # print('pending request : ',inferenceRequest.input)
                    # newInferenceThread.start()


                # reply = self.Answerer.ask(inferenceRequest.input,cacheFileName=inferenceRequest.cacheFilename,historyFileName=inferenceRequest.historyFileName)
                # self.replyHandlerQueue.put(replyDTO(inferenceRequest.clientSocket, inferenceRequest.addr,reply,requestID=inferenceRequest.requestID))






    def makeInferenceAndSendReply(self,inferenceRequest:InferenceRequest):
        print('makeInferenceAndSendReply : {}'.format(inferenceRequest.requestID))
        # load history
        with open( self.kvCacheDir+inferenceRequest.historyFileName, "r", encoding="utf-8") as f:
            inputs = json.load(f)
        f.close()
        # del f
        # print('makeInferenceAndSendReply : {}'.format(inferenceRequest.historyFileName))
        # load kvCache
        past_key_values = torch.load(self.kvCacheDir + inferenceRequest.cacheFilename)
        # print('makeInferenceAndSendReply : {}'.format(inferenceRequest.historyFileName))
        # append new request to input if input is string
        if type(inferenceRequest.input) == str:
            # print('makeInferenceAndSendReply : {}'.format('new Request'))

            # with length control
            # if inferenceRequest.priority == rtllmPriorityMode.HIGH:
            #     inputs.append({'role': 'user', 'content': inferenceRequest.input+' Answer in one word'})
            # elif inferenceRequest.priority == rtllmPriorityMode.MID:
            #     inputs.append({'role': 'user', 'content': inferenceRequest.input+' Answer in thirty to fifty words'})
            # else:
            #     inputs.append({'role':'user','content':inferenceRequest.input})

            #no Length control
            inputs.append({'role': 'user', 'content': inferenceRequest.input})

            encoded_input = self.Tokenizer.apply_chat_template(inputs, return_dict=True, return_tensors='pt').to('cuda')
        else :
            # print('makeInferenceAndSendReply : {}'.format('Resuming paused request'))
            encoded_input = inferenceRequest.input
            # encoded_input['input_ids'] = encoded_input['input_ids'][:,:-1]

        # print(len(encoded_input['input_ids'][0]))
        # print(encoded_input['input_ids'][0])
        # print(past_key_values[0][0].shape)
        # print(past_key_values[0][0].shape)
        # encode input with history

        # print(encoded_input)
        reply = self.Answerer.ask(encoded_input, emergency=False,kvCache=past_key_values)

        # save kvCache
        torch.save(past_key_values, self.kvCacheDir + inferenceRequest.cacheFilename)
        # del past_key_values

        # encoded_input.input_ids.cat(reply, 2)
        # print(encoded_input)
        if self.preemptionFlag == True: # paused reply
            # print('putting previous request to inference request queue')
            # print('reply : ',reply)
            # reply = reply[:-1]
            # print('reply : ', reply)
            # append generated tokens to encoded_input
            wrapped_reply = reply.reshape(1, len(reply))
            encoded_input['input_ids'] = torch.cat((encoded_input['input_ids'], wrapped_reply), 1)
            encoded_input['attention_mask'] = torch.tensor([[1] * len(encoded_input['input_ids'][0])]).to('cuda')

            # create new request with tokens
            newInferenceRequest = InferenceRequest(False,encoded_input,
                                                   inferenceRequest.historyFileName,
                                                   inferenceRequest.cacheFilename,
                                                   inferenceRequest.clientSocket,
                                                   inferenceRequest.addr,
                                                   inferenceRequest.requestID,
                                                   inferenceRequest.priority,
                                                   prevOutput=reply
                                                   )
            self.Scheduler.insertPausedInferenceRequest(newInferenceRequest)

        else : # normal
            # if resumed from preemption, append reply with prevOutput
            if inferenceRequest.prevOutput != None:
                reply = torch.cat((inferenceRequest.prevOutput,reply),dim=-1)

            # decode reply
            output = self.Tokenizer.batch_decode(reply, skip_special_tokens=True, clean_up_tokenization_spaces=False)

            # join the string
            output = ''.join(output)

            # save history
            inputs.append({'role':'user','content':output})
            with open(self.kvCacheDir + inferenceRequest.historyFileName, "w", encoding="utf-8") as f:  # 쓰기 모드(w)나 추가 모드(a)로 열기
                json.dump(inputs, f)
            f.close()
            # del f
            # send reply to client
            self.replyHandlerQueue.put(
                replyDTO(inferenceRequest.clientSocket, inferenceRequest.addr, output, requestID=inferenceRequest.requestID))
            self.inferenceFinished = True
            # self.needCheck.acquire()
            # self.needCheck.notify()
            # self.needCheck.release()
        # print('makeInferenceAndSendReply finished')