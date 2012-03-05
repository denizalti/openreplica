"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: The Nameserver keeps track of the view by being involved in Paxos rounds and replies to DNS queries with the latest view.
@copyright: See LICENSE
"""
import sys
try:
    from boto.route53.connection import Route53Connection
    from concoord.route53 import *
    import boto
except:
    print "Install boto: http://github.com/boto/boto"
    
from openreplicasecret import AWSACCESSKEYID, AWSSECRETACCESSKEY
    
if __name__ == '__main__':
    zone_id = 'Z1A1MS4JFD4PLW'
    name = 'ecoviews.org.'
    type = 'A'
    values = '1.2.3.4,5.6.7.8'
    conn = Route53Connection(AWSACCESSKEYID, AWSSECRETACCESSKEY)
    print ls(conn)
    print get(conn, zone_id)
    # Add Record succeeds only when the type doesn't exist yet
    #add_record(conn, zone_id, name, type, values, ttl=600, comment="Nameserver Node")
    change_record(conn, zone_id, name, type, values)
    print ls(conn)
    print get(conn, zone_id)

    

    
