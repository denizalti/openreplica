"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: The Nameserver keeps track of the view by being involved in Paxos rounds and replies to DNS queries with the latest view.
@copyright: See LICENSE
"""
import socket, select, signal
from time import strftime, gmtime
from concoord.utils import *
from concoord.enums import *
from concoord.pack import *
from concoord.route53 import *
try:
    import dns.exception
    import dns.message
    import dns.rcode
    import dns.opcode
    import dns.rdatatype
    import dns.name
    from dns.flags import *
except:
    print "To use the nameserver install dnspython: http://www.dnspython.org/"

try:
    from boto.route53.connection import Route53Connection
    from boto.route53.exception import DNSServerError
except:
    pass

RRTYPE = ['','A','NS','MD','MF','CNAME','SOA', 'MB', 'MG', 'MR', 'NULL',
          'WKS', 'PTR', 'HINFO', 'MINFO', 'MX', 'TXT', 'RP', 'AFSDB',
          'X25', 'ISDN', 'RT', 'NSAP', 'NSAP_PTR', 'SIG', 'KEY', 'PX',
          'GPOS', 'AAAA', 'LOC', 'NXT', '', '', 'SRV']
RRCLASS = ['','IN','CS','CH','HS']
OPCODES = ['QUERY','IQUERY','STATUS']
RCODES = ['NOERROR','FORMERR','SERVFAIL','NXDOMAIN','NOTIMP','REFUSED']

SRVNAME = '_concoord._tcp.'

class Nameserver():
    """Nameserver keeps track of the connectivity state of the system and replies to
    QUERY messages from dnsserver."""
    def __init__(self, addr, domain, route53, replicas, debug):
        self.ipconverter = '.ipaddr.'+domain+'.'
        try:
            if domain.find('.') > 0:
                self.mydomain = dns.name.Name((domain+'.').split('.'))
            else:
                self.mydomain = domain
            self.mysrvdomain = dns.name.Name((SRVNAME+domain+'.').split('.'))
        except dns.name.EmptyLabel as e:
            print "A DNS name is required. Use -n option."
            raise e

        # Replicas of the Replica
        self.replicas = replicas
        self.debug = debug

        self.route53 = route53
        if self.route53:
            try:
                from boto.route53.connection import Route53Connection
                from boto.route53.exception import DNSServerError
            except Exception as e:
                print "To use Amazon Route 53, install boto: http://github.com/boto/boto/"
                raise e

            # Check if AWS CONFIG data is present
            ROUTE53CONFIGFILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'route53.cfg')
            # Touching the CONFIG file
            with open(ROUTE53CONFIGFILE, 'a'):
                os.utime(ROUTE53CONFIGFILE, None)

            import ConfigParser
            config = ConfigParser.RawConfigParser()
            config.read(ROUTE53CONFIGFILE)

            try:
                AWS_ACCESS_KEY_ID = config.get('ENVIRONMENT', 'AWS_ACCESS_KEY_ID')
                AWS_SECRET_ACCESS_KEY = config.get('ENVIRONMENT', 'AWS_SECRET_ACCESS_KEY')
            except Exception as e:
                print "To use Route53 set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY as follows:"
                print "$ concoord route53id [AWS_ACCESS_KEY_ID]"
                print "$ concoord route53key [AWS_SECRET_ACCESS_KEY]"
                sys.exit(1)

            # initialize Route 53 connection
            self.route53_name = domain+'.'
            self.route53_conn = Route53Connection(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
            # get the zone_id for the domainname, the domainname
            # should be added to the zones beforehand
            self.route53_zone_id = self.get_zone_id(self.route53_conn, self.route53_name)
            self.updateroute53()
        else: # STANDALONE NAMESERVER
            self.addr = addr if addr else findOwnIP()
            self.udpport = 53
            self.udpsocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
            try:
                self.udpsocket.bind((self.addr,self.udpport))
                print "Connected to " + self.addr + ":" + str(self.udpport)
            except socket.error as e:
                print "Can't bind to UDP port 53: %s" % str(e)
                raise e

        # When the nameserver starts the revision number is 00 for that day
        self.revision = strftime("%Y%m%d", gmtime())+str(0).zfill(2)

    def add_logger(self, logger):
        self.logger = logger

    def udp_server_loop(self):
        while True:
            try:
                inputready,outputready,exceptready = select.select([self.udpsocket],[],[self.udpsocket])
                for s in exceptready:
                    if self.debug: self.logger.write("DNS Error", s)
                for s in inputready:
                    data,clientaddr = self.udpsocket.recvfrom(UDPMAXLEN)
                    if self.debug: self.logger.write("DNS State", "received a message from address %s" % str(clientaddr))
                    self.handle_query(data,clientaddr)
            except KeyboardInterrupt, EOFError:
                os._exit(0)
            except Exception as e:
                print "Error:", type(e), e.message
                continue
        self.udpsocket.close()
        return

    def aresponse(self, question=''):
        for address in get_addresses(self.replicas):
            yield address

    def nsresponse(self, question=''):
        # Check which Replicas are also Nameservers
        for replica in self.replicas:
            if replica.type == NODE_NAMESERVER:
                yield replica.addr

    def srvresponse(self, question=''):
        for address,port in get_addressportpairs(self.replicas):
            yield address+self.ipconverter,port

    def txtresponse(self, question=''):
        txtstr = ''
        for peer in self.replicas:
            txtstr += node_names[peer.type] +' '+ peer.addr + ':' + str(peer.port) + ';'
        return txtstr[:-1]

    def ismydomainname(self, question):
        return question.name == self.mydomain or (question.rdtype == dns.rdatatype.SRV and question.name == self.mysrvdomain)

    def should_answer(self, question):
        return (question.rdtype == dns.rdatatype.AAAA or \
                    question.rdtype == dns.rdatatype.A or \
                    question.rdtype == dns.rdatatype.TXT or \
                    question.rdtype == dns.rdatatype.NS or \
                    question.rdtype == dns.rdatatype.SRV or \
                    question.rdtype == dns.rdatatype.SOA) and self.ismydomainname(question)

    def handle_query(self, data, addr):
        query = dns.message.from_wire(data)
        response = dns.message.make_response(query)
        for question in query.question:
            if self.debug: self.logger.write("DNS State", "Received Query for %s\n" % question.name)
            if self.debug: self.logger.write("DNS State", "Mydomainname: %s Questionname: %s" % (self.mydomain, str(question.name)))
            if self.should_answer(question):
                if self.debug: self.logger.write("DNS State", "Query for my domain: %s" % str(question))
                flagstr = 'QR AA' # response, authoritative
                answerstr = ''
                if question.rdtype == dns.rdatatype.AAAA:
                    flagstr = 'QR' # response
                elif question.rdtype == dns.rdatatype.A:
                    # A Queries --> List all Replicas starting with the Leader
                    for address in self.aresponse(question):
                        answerstr += self.create_answer_section(question, addr=address)
                elif question.rdtype == dns.rdatatype.TXT:
                    # TXT Queries --> List all nodes
                    answerstr = self.create_answer_section(question, txt=self.txtresponse(question))
                elif question.rdtype == dns.rdatatype.NS:
                    # NS Queries --> List all Nameserver nodes
                    for address in self.nsresponse(question):
                        #answerstr += self.create_answer_section(question, name=address)
                        answerstr += self.create_answer_section(question, addr=address)
                elif question.rdtype == dns.rdatatype.SOA:
                    # SOA Query --> Reply with Metadata
                    answerstr = self.create_soa_answer_section(question)
                elif question.rdtype == dns.rdatatype.SRV:
                    # SRV Queries --> List all Replicas with addr:port
                    for address,port in self.srvresponse(question):
                        answerstr += self.create_srv_answer_section(question, addr=address, port=port)
                responsestr = self.create_response(response.id,opcode=dns.opcode.QUERY,
                                                   rcode=dns.rcode.NOERROR,flags=flagstr,
                                                   question=question.to_text(),answer=answerstr,
                                                   authority='',additional='')
                response = dns.message.from_text(responsestr)
            else:
                if self.debug: self.logger.write("DNS State", "UNSUPPORTED QUERY, %s" %str(question))
                return
        if self.debug: self.logger.write("DNS State", "RESPONSE:\n%s\n---\n" % str(response))

        towire = response.to_wire()
        self.udpsocket.sendto(towire, addr)

    def create_response(self, id, opcode=0, rcode=0, flags='', question='', answer='', authority='', additional=''):
        answerstr     = ';ANSWER\n'     + answer     + '\n' if answer != '' else ''
        authoritystr  = ';AUTHORITY\n'  + authority  + '\n' if authority != '' else ''
        additionalstr = ';ADDITIONAL\n' + additional + '\n' if additional != '' else ''

        responsestr = "id %s\nopcode %s\nrcode %s\nflags %s\n;QUESTION\n%s\n%s%s%s" % (str(id),
                                                                                       OPCODES[opcode],
                                                                                       RCODES[rcode],
                                                                                       flags,
                                                                                       question,
                                                                                       answerstr, authoritystr, additionalstr)
        return responsestr

    def create_srv_answer_section(self, question, ttl=30, rrclass=1, priority=0, weight=100, port=None, addr=''):
        answerstr = "%s %d %s %s %d %d %d %s\n" % (str(question.name), ttl, RRCLASS[rrclass], RRTYPE[question.rdtype], priority, weight, port, addr)
        return answerstr

    def create_mx_answer_section(self, question, ttl=30, rrclass=1, priority=0, addr=''):
        answerstr = "%s %d %s %s %d %s\n" % (str(question.name), ttl, RRCLASS[rrclass], RRTYPE[question.rdtype], priority, addr)
        return answerstr

    def create_soa_answer_section(self, question, ttl=30, rrclass=1):
        refreshrate = 86000 # time (in seconds) when the slave DNS server will refresh from the master
        updateretry = 7200  # time (in seconds) when the slave DNS server should retry contacting a failed master
        expiry = 360000     # time (in seconds) that a slave server will keep a cached zone file as valid
        minimum = 432000    # default time (in seconds) that the slave servers should cache the Zone file
        answerstr = "%s %d %s %s %s %s (%s %d %d %d %d)" % (str(question.name), ttl, RRCLASS[rrclass],
                                                            RRTYPE[question.rdtype],
                                                            str(self.mydomain),
                                                            'dns-admin.'+str(self.mydomain),
                                                            self.revision,
                                                            refreshrate,
                                                            updateretry,
                                                            expiry,
                                                            minimum)
        return answerstr

    def create_answer_section(self, question, ttl=30, rrclass=1, addr='', txt=None):
        if question.rdtype == dns.rdatatype.A:
            resp = str(addr)
        elif question.rdtype == dns.rdatatype.TXT:
            resp = '"%s"' % txt
        elif question.rdtype == dns.rdatatype.NS:
            resp = str(addr)
        answerstr = "%s %s %s %s %s\n" % (str(question.name), str(ttl), str(RRCLASS[rrclass]), str(RRTYPE[question.rdtype]), resp)
        return answerstr

    def create_authority_section(self, question, ttl='30', rrclass=1, rrtype=1, nshost=''):
        authoritystr = "%s %s %s %s %s\n" % (str(question.name), str(ttl), str(RRCLASS[rrclass]), str(RRTYPE[rrtype]), str(nshost))
        return authoritystr

    def create_additional_section(self, question, ttl='30', rrclass=1, rrtype=1, addr=''):
        additionalstr = "%s %s %s %s %s\n" % (str(question.name), str(ttl), str(RRCLASS[rrclass]), str(RRTYPE[rrtype]), str(addr))
        return additionalstr

    def update(self):
        self.updaterevision()
        if self.route53:
            self.updateroute53()

    ########## ROUTE 53 ##########

    def get_zone_id(self, conn, name):
        response = conn.get_all_hosted_zones()
        for zoneinfo in response['ListHostedZonesResponse']['HostedZones']:
            if zoneinfo['Name'] == name:
                return zoneinfo['Id'].split("/")[-1]

    def append_record(self, conn, hosted_zone_id, name, type, newvalues, ttl=600,
                      identifier=None, weight=None, comment=""):
        values = get_values(conn, hosted_zone_id, name, type)
        if values == '':
            values = newvalues
        else:
            values += ',' + newvalues
        change_record(conn, hosted_zone_id, name, type, values, ttl=ttl, identifier=identifier, weight=weight, comment=comment)

    def get_values(self, conn, hosted_zone_id, name, type):
        response = conn.get_all_rrsets(hosted_zone_id, 'A', name)
        for record in response:
            if record.type == type:
                values = ','.join(record.resource_records)
        return values

    def add_record_bool(self, conn, zone_id, name, type, values, ttl=600, identifier=None, weight=None, comment=""):
        # Add Record succeeds only when the type doesn't exist yet
        try:
            add_record(conn, zone_id, name, type, values, ttl=ttl, identifier=identifier, weight=weight, comment=comment)
        except DNSServerError as e:
            return False
        return True

    def change_record_bool(self, conn, zone_id, name, type, values, ttl=600, identifier=None, weight=None, comment=""):
        try:
            change_record(conn, zone_id, name, type, values, ttl=ttl, identifier=identifier, weight=weight, comment=comment)
        except DNSServerError as e:
            print e
            return False
        return True

    def append_record_bool(self, conn, zone_id, name, type, values, ttl=600, identifier=None, weight=None, comment=""):
        try:
            append_record(conn, zone_id, name, type, values, ttl=ttl, identifier=identifier, weight=weight, comment=comment)
        except DNSServerError as e:
            print e
            return False
        return True

    def del_record_bool(self, conn, zone_id, name, type, values, ttl=600, identifier=None, weight=None, comment=""):
        try:
            del_record(conn, zone_id, name, type, values, ttl=ttl, identifier=identifier, weight=weight, comment=comment)
        except DNSServerError as e:
            print e

    def route53_a(self):
        values = []
        for address in get_addresses(self.replicas):
            values.append(address)
        return ','.join(values)

    def route53_srv(self):
        values = []
        priority = 0
        weight = 100
        for address,port in get_addressportpairs(self.replicas):
            values.append('%d %d %d %s' % (priority, weight, port, address+self.ipconverter))
        return ','.join(values)

    def route53_txt(self):
        txtstr = self.txtresponse()
        lentxtstr = len(txtstr)
        strings = ["\""+txtstr[0:253]+"\""]
        if lentxtstr > 253:
            # cut the string in chunks
            for i in range(lentxtstr/253):
                strings.append("\""+txtstr[i*253:(i+1)*253]+"\"")
        return strings

    def updateroute53(self):
        # type A: update only if added node is a Replica
        rtype = 'A'
        newvalue = self.route53_a()
        self.change_record_bool(self.route53_conn, self.route53_zone_id,
                           self.route53_name, 'A', newvalue)
        # type SRV: update only if added node is a Replica
        rtype = 'SRV'
        newvalue = self.route53_srv()
        self.change_record_bool(self.route53_conn, self.route53_zone_id,
                           self.route53_name, 'SRV', newvalue)
        # type TXT: All Nodes
        rtype = 'TXT'
        newvalue = ','.join(self.route53_txt())
        self.change_record_bool(self.route53_conn, self.route53_zone_id,
                           self.route53_name, 'TXT', newvalue)

    def updaterevision(self):
        if self.debug: self.logger.write("State", "Updating Revision -- from: %s" % self.revision)
        if strftime("%Y%m%d", gmtime()) in self.revision:
            rno = int(self.revision[-2]+self.revision[-1])
            rno += 1
            self.revision = strftime("%Y%m%d", gmtime())+str(rno).zfill(2)
        else:
            self.revision = strftime("%Y%m%d", gmtime())+str(0).zfill(2)
        if self.debug: self.logger.write("State", "Updating Revision -- to: %s" % self.revision)
