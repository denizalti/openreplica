class Test():
    def __init__(self):
        self.value = 13

    def getvalue(self):
        return self.value
    
    def __str__(self):
        return "The value is %d" % self.value
