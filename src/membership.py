class Membership():
    def __init__(self):
        self.members = set() # Members stored as 'addr:port'

    def add(self, args):
        member = args[0]
        if member not in self.members:
            self.members.add(member)
            return "MEMBER %s ADDED" % member
        else:
            return "MEMBER EXISTS"
        
    def delete(self, args):
        member = args[0]
        if member in self.members:
            self.members.remove(member)
            return "MEMBER %s DELETED" % member
        else:
            return "NO SUCH MEMBER"
        
    def who(self, args):
        return self.__str__()
        
    def __str__(self):
        temp = ''
        for member in self.members:
            temp += str(member)+' '
        return temp
        
    
        
        
