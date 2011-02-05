
class Test():
    def __init__(self):
        self.state = ""

    def append(self, args):
        try:
            self.state += args[0]
        except:
            return 'FAIL'
        return 'SUCCESS'

    def __str__(self):
        return self.state
