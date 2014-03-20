#!/usr/bin/env python
'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: openreplica script
@date: February 2013
@copyright: See LICENSE
'''
import argparse
import signal
from time import sleep,time
import os, sys, time, shutil
import ast, _ast
import ConfigParser
from concoord.enums import *
from concoord.safetychecker import *
from concoord.proxygenerator import *
from concoord.openreplica.ec2manager import *

HELPSTR = "openreplica, version 1.1.0-release:\n\
openreplica config - prints config file\n\
openreplica sshkey [sshkeyfilename] - adds sshkey filename to config\n\
openreplica username [ssh username] - adds ssh username to config\n\
openreplica node [publicdns] - adds public dns for node to config\n\
openreplica replica [concoord arguments] - starts a replica node on EC2\n\
openreplica nameserver [concoord arguments] - starts a nameserver node on EC2\n\
openreplica ec2 - starts the EC2 Manager"

OPENREPLICACONFIGFILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'openreplica.cfg')
config = ConfigParser.RawConfigParser()

def touch_config_file():
    with open(OPENREPLICACONFIGFILE, 'a'):
        os.utime(OPENREPLICACONFIGFILE, None)

def read_config_file():
    config.read(OPENREPLICACONFIGFILE)
    section = 'ENVIRONMENT'
    options = ['NODES', 'SSH_KEY_FILE', 'USERNAME']
    rewritten = True
    if not config.has_section(section):
        rewritten = True
        config.add_section(section)
    for option in options:
        if not config.has_option(section, option):
            rewritten = True
            config.set(section, option, '')
    if rewritten:
        # Write to CONFIG file
        with open(OPENREPLICACONFIGFILE, 'wb') as configfile:
            config.write(configfile)
        config.read(OPENREPLICACONFIGFILE)
    nodes = config.get('ENVIRONMENT', 'NODES')
    sshkeyfile = config.get('ENVIRONMENT', 'SSH_KEY_FILE')
    username = config.get('ENVIRONMENT', 'USERNAME')

    return (nodes,sshkeyfile,username)

def print_config_file():
    print "NODES= %s\nSSH_KEY_FILE= %s\nUSERNAME= %s" % read_config_file()

def add_node_to_config(node):
    nodes,sshkeyfile,username = read_config_file()
    ec2manager = EC2Manager(nodes, sshkeyfile, username)
    if not ec2manager.username:
        print "Add a username to connect to the nodes"
        return
    # First check if the node is eligible
    cmd = ["ssh", ec2manager.username+'@'+node, 'python -V']
    ssh = subprocess.Popen(cmd, shell=False,
                     stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE)
    ec2manager._waitforall([ssh])
    result = ssh.stdout.readlines()
    output = ssh.stderr.readlines()[0]
    versionmajor, versionminor, versionmicro = output.strip().split()[1].split('.')
    version = int(versionmajor)*100 + int(versionminor) * 10 + int(versionmicro)
    if version < 266:
        print "Python should be updated to 2.7 or later on this machine. Attempting update."
        cmds = []
        cmds.append("sudo yum install make automake gcc gcc-c++ kernel-devel git-core -y")
        cmds.append("sudo yum install python27-devel -y")
        cmds.append("sudo rm /usr/bin/python")
        cmds.append("sudo ln -s /usr/bin/python2.7 /usr/bin/python")
        cmds.append("sudo cp /usr/bin/yum /usr/bin/_yum_before_27")
        cmds.append("sudo sed -i s/python/python2.6/g /usr/bin/yum")
        cmds.append("sudo sed -i s/python2.6/python2.6/g /usr/bin/yum")
        cmds.append("sudo curl -o /tmp/ez_setup.py https://sources.rhodecode.com/setuptools/raw/bootstrap/ez_setup.py")
        cmds.append("sudo /usr/bin/python27 /tmp/ez_setup.py")
        cmds.append("sudo /usr/bin/easy_install-2.7 pip")
        cmds.append("sudo pip install virtualenv")
        for cmd in cmds:
            p = ec2manager._issuecommand(cmd)

        # Check the version on node again
        cmd = ["ssh", ec2manager.username+'@'+node, 'python -V']
        ssh = subprocess.Popen(cmd, shell=False,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
        ec2manager._waitforall([ssh])
        result = ssh.stdout.readlines()
        output = ssh.stderr.readlines()[0]
        versionmajor, versionminor, versionmicro = output.strip().split()[1].split('.')
        version = int(versionmajor)*100 + int(versionminor) * 10 + int(versionmicro)
        if version < 266:
            print "Remote update failed. To update the node by sshing, you can follow the steps below:"
            print "Install build tools first: "
            print "sudo yum install make automake gcc gcc-c++ kernel-devel git-core -y"
            print "Install Python 2.7 and change python symlink: "
            print "$ sudo yum install python27-devel -y"
            print "$ sudo rm /usr/bin/python"
            print "$ sudo ln -s /usr/bin/python2.7 /usr/bin/python"
            print "Keep Python2.6 for yum: "
            print "$ sudo cp /usr/bin/yum /usr/bin/_yum_before_27"
            print "$ sudo sed -i s/python/python2.6/g /usr/bin/yum"
            print "$ sudo sed -i s/python2.6/python2.6/g /usr/bin/yum"
            print "Install pip for Python2.7: "
            print "$ sudo curl -o /tmp/ez_setup.py https://sources.rhodecode.com/setuptools/raw/bootstrap/ez_setup.py"
            print "$ sudo /usr/bin/python27 /tmp/ez_setup.py"
            print "$ sudo /usr/bin/easy_install-2.7 pip"
            print "$ sudo pip install virtualenv"
            return
    if nodes == '':
        # There are no nodes
        newnodes = node
    elif nodes.find(',')!=-1:
        # There are multiple nodes
        if node in nodes.split(','):
            print "Node is already in the CONFIG file."
            return
        newnodes = nodes+','+node
    else:
        # There is only one node
        if node == nodes:
            print "Node is already in the CONFIG file."
            return
        newnodes = nodes+','+node

    # Write to CONFIG file
    config.set('ENVIRONMENT', 'NODES', newnodes)
    with open(OPENREPLICACONFIGFILE, 'wb') as configfile:
        config.write(configfile)

def add_username_to_config(newusername):
    nodes,sshkeyfile,username = read_config_file()
    if username and username == newusername:
        print "USERNAME is already in the CONFIG file."
        return
    # Write to CONFIG file
    config.set('ENVIRONMENT', 'USERNAME', newusername)
    with open(OPENREPLICACONFIGFILE, 'wb') as configfile:
        config.write(configfile)

def add_sshkeyfile_to_config(newsshkeyfile):
    nodes,sshkeyfile,username = read_config_file()
    if sshkeyfile and sshkeyfile == newsshkeyfile:
        print "SSH_KEY_FILE is already in the CONFIG file."
        return
    # Write to CONFIG file
    config.set('ENVIRONMENT', 'SSH_KEY_FILE', newsshkeyfile)
    with open(OPENREPLICACONFIGFILE, 'wb') as configfile:
        config.write(configfile)

def start_node(nodetype):
    ec2manager = EC2Manager(*read_config_file())

    i = random.choice(ec2manager.instances)
    if nodetype == NODE_REPLICA:
        print "Starting replica on %s" % str(i)
        cmd = ["ssh", ec2manager.username+'@'+i, 'concoord replica ' + ' '.join(sys.argv[1:])]
        p = ec2manager._issuecommand(cmd)
    elif nodetype == NODE_NAMESERVER:
        # Check if nameserver can connect to port 53
        cmd = ["ssh", "-t", ec2manager.username+'@'+i,
               "sudo python -c \"exec(\\\"import socket\\nsocket.socket(socket.AF_INET,socket.SOCK_STREAM).bind(('localhost', 53))\\\")\""]

        ssh = subprocess.Popen(cmd, shell=False,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
        ec2manager._waitforall([ssh])
        result = ssh.stdout.readlines()
        output = ssh.stderr.readlines()
        if result:
            print "The Nameserver cannot bind to socket 53. Try another instance."
            return

        cmd = ["ssh", "-t", ec2manager.username+'@'+i,
               "sudo python -c \"exec(\\\"import boto\\\")\""]

        ssh = subprocess.Popen(cmd, shell=False,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
        ec2manager._waitforall([ssh])
        result = ssh.stdout.readlines()
        output = ssh.stderr.readlines()
        if result:
            cmd = ["ssh", "-t", ec2manager.username+'@'+i,
                   "sudo pip install -U boto"]

            ssh = subprocess.Popen(cmd)
            ec2manager._waitforall([ssh])
        print "Starting nameserver on %s" % str(i)
        cmd = ["ssh", ec2manager.username+'@'+i, 'concoord nameserver ' + ' '.join(sys.argv[1:])]
        p = ec2manager._issuecommand(cmd)

def start_ec2manager():
    ec2manager = EC2Manager(*read_config_file())
    ec2manager.startservice()
    signal.signal(signal.SIGINT, ec2manager.terminate_handler)
    signal.signal(signal.SIGTERM, ec2manager.terminate_handler)
    signal.pause()

def main():
    touch_config_file()
    if len(sys.argv) < 2:
        print HELPSTR
        sys.exit()

    eventtype = sys.argv[1].upper()
    sys.argv.pop(1)

    touch_config_file()
    read_config_file()

    if eventtype == 'CONFIG':
        print_config_file()
    elif eventtype == 'SSHKEY':
        print "Adding SSHKEY to CONFIG"
        add_sshkeyfile_to_config(sys.argv[1])
        print_config_file()
    elif eventtype == 'USERNAME':
        print "Adding USERNAME to CONFIG"
        add_username_to_config(sys.argv[1])
        print_config_file()
    elif eventtype == 'NODE':
        print "Adding NODE to CONFIG"
        add_node_to_config(sys.argv[1])
        print_config_file()
    elif eventtype == 'EC2':
        print "Starting EC2 Manager"
        start_ec2manager()
    elif eventtype == node_names[NODE_REPLICA]:
        start_node(NODE_REPLICA)
    elif eventtype == node_names[NODE_NAMESERVER]:
        start_node(NODE_NAMESERVER)
    else:
        print HELPSTR

if __name__=='__main__':
    main()
