class InferenceRequest:
    def __init__(self,createCacheMode:bool,input,historyFileName:str,cacheFilename:str=None,clientSocket=None,addr=None,requestID:int=None,priority:int=0,prevOutput=None):
        self.createCacheMode = createCacheMode
        self.input = input
        self.historyFileName = historyFileName
        self.cacheFilename = cacheFilename
        self.clientSocket = clientSocket
        self.addr = addr
        self.requestID = requestID
        self.priority = priority
        self.prevOutput = prevOutput
        # print('InferenceRequest ',input)

    def __copy__(self):
        return InferenceRequest(createCacheMode=self.createCacheMode,
                                input=self.input,
                                historyFileName=self.historyFileName,
                                cacheFilename=self.cacheFilename,
                                clientSocket=self.clientSocket,
                                addr=self.addr,
                                requestID=self.requestID,
                                priority=self.priority,
                                prevOutput=self.prevOutput)