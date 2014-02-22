'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: This class holds enums that are widely used throughout the program
       Because it imports itself, this module MUST NOT HAVE ANY SIDE EFFECTS!!!!
@copyright: See LICENSE
'''
import enums

# message types
MSG_CLIENTREQUEST, MSG_CLIENTREPLY, MSG_INCCLIENTREQUEST, \
    MSG_PREPARE, MSG_PREPARE_ADOPTED, MSG_PREPARE_PREEMPTED, MSG_PROPOSE, \
    MSG_PROPOSE_ACCEPT, MSG_PROPOSE_REJECT, \
    MSG_HELO, MSG_HELOREPLY, MSG_PING, MSG_PINGREPLY, \
    MSG_UPDATE, MSG_UPDATEREPLY, \
    MSG_PERFORM, MSG_RESPONSE, \
    MSG_GARBAGECOLLECT, MSG_STATUS, MSG_ISSUE = range(20)

# message fields
FLD_ID, FLD_TYPE, FLD_SRC, FLD_BALLOTNUMBER, FLD_COMMANDNUMBER, \
FLD_PROPOSAL, FLD_DECISIONS, \
FLD_REPLY, FLD_REPLYCODE, FLD_INRESPONSETO, FLD_SNAPSHOT, FLD_PVALUESET, FLD_LEADER, \
FLD_TOKEN, FLD_CLIENTBATCH, FLD_SERVERBATCH, FLD_SENDCOUNT = range(17)

# node types
NODE_CLIENT, NODE_ACCEPTOR, NODE_REPLICA, NODE_NAMESERVER = range(4)

# error_types
ERR_NOERROR, ERR_NOTLEADER, ERR_INITIALIZING = range(3)

# nameserver service types
NS_MASTER, NS_SLAVE, NS_ROUTE53 = range(1,4)

# proxy types
PR_BASIC, PR_BLOCK, PR_CBATCH, PR_SBATCH = range(4)

# command result
META = 'META'
BLOCK = 'BLOCK'
UNBLOCK = 'UNBLOCK'

# executed indexing
EXC_RCODE, EXC_RESULT, EXC_UNBLOCKED = range(3)

# client reply codes
CR_OK, CR_INPROGRESS, CR_LEADERNOTREADY, CR_REJECTED, \
CR_EXCEPTION, CR_BLOCK, CR_UNBLOCK, CR_META, CR_BATCH = range(9)

# timeouts
ACKTIMEOUT = 1
LIVENESSTIMEOUT = 5
NASCENTTIMEOUT = 20 * ACKTIMEOUT
CLIENTRESENDTIMEOUT = 5
BACKOFFDECREASETIMEOUT = 30
TESTTIMEOUT = 1
BOOTSTRAPCONNECTTIMEOUT = 60

# ballot
BALLOTNO = 0
BALLOTNODE = 1

# backoff
BACKOFFINCREASE = 0.1

METACOMMANDS = set(["_add_node", "_del_node", "_garbage_collect"])
WINDOW = 10
GARBAGEPERIOD = 100000

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
err_types = get_var_list("ERR_")
cr_codes = get_var_list("CR_")
ns_services = get_var_list("NS_")
