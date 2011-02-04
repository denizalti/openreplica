'''
@author: egs
@note: This class holds enums that are widely used throughout the program
       Because it imports itself, this module MUST NOT HAVE ANY SIDE EFFECTS!!!!
@date: February 3, 2011
'''
import enums

# message types
MSG_ACCEPT, MSG_REJECT, MSG_PREPARE, MSG_PROPOSE, MSG_PERFORM, MSG_REMOVE, MSG_PING, MSG_ERROR, MSG_HELO, MSG_HELOREPLY,\
            MSG_NEW, MSG_BYE, MSG_DEBIT, MSG_DEPOSIT, MSG_OPEN, MSG_CLOSE, MSG_DONE, MSG_FAIL = range(18)

# scout and commander return values
SCOUT_NOREPLY, SCOUT_ADOPTED, SCOUT_BUSY, SCOUT_PREEMPTED = range(4)
COMMANDER_CHOSEN, COMMANDER_BUSY, COMMANDER_PREEMPTED = range(4, 7)

# node types 
NODE_ACCEPTOR, NODE_LEADER, NODE_REPLICA, NODE_CLIENT = range(4)

################# 
# Magic numbers 

# Lengths
MAXPROPOSALLENGTH = 20
PVALUELENGTH = 32
PEERLENGTH = 28
ADDRLENGTH = 15

# Command Index
COMMANDNUMBER = 0
COMMAND = 1

# integer infinity
INFINITY = 10**100

###########################
# code to convert enum variables to strings of different kinds

# convert a set of enums with a given prefix into a dictionary
def get_var_mappings(prefix):
    return dict([(varname.replace(prefix, "", 1),getattr(enums,varname)) for varname in dir(enums) if varname.startswith(prefix)]) 

# convert a set of enums with a given prefix into a list
def get_var_list(prefix):
    return [name for (name,value) in sorted(get_var_mappings(prefix).iteritems(), key=lambda (name,v): v)]

msg_names = get_var_list("MSG_")
scout_names = get_var_list("SCOUT_")
commander_names = get_var_list("COMMANDER_")
node_names = get_var_list("NODE_")

