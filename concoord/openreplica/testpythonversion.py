'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Script to check Python installation version
@copyright: See LICENSE
'''
import sys

def checkpythonversion():
    version = sys.version_info.major*100 + sys.version_info.minor * 10 + sys.version_info.micro
    if version > 266:
        return 0
    return 1

if __name__=='__main__':
    sys.exit(checkpythonversion())
