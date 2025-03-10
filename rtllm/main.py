from NetworkController import NetworkController
from AnswererController import AnswererController
# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    AnswererController = AnswererController()
    NetworkControllerInstance = NetworkController()
    NetworkControllerInstance.setAnswererControllerScheduler(AnswererController.Scheduler)
    AnswererController.setReplyHandlerQueue(NetworkControllerInstance.replyQueue)
    AnswererController.start()
    NetworkControllerInstance.start()

