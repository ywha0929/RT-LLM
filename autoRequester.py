from rtllmAPI import *
import time
Helper = rtllm("127.0.1.1",10000)
Helper.connectToServer()
Helper.tryConnectionTest()

Helper.createHistoryFile('autoRequester')
print('return of checkHistoryFile : ',Helper.checkHistoryFile('autoRequester'))


f = open('/home/ywha/RT-LLM/country-list.json')
jsonObject = json.load(f)
print(len(jsonObject))
for i in range(100):
    thisObject = jsonObject[i]
    request = 'Where is capital of {}'.format(thisObject['country'])
    start = time.time_ns()
    print(Helper.requestInference('autoRequester',request,1)," time : ",(time.time_ns()-start)/1000000)
    time.sleep(0.5)