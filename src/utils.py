import hashlib
import socket
import random
import struct

def createID(addr,port):
    random.seed(addr+str(port))
    return random.randint(0, 1000000)

def findOwnIP():
    return socket.gethostbyname(socket.gethostname())

# pvalue calculations
# Returns the union of two pvalue arrays
def union(pvalues1, pvalues2):
    for pvalue in pvalues2:
        if pvalue in pvalues1:
            pass
        else:
            pvalues1.append(pvalue)
    return pvalues1

# Returns the max of a pvalue array            
def max(pvalues):
    maxpvalue = pvalue(ballotnumber=(0,0),commandnumber=0,proposal="")
    for pvalue in pvalues:
        if pvalue > maxpvalue:
            maxpvalue = pvalue
    return maxpvalue
