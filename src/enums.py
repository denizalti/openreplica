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
         MSG_UPDATE, MSG_UPDATEREPLY, \
         MSG_PERFORM, MSG_RESPONSE, \
         MSG_CLIENTREQUEST, MSG_CLIENTREPLY, MSG_CLIENTMETAREPLY, MSG_INCCLIENTREQUEST, \
         MSG_GARBAGECOLLECT, \
         MSG_QUERY, MSG_QUERYREPLY, \
         MSG_OUTPUT, \
         MSG_REFER = range(23)

# node types 
NODE_ACCEPTOR, NODE_REPLICA, NODE_LEADER, NODE_CLIENT, NODE_TRACKER, NODE_NAMESERVER, NODE_COORDINATOR = range(7)

# error_types
ERR_NOERROR, ERR_NOTLEADER, ERR_INITIALIZING = range(3)

# command result
META = 'META'
BLOCK = 'BLOCK'
UNBLOCK = 'UNBLOCK'

#executed indexing
RCODE, RESULT, UNBLOCKED = range(3)

# message states
ACK_NOTACKED, ACK_ACKED = range(2)

# client reply codes
CR_OK, CR_INPROGRESS, CR_LEADERNOTREADY, CR_REJECTED, CR_EXCEPTION, CR_BLOCK, CR_UNBLOCK, CR_META = range(8)

# timeouts
ACKTIMEOUT = 1
LIVENESSTIMEOUT = 30
NASCENTTIMEOUT = 20 * ACKTIMEOUT
CLIENTRESENDTIMEOUT = 5
BACKOFFDECREASETIMEOUT = 30
TESTTIMEOUT = 1

# magic numbers
## ballot
BALLOTNO = 0
BALLOTNODE = 1
##backoff
BACKOFFINCREASE = 0.1

METACOMMANDS = set(["add_acceptor", "del_acceptor", "add_replica", "del_replica", "garbage_collect"])
WINDOW = 20
GARBAGEPERIOD = 100

NOOP = "do_noop"

# UDPPACKETLEN
UDPMAXLEN = 1024

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
err_types = get_var_list("ERR_")
cr_codes = get_var_list("CR_")
