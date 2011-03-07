'''
@author: egs
@note: This class holds enums that are widely used throughout the program
       Because it imports itself, this module MUST NOT HAVE ANY SIDE EFFECTS!!!!
@date: February 3, 2011
'''
import enums

# message types
MSG_ACK, \
         MSG_PREPARE, MSG_PREPARE_ADOPTED, MSG_PREPARE_PREEMPTED, MSG_PROPOSE, MSG_PROPOSE_ACCEPT, MSG_PROPOSE_REJECT, \
         MSG_HELO, MSG_HELOREPLY, MSG_BYE, \
         MSG_PERFORM, MSG_RESPONSE, \
         MSG_CLIENTREQUEST, MSG_CLIENTREPLY = range(14)

# node types 
NODE_ACCEPTOR, NODE_LEADER, NODE_REPLICA, NODE_CLIENT = range(4)

# command states
CMD_EXECUTED, CMD_DECIDED = range(2)

# message states
ACK_NOTACKED, ACK_ACKED = range(2)

# timeouts
ACKTIMEOUT = 1
LIVENESSTIMEOUT = 60
HELOTIMEOUT = 20 * ACKTIMEOUT

# magic numbers
COMMANDSTATE = 0
COMMAND = 1
COMMANDRESULT = 2

CLIENTRESENDTIMEOUT = 30

METACOMMANDS = set(["add_acceptor", "del_acceptor", "add_replica", "del_replica"])
WINDOW = 3

###########################
# code to convert enum variables to strings of different kinds

# convert a set of enums with a given prefix into a dictionary
def get_var_mappings(prefix):
    """Returns a dictionary with <enumvalue, enumname> mappings"""
    return dict([(getattr(enums,varname),varname.replace(prefix, "", 1)) for varname in dir(enums) if varname.startswith(prefix)]) 

# convert a set of enums with a given prefix into a list
def get_var_list(prefix):
    """Returns a list of enumnames"""
    return [name for (value,name) in sorted(get_var_mappings(prefix).iteritems())]

msg_names = get_var_list("MSG_")
node_names = get_var_list("NODE_")
cmd_states = get_var_list("CMD_")
msg_states = get_var_list("ACK_")
