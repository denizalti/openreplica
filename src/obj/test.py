class Test():
    """Test object that supports the following function:
    - append: appends given string argument to the state string
    - state: returns the state of the object
    """
    def __init__(self):
        self.state = ""

    def append(self, args):
        try:
            self.state += args[0]
        except:
            return 'FAIL'
        return 'SUCCESS'

    def state(self,args):
        return self.state

    def __str__(self):
        return self.state
