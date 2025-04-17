import json
import multiprocessing
import os
import select

from StructClass.ReplyDTO import replyDTO
from _thread import *

class ClientReplyHandler(multiprocessing.Process):
    def __init__(self,pipe_Q,replyQueue):
        multiprocessing.Process.__init__(self)
        self.pipe_Q = pipe_Q
        self.pipe_descriptor_map = {}
        self.replyQueue = replyQueue


    def pipe_queue_handler(self):

        while True:
            pipe_name = self.pipe_Q.get()
            pipe_write_name = pipe_name+"_from_server"
            pipe_write = os.open(pipe_name + '_from_server', os.O_NONBLOCK | os.O_WRONLY)
            print('{} opened'.format(pipe_write_name))
            self.pipe_descriptor_map[pipe_name] = pipe_write
            print('replyHandler : {} - {}'.format(pipe_name,pipe_write))

    def reply_pipe_handler(self):
        select.select([self.replyPipe], [], [], 0.001)
        replyObject = json.loads(os.read(self.replyPipe, 1024).decode())
        self.replyQueue.put(replyDTO(
            client_sock=replyObject['client_sock'],
            addr= replyObject['addr'],
            reply_msg=replyObject['reply_msg'],
            requestID=replyObject['requestID']
        ))

    def run(self):
        self.replyPipe = os.open('/home/ywha/RT-LLM/named_pipes/insertReplyPipe', os.O_RDONLY | os.O_NONBLOCK)
        start_new_thread(self.pipe_queue_handler, ())

        while(True):
            targetReply = self.replyQueue.get()
            import time
            print('reply {} : {}'.format(targetReply.requestID, time.time_ns()))
            if isinstance(targetReply, replyDTO) == False:
                print('replyHandler - error : wrong ReplyFormat')

            msg = targetReply.toJson()
            # print('replyHandler - ',targetReply.getClientAddr(), '->', msg)
            print('replyHandler : {} - {}'.format(targetReply.getClientSocket(),self.pipe_descriptor_map[targetReply.getClientSocket()]))
            os.write(self.pipe_descriptor_map[targetReply.getClientSocket()], msg.encode())
            # targetReply.getClientSocket().write( msg.encode() )
            if targetReply.reply_msg == 'bye':
                # print('replyHandler - ending session')
                os.close(targetReply.getClientSocket())
                # targetReply.getClientSocket().close()