import socket
import json
import os
import select
from enum import Enum
import time
class rtllmMsgMode(int,Enum):
    test=0
    createHistoryFile=1
    checkHistoryFile=2
    inferenceRequest=3
    disconnect=4

class rtllmPriorityMode(int,Enum):
    HIGH=0
    MID=5
    LOW=10

class rtllm:
    def __init__(self,ip,port):
        self.ip = ip
        self.port = port
        

    def connectToServer(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.connect((self.ip, self.port))
        pipe_name = server.recv(1024).decode()
        print('received pipe name : ',pipe_name)
        self.pipe_name_read = pipe_name+'_from_server'
        self.pipe_name_write = pipe_name+'_to_server'
        self.pipe_write = os.open(self.pipe_name_write, os.O_NONBLOCK | os.O_WRONLY)
        self.pipe_read = os.open(self.pipe_name_read, os.O_NONBLOCK | os.O_RDONLY)
        server.send('opened named pipe {}'.format(self.pipe_name_read).encode())
        print(server.recv(1024).decode())
        server.close()
    
    def disconnect(self,requestID:int=None):
        print('ending session')
        msg = {
            "mode":rtllmMsgMode.disconnect,
            "requestID":requestID
        }
        os.write(self.pipe_write,json.dumps(msg).encode())
        readables, writeables, excpetions = select.select([self.pipe_read],[],[])
        reply = os.read(self.pipe_read,1024).decode()
        # self.pipe_write.write()
        # reply = self.pipe.read().decode()
        # self.server.send(json.dumps(msg).encode())
        # self.server.sendall()
        # reply = self.server.recv(4096).decode()
        print("data received : ",reply)
        self.server.close()


    def tryConnectionTest(self):
        print('sending test data')
        msg = {
            "mode":rtllmMsgMode.test,
            "msg":"this is test",
            "requestID":0

            }
        os.write(self.pipe_write,json.dumps(msg).encode())
        readables, writeables, excpetions = select.select([self.pipe_read],[],[])
        reply = os.read(self.pipe_read,1024).decode()
        # self.pipe_write.write(json.dumps(msg).encode())
        # reply = self.pipe_read.read().decode()
        # self.server.send(json.dumps(msg).encode())
        # reply = self.server.recv(4096).decode()
        print("data received : ",reply)

    def createHistoryFile(self,filename:str,requestID:int=None):
        print('sending request to createHistoryFile')
        msg = {
            "mode":rtllmMsgMode.createHistoryFile,
            "filename":filename,
            "requestID":requestID
        }
        os.write(self.pipe_write,json.dumps(msg).encode())
        # self.server.send(json.dumps(msg).encode())

    def checkHistoryFile(self,filename:str,requestID:int=None):
        print('sending request to checkHistoryFile')
        msg={
            "mode":rtllmMsgMode.checkHistoryFile,
            "filename":filename,
            "requestID":requestID
        }
        os.write(self.pipe_write,json.dumps(msg).encode())
        readables, writeables, excpetions = select.select([self.pipe_read],[],[])
        reply = os.read(self.pipe_read,1024).decode()
        # self.server.send(json.dumps(msg).encode())
        # reply = self.server.recv(4096).decode()
        return reply
    
    def requestInference(self,filename,input,requestID:int=None,priority:int=0) :
        print('sending request to requestInference')
        msg ={
            "mode":rtllmMsgMode.inferenceRequest,
            "historyFilename":filename,
            "input":input,
            "requestID":requestID,
            "priority":priority
        }
        print('write data to server : {} - {}'.format(requestID,time.time_ns()))
        os.write(self.pipe_write,json.dumps(msg).encode())
        readables, writeables, excpetions = select.select([self.pipe_read],[],[])
        replyRaw = os.read(self.pipe_read,100000)
        print('read data from server : {} - {}'.format(requestID,time.time_ns()))
        # self.server.send(json.dumps(msg).encode())
        # replyRaw = self.server.recv(100000)
        reply = json.loads(replyRaw.decode())
        return reply