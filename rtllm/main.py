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

    # for profiling
    # from torch.profiler import profile, record_function, ProfilerActivity
    #
    # activities = [ProfilerActivity.CPU, ProfilerActivity.CUDA, ProfilerActivity.XPU]
    # with profile(activities=activities, profile_memory=True, record_shapes=True, with_modules=True,
    #              with_stack=True) as prof:
    #     with record_function("model_inference"):
    #         AnswererPreemptionController = AnswererPreemptionController()
    #         NetworkControllerInstance = NetworkController()
    #         NetworkControllerInstance.setAnswererControllerScheduler(AnswererPreemptionController.Scheduler)
    #         AnswererPreemptionController.setReplyHandlerQueue(NetworkControllerInstance.replyQueue)
    #         AnswererPreemptionController.start()
    #         NetworkControllerInstance.start()
    #
    #
    # import time
    # time.sleep(30)
    # prof.export_chrome_trace('Preemption.json')
    # print('done')