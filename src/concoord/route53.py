"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: The Nameserver keeps track of the view by being involved in Paxos rounds and replies to DNS queries with the latest view.
@copyright: See LICENSE
"""
try:
    from boto.route53.connection import Route53Connection
except:
    print "Install dnspython: http://www.dnspython.org/"

from openreplicasecret import AWSACCESSKEYID, AWSSECRETACCESSKEY

def createhostedzone(route53conn, zonename):
    return route53conn.create_hosted_zone('ecoviews.org')

def listzones(route53conn):
    results = route53conn.get_all_hosted_zones()
    output = ''
    for zone in results['ListHostedZonesResponse']['HostedZones']:
        output +=  zone['Name'] + "\n"
        output += "\t%s\n" % zone['Id']
        zone_id = zone['Id'].replace('/hostedzone/', '')
        zones[zone['Name']] = zone_id
        sets = route53conn.get_all_rrsets(zone_id)
        for rset in sets:
            output += "\t%s: %s %s @ %s\n" % (rset.name, rset.type, rset.resource_records, rset.ttl)
    return output
    
if __name__ == '__main__':
    zones = {}
    route53conn = Route53Connection(AWSACCESSKEYID, AWSSECRETACCESSKEY)
    
    print listzones(route53conn)
    
    # add an A record
    xml = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
    <ChangeResourceRecordSetsRequest xmlns=\"https://route53.amazonaws.com/doc/2010-10-01/\">
        <ChangeBatch>
            <Comment>
            New A Record Test: 1.2.3.4
            </Comment>
            <Changes>
                <Change>
                    <Action>CREATE</Action>
                    <ResourceRecordSet>
                        <Name>ecoviews.org.</Name>
                        <Type>A</Type>
                        <TTL>300</TTL>
                        <ResourceRecords>
                            <ResourceRecord>
                                <Value>1.2.3.4</Value>
                            </ResourceRecord>
                        </ResourceRecords>
                    </ResourceRecordSet>
                </Change>          
            </Changes>
        </ChangeBatch>
    </ChangeResourceRecordSetsRequest>"""
    response = route53conn.change_rrsets(zones['ecoviews.org.'], xml)
    
