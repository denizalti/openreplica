import socket, time
from threading import RLock, Thread
from concoord.exception import *
from concoord.threadingobject.dcondition import DCondition

MSG_PING = 8
PING_DELAY = 10

class Pinger():
    def __init__(self):
        self.members = set()
        self.membership_condition = DCondition()

        self.liveness = {}

        self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        myaddr = socket.gethostbyname(socket.gethostname())
        myport = self.socket.getsockname()[1]
        self.me = "%s:%d", (myaddr,myport)

        comm_thread = Thread(target=self.ping_members, name='PingThread')
        comm_thread.start()

    def add(self, member):
        if member not in self.members:
            self.members.add(member)
            self.liveness[member] = 0
        # Notify nodes of membership change
        self.membership_condition.notifyAll()

    def remove(self, member):
        if member in self.members:
            self.members.remove(member)
            del self.liveness[member]
        else:
            raise KeyError(member)
        # Notify nodes of membership change
        self.membership_condition.notifyAll()

    def get_members(self):
        return self.members

    def ping_members(self):
        while True:
            for member in self.members:
                print "Sending PING to %s" % str(member)
                pingmessage = PingMessage(self.me)
                success = self.send(pingmessage, peer=peer)
                if success < 0:
                    print "Node not responding, marking."
                    self.liveness[member] += 1

            time.sleep(PING_DELAY)

    def send(self, msg):
        messagestr = pickle.dumps(msg)
        message = struct.pack("I", len(messagestr)) + messagestr
        try:
            while len(message) > 0:
                try:
                    bytesent = self.thesocket.send(message)
                    message = message[bytesent:]
                except IOError, e:
                    if isinstance(e.args, tuple):
                        if e[0] == errno.EAGAIN:
                            continue
                        else:
                            raise e
                except AttributeError, e:
                    raise e
            return True
        except socket.error, e:
            if isinstance(e.args, tuple):
                if e[0] == errno.EPIPE:
                    print "Remote disconnect"
                    return False
        except IOError, e:
            print "Send Error: ", e
        except AttributeError, e:
            print "Socket deleted."
        return False

    def __str__(self):
        return " ".join([str(m) for m in self.members])

class PingMessage():
    def __init__(self, srcname):
        self.type = MSG_PING
        self.source = srcname

    def __str__(self):
        return 'PingMessage from %s' % str(self.source)
