"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Value object proxy to test concoord implementation
@copyright: See LICENSE
"""
from concoord.asyncclientproxy import ClientProxy

class Test():
    def __init__(self, bootstrap):
        self.proxy = ClientProxy(bootstrap, True)

    def __concoordinit__(self):
        repeat = True
        while repeat:
            reqdesc = self.proxy.invoke_command_async('__init__')
            with reqdesc.replyarrivedcond:
                while not reqdesc.replyarrived:
                    reqdesc.replyarrivedcond.wait()
            repeat = reqdesc.resendnecessary
        return reqdesc.reply.reply

    def getvalue(self):
        repeat = True
        while repeat:
            reqdesc = self.proxy.invoke_command_async('getvalue')
            with reqdesc.replyarrivedcond:
                print reqdesc
                while not reqdesc.replyarrived:
                    reqdesc.replyarrivedcond.wait()
            repeat = reqdesc.resendnecessary
        return reqdesc.reply.reply

    def setvalue(self, newvalue):
        repeat = True
        while repeat:
            reqdesc = self.proxy.invoke_command_async('setvalue', newvalue)
            with reqdesc.replyarrivedcond:
                while not reqdesc.replyarrived:
                    reqdesc.replyarrivedcond.wait()
            repeat = reqdesc.resendnecessary
        return reqdesc.reply.reply

    def __str__(self):
        repeat = True
        while repeat:
            reqdesc = self.proxy.invoke_command_async('__str__')
            with reqdesc.replyarrivedcond:
                while not reqdesc.replyarrived:
                    reqdesc.replyarrivedcond.wait()
            repeat = reqdesc.resendnecessary
        return reqdesc.reply.reply
