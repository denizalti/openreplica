
class Test():
    def __init__(self):
        self.state = ""

    def append(self, args):
        self.state += args[0]

    def __str__(self):
        return self.state
