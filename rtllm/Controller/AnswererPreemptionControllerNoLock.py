import gc
import threading

import Scheduler.SchedulerPriorityQNoLock
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
import time
from StructClass.rtllmPriorityMode import rtllmPriorityMode


# preemptionFlag = False
class AnswererPreemptionControllerNoLock(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.Answerer = Answerer("meta-llama/Llama-3.2-1B-Instruct","meta-llama/Llama-3.2-1B-Instruct")
        self.Tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3.2-1B-Instruct", torch_dtype=torch.float16)
        self.kvCacheHolder = {}
        self.historyHolder = {}
        self.END = False
        self.preemptionFlag = False
        self.prevPriority = 0
        self.kvCacheDir = '/home/ywha/RT-LLM/kvCaches/'
        self.inferenceFinished = False
        self.Scheduler = Scheduler.SchedulerPriorityQNoLock.SchedulerPriorityQNoLock(3)


    def run(self):
        # global preemptionFlag
        inferenceRequest = self.Scheduler.getInferenceRequest()

        while self.END == False:
            # print('AnswererController.run : {}'.format(inferenceRequest.requestID))
            if inferenceRequest.createCacheMode == True:

                # print('AnswererController.run : {}'.format('createCacheMode'))

                history = [{"role": "assistant", "content": "You are a chatbot who answers my question."}]
                self.historyHolder[self.kvCacheDir+inferenceRequest.historyFileName+'.json'] = history
                # with open(self.kvCacheDir+inferenceRequest.historyFileName+'.json', "w", encoding="utf-8") as f:  # 쓰기 모드(w)나 추가 모드(a)로 열기
                #     json.dump(history, f)
                # f.close()
                # del f
                encoded_input = self.Tokenizer.apply_chat_template(history, return_dict=True, return_tensors='pt').to('cuda')
                kvCache = DynamicCache()
                self.Answerer.createKVCache(encoded_input,kvCache)
                kvCacheFileName = self.kvCacheDir+inferenceRequest.historyFileName+'.pt'
                legacy_cache = kvCache.to_legacy_cache()
                clone = []
                for i in range(len(legacy_cache)):
                    #clone layer
                    layer_clone = []
                    for j in range(len(legacy_cache[i])):
                        layer_clone.append(legacy_cache[i][j].clone().detach())
                    clone.append(tuple(layer_clone))
                self.kvCacheHolder[kvCacheFileName] = tuple(clone)

                # del kvCache
                # gc.collect()
                # torch.cuda.empty_cache()
                # torch.save(kvCache,self.kvCacheDir+inferenceRequest.historyFileName+'.pt')
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
                    print('priority check : {} - {}'.format(self.prevPriority, nextPriority))
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


    def setReplyHandlerQueue(self, queue:Queue):
        self.replyHandlerQueue = queue



    def makeInferenceAndSendReply(self,inferenceRequest:InferenceRequest):
        check1 = time.time_ns()
        print('makeInferenceAndSendReply : {} - {}'.format(inferenceRequest.requestID,check1))
        # load history
        inputs = self.historyHolder[self.kvCacheDir+inferenceRequest.historyFileName]
        # with open( self.kvCacheDir+inferenceRequest.historyFileName, "r", encoding="utf-8") as f:
        #     inputs = json.load(f)
        # f.close()
        # del f
        # print('makeInferenceAndSendReply : {}'.format(inferenceRequest.historyFileName))

        # load kvCache
        # past_key_values = torch.load(self.kvCacheDir + inferenceRequest.cacheFilename,weights_only=False)
        legacy_cache = self.kvCacheHolder.get(self.kvCacheDir + inferenceRequest.cacheFilename)
        clone = []
        for i in range(len(legacy_cache)):
            # clone layer
            layer_clone = []
            for j in range(len(legacy_cache[i])):
                layer_clone.append(legacy_cache[i][j].clone().detach().to('cuda'))
            clone.append(tuple(layer_clone))
        past_key_values = DynamicCache().from_legacy_cache(tuple(clone))



        check2 = time.time_ns()
        print('makeInferenceAndSendReply2 load history and kvCache: {} - {}'.format(inferenceRequest.requestID, (check2-check1)/1000000))
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
        # print(inputs)
        # print(past_key_values[0][0].shape)
        # print(past_key_values[0][0].shape)
        # encode input with history

        # print(encoded_input)
        check3 = time.time_ns()
        print('makeInferenceAndSendReply3 prepare encoded_input: {} - {}'.format(inferenceRequest.requestID,(check3-check2)/1000000))
        reply = self.Answerer.ask(encoded_input, emergency=False,kvCache=past_key_values)
        check4 = time.time_ns()
        print('makeInferenceAndSendReply4 ask inference: {} - {}'.format(inferenceRequest.requestID,(check4-check3)/1000000))

        # save kvCache
        # torch.save(past_key_values, self.kvCacheDir + inferenceRequest.cacheFilename)
        legacy_cache = past_key_values.to_legacy_cache()
        clone = []
        for i in range(len(legacy_cache)):
            # clone layer
            layer_clone = []
            for j in range(len(legacy_cache[i])):
                layer_clone.append(legacy_cache[i][j].clone().detach())
            clone.append(tuple(layer_clone))
        self.kvCacheHolder[self.kvCacheDir + inferenceRequest.cacheFilename] = tuple(clone)
        check5 = time.time_ns()
        print('makeInferenceAndSendReply5 save kvCache: {} - {}'.format(inferenceRequest.requestID,(check5-check4)/1000000))
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
            check6 = time.time_ns()
            print('makeInferenceAndSendReply6 paused inference post processing: {} - {}'.format(inferenceRequest.requestID,
                                                                            (check6 - check5) / 1000000))

        else : # normal

            # if resumed from preemption, append reply with prevOutput
            if inferenceRequest.prevOutput != None:
                reply = torch.cat((inferenceRequest.prevOutput,reply),dim=-1)
            # print('reply : {}'.format(reply))
            # decode reply
            output = self.Tokenizer.batch_decode(reply, skip_special_tokens=True, clean_up_tokenization_spaces=False)
            # print('output : {}'.format(output))
            # join the string
            output = ''.join(output)

            # save history
            inputs.append({'role':'user','content':output})
            self.historyHolder[self.kvCacheDir + inferenceRequest.historyFileName] = inputs
            # with open(self.kvCacheDir + inferenceRequest.historyFileName, "w", encoding="utf-8") as f:  # 쓰기 모드(w)나 추가 모드(a)로 열기
            #     json.dump(inputs, f)
            # f.close()
            # del f
            # send reply to client
            print('putting reply to replyHandlerQueue {} : {}'.format(inferenceRequest.requestID,time.time_ns()))
            self.replyHandlerQueue.put(
                replyDTO(inferenceRequest.clientSocket, inferenceRequest.addr, output, requestID=inferenceRequest.requestID))
            self.inferenceFinished = True
            check6 = time.time_ns()
            print('makeInferenceAndSendReply6 ended inference post processing: {} - {}'.format(
                inferenceRequest.requestID,
                (check6 - check5) / 1000000))

        # print('makeInferenceAndSendReply finished')