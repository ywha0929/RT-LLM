import multiprocessing
import threading
import socket
from _thread import *

from Scheduler.SchedulerFIFO import *
from StructClass.rtllmMsgMode import *
from StructClass.InferenceRequest import *
from StructClass.ReplyDTO import *
from multiprocessing import Process, Queue,Manager
import select
import os.path
kvCacheDir = '/home/ywha/RT-LLM/kvCaches/'

class NamedPipeRequestController(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.pipe_index = 0
        self.pipe_prefix = '/home/ywha/RT-LLM/named_pipes/pipe_'
        self.host = socket.gethostbyname(socket.gethostname())
        print(self.host)
        self.port = 10000
        self.clients_read = []
        self.clients_map = {}
        self.replyQueue = Queue()
        self.END = False

    def setAnswererControllerScheduler(self, queue: SchedulerFIFO):
        self.inferenceQueue = queue

    def run(self):
        manager = Manager()
        # Process(target=self.replyHandler,args=(self.replyQueue,)).start()
        # Process(target=self.clientRequestHandler, args=(self.clients_read,self.clients_map)).start()

        start_new_thread(self.replyHandler,(self.replyQueue,) )
        start_new_thread(self.clientRequestHandler,(self.clients_read,self.clients_map))
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host, self.port))
        sock.listen()
        try:
            while True:
                # print('NetworkController/run - Wait')

                client_socket, addr = sock.accept()
                pipe_name = '{}{}'.format(self.pipe_prefix, self.pipe_index)
                self.pipe_index += 1

                os.mkfifo(pipe_name + '_from_server')
                os.mkfifo(pipe_name + '_to_server')
                pipe_read = os.open(pipe_name + '_to_server', os.O_NONBLOCK | os.O_RDONLY)
                self.clients_read.append(pipe_read)
                client_socket.send(pipe_name.encode())
                pipe_ready = client_socket.recv(1024).decode()
                print(pipe_ready)
                pipe_write = os.open(pipe_name + '_from_server', os.O_NONBLOCK | os.O_WRONLY)
                self.clients_map[pipe_read] = pipe_write
                client_socket.send('ready'.encode())


                # start_new_thread(self.clientRequestHandler, (pipe_name, pipe_read,pipe_write))
                # print("NetworkController/run - client count ", len(self.clients))
        except Exception as e:
            print('에러 : ', e)

        finally:
            sock.close()

    def clientRequestHandler(self, clients_read, clients_map):
        # clientStr = '{}'.format(pipe_name)

        # pipe_read = os.open(pipe_name+'_to_server', os.O_NONBLOCK | os.O_RDONLY)
        # pipe_write = os.open(pipe_name+'_from_server', os.O_NONBLOCK | os.O_WRONLY)
        while(True):
            if len(clients_read) != 0:
                break
        ## process until client disconnect ##
        while True:
            try:
                ## send client if data recieved(echo) ##
                # print('before select')
                readables, writeables, excpetions = select.select(clients_read, [], [],0.01)
                # print('after select')
                for readable in readables:
                    print(len(readables))
                    pipe_read = readable
                    pipe_write = clients_map[pipe_read]
                    dataRaw = os.read(pipe_read,1024)
                    # dataRaw = pipe_read.read()

                    # print('clientRequestHandler - data received from {} - {}'.format(pipe_name,dataRaw.decode()))
                    data = json.loads(dataRaw.decode())
                    import time
                    print('clientRequestHandler - data received {} : {}'.format(data,time.time_ns()))

                    if data['mode'] == rtllmMsgMode.test:
                        self.replyQueue.put(replyDTO(pipe_write, 'addr',"check",data['requestID']))

                    elif data['mode'] == rtllmMsgMode.createHistoryFile:

                        self.inferenceQueue.insertInferenceRequest(InferenceRequest(True, None, data['filename']))

                    elif data['mode'] == rtllmMsgMode.checkHistoryFile:
                        jsonFilename = kvCacheDir+data['filename']+'.json'
                        cacheFilename = kvCacheDir+data['filename'] + '.pt'
                        reply = {}
                        if os.path.isfile(jsonFilename) :
                            reply['json'] = True
                        else:
                            reply['json'] = False
                        if os.path.isfile(cacheFilename) :
                            reply['cache'] = True
                        else :
                            reply['cache'] = False

                        self.replyQueue.put(replyDTO(pipe_write, 'addr',reply,requestID=data['requestID']))

                    elif data['mode'] == rtllmMsgMode.inferenceRequest:
                        history = data['historyFilename']
                        jsonFilename = history+'.json'
                        cacheFilename = history+'.pt'
                        input = data['input']
                        # print(cacheFilename)
                        self.inferenceQueue.insertInferenceRequest(InferenceRequest(
                            False,
                            input=input,
                            historyFileName=jsonFilename,
                            cacheFilename=cacheFilename,
                            clientSocket=pipe_write,
                            addr = 'addr',
                            requestID = data['requestID'],
                            priority = data['priority']
                        ))
                    elif data['mode'] == rtllmMsgMode.disconnect:
                        self.replyQueue.put(replyDTO(pipe_write, 'addr', 'bye',requestID=data['requestID']))


            except ConnectionResetError as e:
                # print('clientRequestHandler -  Disconnected by ' + addr[0], ':', addr[1])
                break

    def replyHandler(self,queue: Queue):
        while(self.END == False):
            targetReply = queue.get()
            import time
            print('reply {} : {}'.format(targetReply.requestID, time.time_ns()))
            if isinstance(targetReply, replyDTO) == False:
                print('replyHandler - error : wrong ReplyFormat')


            msg = targetReply.toJson()
            # print('replyHandler - ',targetReply.getClientAddr(), '->', msg)
            os.write(targetReply.getClientSocket(),msg.encode())
            # targetReply.getClientSocket().write( msg.encode() )
            if targetReply.reply_msg == 'bye':
                # print('replyHandler - ending session')
                os.close(targetReply.getClientSocket())
                # targetReply.getClientSocket().close()