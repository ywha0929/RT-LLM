import multiprocessing
import os
import time

from Scheduler.SchedulerFIFO import *
from StructClass.rtllmMsgMode import *
from StructClass.InferenceRequest import *
from StructClass.ReplyDTO import *
from multiprocessing import Process, Queue,Manager
import select
import os.path
kvCacheDir = '/home/ywha/RT-LLM/kvCaches/'
from _thread import *

class ClientRequestHandler(multiprocessing.Process):

    def __init__(self,pipe_Q,replyQueue):
        multiprocessing.Process.__init__(self)
        self.insertSchedulerQueue = None
        self.pipe_Q = pipe_Q
        self.pipe_descriptor_map = {}
        self.replyQueue = replyQueue
        self.clients_read = []


    def setAnswererControllerScheduler(self, queue):
        self.insertSchedulerQueue = queue

    def pipe_queue_handler(self):
        while True:
            pipe_name = self.pipe_Q.get()
            pipe_read_name = pipe_name+"_to_server"
            pipe_read = os.open(pipe_name + '_to_server', os.O_NONBLOCK | os.O_RDONLY)
            print('{} opened'.format(pipe_read_name))
            self.pipe_descriptor_map[pipe_read] = pipe_name
            self.clients_read.append(pipe_read)

    def run(self):
        start_new_thread(self.pipe_queue_handler, ())
        self.insertSchedulerPipe = os.open('/home/ywha/RT-LLM/named_pipes/insertSchedulerPipe',os.O_WRONLY | os.O_NONBLOCK)
        time.sleep(0.5)
        os.write(self.insertSchedulerPipe, 'ready'.encode())
        while (True):
            if len(self.clients_read) != 0:
                break
            ## process until client disconnect ##
        while True:
            try:
                ## send client if data recieved(echo) ##
                # print('before select')
                readables, writeables, excpetions = select.select(self.clients_read, [], [], 0.01)
                # print('after select')
                for readable in readables:
                    # print(len(readables))
                    pipe_read = readable
                    pipe_write = self.pipe_descriptor_map[pipe_read]
                    print('clientRequestHandler : ',pipe_write)
                    dataRaw = os.read(pipe_read, 1024)
                    # dataRaw = pipe_read.read()

                    # print('clientRequestHandler - data received from {} - {}'.format(pipe_name,dataRaw.decode()))
                    data = json.loads(dataRaw.decode())
                    print('clientRequestHandler - data received {} : {}'.format(data, time.time_ns()))

                    if data['mode'] == rtllmMsgMode.test:
                        self.replyQueue.put(replyDTO(pipe_write, 'addr', "check", data['requestID']))

                    elif data['mode'] == rtllmMsgMode.createHistoryFile:
                        msg = {
                            'createCacheMode':True,
                            'input' : None,
                            'historyFileName' : data['filename'],
                            'cacheFilename' : None,
                            'clientSocket' : None,
                            'addr' : None,
                            'requestID' : data['requestID'],
                            'priority' : None
                        }
                        os.write(self.insertSchedulerPipe, json.dumps(msg).encode())
                        # self.insertSchedulerPipe
                        # self.insertSchedulerQueue.put(InferenceRequest(True, None, data['filename']))

                    elif data['mode'] == rtllmMsgMode.checkHistoryFile:
                        jsonFilename = kvCacheDir + data['filename'] + '.json'
                        cacheFilename = kvCacheDir + data['filename'] + '.pt'
                        reply = {}
                        if os.path.isfile(jsonFilename):
                            reply['json'] = True
                        else:
                            reply['json'] = False
                        if os.path.isfile(cacheFilename):
                            reply['cache'] = True
                        else:
                            reply['cache'] = False

                        self.replyQueue.put(replyDTO(pipe_write, 'addr', reply, requestID=data['requestID']))

                    elif data['mode'] == rtllmMsgMode.inferenceRequest:
                        history = data['historyFilename']
                        jsonFilename = history + '.json'
                        cacheFilename = history + '.pt'
                        input = data['input']
                        # print(cacheFilename)
                        msg = {
                            'createCacheMode' :False,
                            'input' : input,
                            'historyFileName' : jsonFilename,
                            'cacheFilename' : cacheFilename,
                            'clientSocket' : pipe_write,
                            'addr' : 'addr',
                            'requestID' : data['requestID'],
                            'priority' : data['priority']
                        }
                        os.write(self.insertSchedulerPipe, json.dumps(msg).encode())
                        # self.insertSchedulerQueue.put(InferenceRequest(
                        #     False,
                        #     input=input,
                        #     historyFileName=jsonFilename,
                        #     cacheFilename=cacheFilename,
                        #     clientSocket=pipe_write,
                        #     addr='addr',
                        #     requestID=data['requestID'],
                        #     priority=data['priority']
                        # ))
                    elif data['mode'] == rtllmMsgMode.disconnect:
                        self.replyQueue.put(replyDTO(pipe_write, 'addr', 'bye', requestID=data['requestID']))


            except ConnectionResetError as e:
                # print('clientRequestHandler -  Disconnected by ' + addr[0], ':', addr[1])
                break
