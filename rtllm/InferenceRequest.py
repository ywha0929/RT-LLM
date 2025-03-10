class InferenceRequest:
    def __init__(self,createCacheMode:bool,input:str,historyFileName:str,cacheFilename:str=None,clientSocket=None,addr=None,requestID:int=None):
        self.createCacheMode = createCacheMode
        self.input = input
        self.historyFileName = historyFileName
        self.cacheFilename = cacheFilename
        self.clientSocket = clientSocket
        self.addr = addr
        self.requestID = requestID