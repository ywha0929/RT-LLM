import threading
import socket
from _thread import *
from multiprocessing  import Queue

from SchedulerFIFO import *
from AnswererController import AnswererController
from rtllmMsgMode import *
from InferenceRequest import *
import jsonlines
from transformers.cache_utils import DynamicCache
import ReplyDTO
from ReplyDTO import *
import os.path
kvCacheDir = '/home/ywha/RT-LLM/kvCaches/'
class NetworkController(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.host = socket.gethostbyname(socket.gethostname())
        print(self.host)
        self.port = 10000
        self.clients = []
        self.replyQueue = Queue()
        self.END = False

    def setAnswererControllerScheduler(self, queue:SchedulerFIFO):
        self.inferenceQueue = queue

    def run(self):
        start_new_thread(self.replyHandler,(self.replyQueue,) )
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host, self.port))
        sock.listen()
        try:
            while True:
                print('NetworkController/run - Wait')

                client_socket, addr = sock.accept()
                self.clients.append(client_socket)
                start_new_thread(self.clientRequestHandler, (client_socket, addr))
                print("NetworkController/run - client count ", len(self.clients))
        except Exception as e:
            print('에러 : ', e)

        finally:
            sock.close()

    def clientRequestHandler(self, client_socket, addr):
        print('clientRequestHandler - Connected by :', addr[0], ':', addr[1])
        clientStr = '{}/{}'.format(addr[0],addr[1])
        ## process until client disconnect ##
        while True:
            try:
                ## send client if data recieved(echo) ##
                dataRaw = client_socket.recv(1024)
                data = json.loads(dataRaw.decode())
                print('clientRequestHandler - data received from {} : {}'.format(clientStr, data))

                if data['mode'] == rtllmMsgMode.test:
                    self.replyQueue.put(replyDTO(client_socket, addr,"check",data['requestID']))

                elif data['mode'] == rtllmMsgMode.createHistoryFile:

                    self.inferenceQueue.insertInferenceRequest(InferenceRequest(True,None,data['filename']))

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

                    self.replyQueue.put(replyDTO(client_socket, addr,reply,requestID=data['requestID']))

                elif data['mode'] == rtllmMsgMode.inferenceRequest:
                    history = data['historyFilename']
                    jsonFilename = history+'.json'
                    cacheFilename = history+'.pt'
                    input = data['input']
                    print(cacheFilename)
                    self.inferenceQueue.insertInferenceRequest(InferenceRequest(
                        False,
                        input=input,
                        historyFileName=jsonFilename,
                        cacheFilename=cacheFilename,
                        clientSocket=client_socket,
                        addr = addr,
                        requestID = data['requestID']
                    ))
                elif data['mode'] == rtllmMsgMode.disconnect:
                    self.replyQueue.put(replyDTO(client_socket, addr, 'bye',requestID=data['requestID']))


            except ConnectionResetError as e:
                print('clientRequestHandler -  Disconnected by ' + addr[0], ':', addr[1])
                break

    def replyHandler(self,queue: Queue):
        while(self.END == False):
            targetReply = queue.get()
            if isinstance(targetReply, replyDTO) == False:
                print('replyHandler - error : wrong ReplyFormat')


            msg = targetReply.toJson()
            print('replyHandler - ',targetReply.getClientAddr(), '->', msg)
            targetReply.getClientSocket().send( msg.encode() )
            if targetReply.reply_msg == 'bye':
                print('replyHandler - ending session')
                targetReply.getClientSocket().close()