import socket
import json

from enum import Enum
class rtllmMsgMode(int,Enum):
    test=0
    createHistoryFile=1
    checkHistoryFile=2
    inferenceRequest=3
    disconnect=4


class rtllm:
    def __init__(self,ip,port):
        self.ip = ip
        self.port = port
        

    def connectToServer(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.connect((self.ip, self.port))
    
    def disconnect(self,requestID:int=None):
        print('ending session')
        msg = {
            "mode":rtllmMsgMode.disconnect,
            "requestID":requestID
        }
        self.server.send(json.dumps(msg).encode())
        reply = self.server.recv(1024).decode()
        print("data received : ",reply)
        self.server.close()


    def tryConnectionTest(self):
        print('sending test data')
        msg = {
            "mode":rtllmMsgMode.test,
            "msg":"this is test",
            "requestID":0

            }
        self.server.send(json.dumps(msg).encode())
        reply = self.server.recv(1024).decode()
        print("data received : ",reply)

    def createHistoryFile(self,filename:str,requestID:int=None):
        print('sending request to createHistoryFile')
        msg = {
            "mode":rtllmMsgMode.createHistoryFile,
            "filename":filename,
            "requestID":requestID
        }
        self.server.send(json.dumps(msg).encode())

    def checkHistoryFile(self,filename:str,requestID:int=None):
        print('sending request to checkHistoryFile')
        msg={
            "mode":rtllmMsgMode.checkHistoryFile,
            "filename":filename,
            "requestID":requestID
        }
        self.server.send(json.dumps(msg).encode())
        reply = self.server.recv(1024).decode()
        return reply
    
    def requestInference(self,filename,input,requestID:int=None) :
        print('sending request to requestInference')
        msg ={
            "mode":rtllmMsgMode.inferenceRequest,
            "historyFilename":filename,
            "input":input,
            "requestID":requestID
        }
        self.server.send(json.dumps(msg).encode())
        reply = self.server.recv(1024).decode()
        return reply