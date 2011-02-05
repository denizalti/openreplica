'''
@author: egs
@note: This class holds enums that are widely used throughout the program
       Because it imports itself, this module MUST NOT HAVE ANY SIDE EFFECTS!!!!
@date: February 3, 2011
'''
import enums

# message types
MSG_ACCEPT, MSG_REJECT, MSG_PREPARE, MSG_PROPOSE, MSG_PERFORM, MSG_RESPONSE, \
    MSG_HELO, MSG_HELOREPLY, MSG_BYE, \
    MSG_CLIENTREQUEST, MSG_CLIENTREPLY = range(11)

# scout and commander return values
LEADERMSG_NOREPLY, LEADERMSG_SCOUT_ADOPTED, LEADERMSG_SCOUT_BUSY, LEADERMSG_SCOUT_PREEMPTED, \
LEADERMSG_COMMANDER_CHOSEN,LEADERMSG_COMMANDER_BUSY, LEADERMSG_COMMANDER_PREEMPTED = range(7)

# node types 
NODE_ACCEPTOR, NODE_LEADER, NODE_REPLICA, NODE_CLIENT = range(4)

###########################
# code to convert enum variables to strings of different kinds

# convert a set of enums with a given prefix into a dictionary
def get_var_mappings(prefix):
    return dict([(getattr(enums,varname),varname.replace(prefix, "", 1)) for varname in dir(enums) if varname.startswith(prefix)]) 

# convert a set of enums with a given prefix into a list
def get_var_list(prefix):
    return [name for (value,name) in sorted(get_var_mappings(prefix).iteritems())]

msg_names = get_var_list("MSG_")
leadermsg_names = get_var_list("LEADERMSG_")
node_names = get_var_list("NODE_")

