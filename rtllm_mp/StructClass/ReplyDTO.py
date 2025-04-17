import json

class replyDTO:
    def __init__(self, client_sock,addr, reply_msg,requestID):
        self.client_sock = client_sock
        self.reply_msg = reply_msg
        self.addr = addr
        self.requestID = requestID

    def toJson(self):
        msg = {'msg':self.reply_msg,'requestID':self.requestID}
        return json.dumps(msg)

    def getClientSocket(self):
        return self.client_sock

    def getClientAddr(self):
        return '{}/{}'.format(self.addr[0], self.addr[1])