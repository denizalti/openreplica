import socket

def findOwnIP():
    """Retrieves the hostname of the caller"""
    return socket.gethostbyname(socket.gethostname())

logprefix = None

def setlogprefix(logpre):
    global logprefix
    logprefix = logpre

def logger(logstr):
    if logprefix:
        print "[%s] %s" % (logprefix, logstr)
    
