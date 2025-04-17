import multiprocessing
import threading
import socket
import time
from _thread import *

from InferenceController.clientRequestHandler import ClientRequestHandler
from InferenceController.clientReplyHandler import ClientReplyHandler
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
        self.replyQueue = multiprocessing.Queue()
        self.END = False
        self.replyPipeQ = multiprocessing.Queue()
        self.requestPipeQ = multiprocessing.Queue()
        self.clientReplyHandler = ClientReplyHandler(self.replyPipeQ,self.replyQueue)
        self.clientRequestHandler = ClientRequestHandler(self.requestPipeQ,self.replyQueue)

    def run(self):
        # manager = Manager()
        # Process(target=self.replyHandler,args=(self.replyQueue,)).start()
        # Process(target=self.clientRequestHandler, args=(self.clients_read,self.clients_map)).start()

        self.clientReplyHandler.start()

        self.clientRequestHandler.start()
        # start_new_thread(self.replyHandler,(self.replyQueue,) )
        # start_new_thread(self.clientRequestHandler,(self.clients_read,self.clients_map))
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
                self.requestPipeQ.put(pipe_name)
                time.sleep(0.5)
                # pipe_read = os.open(pipe_name + '_to_server', os.O_NONBLOCK | os.O_RDONLY)
                # self.clients_read.append(pipe_read)
                client_socket.send(pipe_name.encode())
                pipe_ready = client_socket.recv(1024).decode()
                print(pipe_ready)
                self.replyPipeQ.put(pipe_name)
                time.sleep(0.5)
                # pipe_write = os.open(pipe_name + '_from_server', os.O_NONBLOCK | os.O_WRONLY)
                # self.clients_map[pipe_read] = pipe_write
                client_socket.send('ready'.encode())


                # start_new_thread(self.clientRequestHandler, (pipe_name, pipe_read,pipe_write))
                # print("NetworkController/run - client count ", len(self.clients))
        except Exception as e:
            print('에러 : ', e)

        finally:
            sock.close()

