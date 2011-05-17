class Membership():
    """Object to keep track of members in a system.
    Supports three functions:
    - add: adds a member
    - remove: removes a member
    """
    def __init__(self):
        self.members = set()

    def add(self, args, _paxi_designated, _paxi_client_cmdno, _paxi_me):
        member = args[0]
        if member not in self.members:
            self.members.add(member)
            return 0
        
    def remove(self, args, _paxi_designated, _paxi_client_cmdno, _paxi_me):
        member = args[0]
        if member in self.members:
            self.members.remove(member)
            return 0
        else:
            raise KeyError(member)
        
    def __str__(self):
        return " ".join([str(m) for m in self.members])
    
        
        
