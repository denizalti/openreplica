"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Example data storage
@copyright: See LICENSE
"""
class DataStorage():
    def __init__(self, **kwargs):
        pass
        
    def write(self, data, **kwargs):
        return open("fs", "w").write(data)
        
    def append(self, data, **kwargs):
        return open("fs", "a").append(data)

    def seek(self, byte, **kwargs):
        return open("fs", "r").seek(byte)

    def read(self, bytes=None, **kwargs):
        return open("fs", "r").read(bytes)
        
        
    
        
        
