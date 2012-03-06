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

from credentials import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY

def get_zone_id(conn, name):
    response = conn.get_all_hosted_zones()
    for zoneinfo in response['ListHostedZonesResponse']['HostedZones']:
        if zoneinfo['Name'] == name:
            return zoneinfo['Id'].split("/")[-1]

def append_to_record(conn, hosted_zone_id, name, rtype, newvalues, ttl=600,
                   identifier=None, weight=None, comment=""):
    values = get_values(conn, hosted_zone_id, name, rtype)
    if values == '':
        values = newvalues
    else:
        values += ',' + newvalues
    change_record(conn, zone_id, name, rtype, values)

def get_values(conn, hosted_zone_id, name, rtype, ttl=600,
                   identifier=None, weight=None, comment=""):
    response = conn.get_all_rrsets(hosted_zone_id, 'A', name)
    for record in response:
        if record.type == rtype:
            values = ','.join(record.resource_records)
    return values

if __name__ == '__main__':
    zone_id = 'Z1A1MS4JFD4PLW'
    name = 'ecoviews.org.'
    rtype = 'A'
    values = "1.2.3.4"
    conn = Route53Connection(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
    print get_zone_id(conn, name)
    # Add Record succeeds only when the type doesn't exist yet
    print "Adding record..."
    try:
        add_record(conn, zone_id, name, rtype, values, ttl=600, comment="Add Test")
    except DNSServerError as e:
        if e.error_code == 'InvalidChangeBatch':
            print "Record already exists.."
    print get(conn, zone_id)
    print "Changing record..."
    values = "5.6.7.8"
    try:
        change_record(conn, zone_id, name, rtype, values)
    except DNSServerError as e:
        print e
    print get(conn, zone_id)
    print "Appending to record..."
    values = "3.4.5.6"
    try:
        append_to_record(conn, zone_id, name, rtype, values)
    except DNSServerError as e:
        print e
    print get(conn, zone_id)
    values = get_values(conn, zone_id, name, rtype)
    print "Deleting record..."
    try:
        del_record(conn, zone_id, name, rtype, values, ttl=600, comment="Delete Test")
    except DNSServerError as e:
        print e
    print get(conn, zone_id)

    

    
