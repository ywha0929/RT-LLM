from enum import Enum
class rtllmPriorityMode(int,Enum):
    HIGH=0
    MID=5
    LOW=10
    EMPTY=100000