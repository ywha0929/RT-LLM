from Controller.AnswererPreemptionController import AnswererPreemptionController
from Controller.NetworkController import NetworkController
from Controller.AnswererController import AnswererController
# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # normal mode
    # AnswererController = AnswererController()
    # NetworkControllerInstance = NetworkController()
    # NetworkControllerInstance.setAnswererControllerScheduler(AnswererController.Scheduler)
    # AnswererController.setReplyHandlerQueue(NetworkControllerInstance.replyQueue)
    # AnswererController.start()
    # NetworkControllerInstance.start()

    # preemption mode
    AnswererPreemptionController = AnswererPreemptionController()
    NetworkControllerInstance = NetworkController()
    NetworkControllerInstance.setAnswererControllerScheduler(AnswererPreemptionController.Scheduler)
    AnswererPreemptionController.setReplyHandlerQueue(NetworkControllerInstance.replyQueue)
    AnswererPreemptionController.start()
    NetworkControllerInstance.start()

