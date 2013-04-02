"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: The Nameserver keeps track of the view by being involved in Paxos rounds and replies to DNS queries with the latest view.
@copyright: See LICENSE
"""
import sys
try:
    from boto.route53.connection import Route53Connection
    from boto.route53.exception import DNSServerError
    from concoord.route53 import *
    import boto
except:
    print "Install boto: http://github.com/boto/boto"

def get_zone_id(conn, name):
    response = conn.get_all_hosted_zones()
    for zoneinfo in response['ListHostedZonesResponse']['HostedZones']:
        if zoneinfo['Name'] == name:
            return zoneinfo['Id'].split("/")[-1]

def append_record(conn, hosted_zone_id, name, type, newvalues, ttl=600,
                   identifier=None, weight=None, comment=""):
    values = get_values(conn, hosted_zone_id, name, type)
    if values == '':
        values = newvalues
    else:
        values += ',' + newvalues
    change_record(conn, hosted_zone_id, name, type, values, ttl=ttl, identifier=identifier, weight=weight, comment=comment)

def get_values(conn, hosted_zone_id, name, type):
    response = conn.get_all_rrsets(hosted_zone_id, 'A', name)
    for record in response:
        if record.type == type:
            values = ','.join(record.resource_records)
    return values

def add_record_bool(conn, zone_id, name, type, values, ttl=600, identifier=None, weight=None, comment=""):
    # Add Record succeeds only when the type doesn't exist yet
    print "Adding record..."
    try:
        add_record(conn, zone_id, name, type, values, ttl=ttl, identifier=identifier, weight=weight, comment=comment)
    except DNSServerError as e:
        return False
    return True

def change_record_bool(conn, zone_id, name, type, values, ttl=600, identifier=None, weight=None, comment=""):
    try:
        change_record(conn, zone_id, name, type, values, ttl=ttl, identifier=identifier, weight=weight, comment=comment)
    except DNSServerError as e:
        print e
        return False
    return True

def append_record_bool(conn, zone_id, name, type, values, ttl=600, identifier=None, weight=None, comment=""):
    try:
        append_record(conn, zone_id, name, type, values, ttl=ttl, identifier=identifier, weight=weight, comment=comment)
    except DNSServerError as e:
        print e
        return False
    return True

def del_record_bool(conn, zone_id, name, type, values, ttl=600, identifier=None, weight=None, comment=""):
    try:
        del_record(conn, zone_id, name, type, values, ttl=ttl, identifier=identifier, weight=weight, comment=comment)
    except DNSServerError as e:
        print e

if __name__ == '__main__':
    try:
        CONFIGDICT = load_configdict(sys.argv[1])
        AWS_ACCESS_KEY_ID = CONFIGDICT['AWS_ACCESS_KEY_ID']
        AWS_SECRET_ACCESS_KEY = CONFIGDICT['AWS_SECRET_ACCESS_KEY']
    except:
        print "To set Amazon Route 53 keys, pass the configuration file path"

    zone_id = 'Z1A1MS4JFD4PLW'
    name = 'ecoviews.org.'
    type = 'A'
    #values = ''
    conn = Route53Connection(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
    print get(conn, zone_id)
    #print "Changing record..."
    #values = "5.6.7.8"
    #change_record_bool(conn, zone_id, name, type, values)
    #print get(conn, zone_id)
    #print "Appending to record..."
    #values = "3.4.5.6"
    #append_record_bool(conn, zone_id, name, type, values)
    #print get(conn, zone_id)
    #values = get_values(conn, zone_id, name, type)
    #print "Deleting record..."
    #del_record_bool(conn, zone_id, name, type, values)
    #print get(conn, zone_id)

    

    
