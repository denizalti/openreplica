class Test():
    def __init__(self, **kwargs):
        self.value = 13

    def getvalue(self, **kwargs):
        return self.value
    
    def __str__(self, **kwargs):
        return "The value is %d" % self.value
