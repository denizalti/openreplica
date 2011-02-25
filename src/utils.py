import socket

def findOwnIP():
    """Retrieves the hostname of the caller"""
    return socket.gethostbyname(socket.gethostname())

logprefix = ""

def setlogprefix(logpre):
    global logprefix
    logprefix = logpre
    
def logger(logstr):
    print "[%s] %s" % (logprefix, logstr)
    
