'''
@author: egs
@note: This class holds enums that are widely used throughout the program
       Because it imports itself, this module MUST NOT HAVE ANY SIDE EFFECTS!!!!
@date: February 3, 2011
'''
import enums

# message types
MSG_ACCEPT, MSG_REJECT, MSG_PREPARE, MSG_PROPOSE, MSG_PERFORM, \
    MSG_HELO, MSG_HELOREPLY, MSG_BYE, \
    MSG_CLIENTREQUEST, MSG_CLIENTREPLY = range(10)

# scout and commander return values
SCOUT_NOREPLY, SCOUT_ADOPTED, SCOUT_BUSY, SCOUT_PREEMPTED = range(4)
COMMANDER_CHOSEN, COMMANDER_BUSY, COMMANDER_PREEMPTED = range(4,7)

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
scout_names = get_var_list("SCOUT_")
commander_names = get_var_list("COMMANDER_")
node_names = get_var_list("NODE_")

