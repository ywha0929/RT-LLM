from enum import Enum
class rtllmMsgMode(int,Enum):
    test=0
    createHistoryFile=1
    checkHistoryFile=2
    inferenceRequest=3
    disconnect = 4