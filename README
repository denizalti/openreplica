.. -*-restructuredtext-*-

========
ConCoord
========

Overview
========

ConCoord is a novel coordination service that provides replication and
synchronization support for large-scale distributed systems. ConCoord
employs an object-oriented approach, in which the system creates
and maintains live replicas for Python objects written by the user.
ConCoord converts these Python objects into Paxos Replicated State
Machines (RSM) and enables clients to do method invocations on them
transparently as if they are local objects. ConCoord uses these
replicated objects to implement coordination and synchronization
constructs in large-scale distributed systems, in effect establishing
a transparent way of providing a coordination service.

:Authors:
    - Deniz Altinbuken (deniz@systems.cs.cornell.edu)
    - Emin Gun Sirer (egs@systems.cs.cornell.edu)
:Version: 1.1.0
:Date: 2014-04-03

Requirements
============

The minimum requirements for ConCoord are::

  - python 2.7.2 or later
  - dnspython-1.9.4
  - msgpack-python

Installation
============

ConCoord can be installed from source with::

  $ python setup.py install

ConCoord is also available for install through PyPI::

  $ pip install concoord

Tutorial
========

Getting Started
---------------

To use ConCoord you need a Python object that can be used for the
coordination of your distributed system. In the ConCoord distribution,
we offer ready-to-use objects that cover the most common coordination
needs. So first, let's start a ConCoord instance with an object in
the distribution, namely Counter under concoord/object/counter.py.

Starting Nodes
--------------

To distribute the local object you should start at least one replica.

Starting Replicas
~~~~~~~~~~~~~~~~~

To start a bootstrap replica node that doesn't need to be connected to
another replica, use the following command::

  $ concoord replica -o concoord.object.counter.Counter -a 127.0.0.1 -p 14000

To start replica nodes to join an active ConCoord instance, use the
following command to connect to another replica::

  $ concoord replica -o concoord.object.counter.Counter -b 127.0.0.1:14000 -a 127.0.0.1 -p 14001

You can specify the port and the address of any replica with options -p and -a
respectively. The replicas can also be run in the debug mode or with a logger
with the commands shown below::

  Usage: concoord replica [-h] [-a ADDR] [-p PORT] [-b BOOTSTRAP]
 	   	          [-o OBJECTNAME] [-l LOGGER] [-n DOMAIN]
			  [-r] [-w] [-d]

where,
  -h, --help            show this help message and exit
  -a ADDR, --addr ADDR  address for the node
  -p PORT, --port PORT  port for the node
  -b BOOTSTRAP, --boot BOOTSTRAP
                        address:port tuple for the bootstrap peer
  -o OBJECTNAME, --objectname OBJECTNAME
                        client object dotted name
  -l LOGGER, --logger LOGGER
                        logger address
  -n DOMAIN, --domainname DOMAIN
                        domain name that the name server will accept queries for
  -r, --route53         use Route53
  -w, --writetodisk     writing to disk on/off
  -d, --debug           debug on/off

Starting Replicas as Name Servers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can dynamically locate nodes in a given ConCoord instance using
DNS queries if the instance includes replicas that can act as name
servers. There are two ways you can run a ConCoord Replica as a name
server.

* **Master Name Server:** Keeps track of the view and responds to DNS
  queries itself. Requires su privileges to bind to Port 53.

* **Route53 Name Server:** Keeps track of the view and updates an Amazon
  Route53 account. Amazon Route53 answers to DNS queries on behalf of
  the slave name server. Requires a ready-to-use Amazon Route53
  account.

Master Name Server
+++++++++++++++++++

To use a replica node as a master name server first you have to setup
the name server delegations (you can do this by updating the domain
name server information of any domain name you own from the domain
registrar you use (godaddy, namecheap etc.)). Once all the delegations
are setup for the ip address the replica uses, you can start a replica
node as a name server for counterdomain.com as follows::

  $ sudo concoord replica -o concoord.object.counter.Counter -a 127.0.0.1 -n counterdomain.com

And to start the replica to join an already running ConCoord instance,
provide the bootstrap::

  $ sudo concoord replica -o concoord.object.counter.Counter -a 127.0.0.1 -b 127.0.0.1:14000 -n counterdomain.com

When the replica starts running, you can send queries for
counterdomain.com and see the most current set of nodes as follows::

  $ dig -t a counterdomain.com                   # returns set of Replicas

  $ dig -t srv _concoord._tcp.counterdomain.com  # returns set of Replicas with ports

  $ dig -t txt counterdomain.com                 # returns set of all nodes

  $ dig -t ns counterdomain.com                  # returns set of name servers

If you want to run the name server without proper delegation setup, you
can query the name server bound to 127.0.0.1 specifically as follows::

  $ dig -t txt counterdomain.com @127.0.0.1      # returns set of all nodes

Note that this would only work for a, srv and txt queries, since ns
queries require absolute dns names or origins, not an ip address.

Amazon Route53 Name Server
++++++++++++++++++++++++++

First make sure that boto is installed on the machine you want to run
the Route53 name server. You can easily install boto as follows::

  $ pip install boto

Before starting a name server connected to Amazon Route 53, you should
have a Route53 account set up and ready to receive requests. This is
done through the AWS Console (http://console.aws.amazon.com/route53), by
creating a new Hosted Zone to host your domain name.

After your Route53 account is set up, the name server can update
Route53 records every time the view of the system changes.

To use the Name Server to update Amazon Route53, you should provide
your AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY. You can retrieve
these from the AWS Console (http://console.aws.amazon.com/iam), by
looking under the security credentials of the username that you used
while creating the Hosted Zone for your domain name. Once you have the
information, you can set up ConCoord configuration easily as follows::

  $ concoord route53id [AWS_ACCESS_KEY_ID]
  $ concoord route53key [AWS_SECRET_ACCESS_KEY]

Once you make sure that your Route53 account is set up and the
configuration file includes your AWS credentials, you can start the
replica with a name server as follows::

  $ concoord replica -o concoord.object.counter.Counter -n counterdomain.com -r

When the replica starts running, you can send queries for
counterdomain.com and see the most current set of nodes as follows::

  $ dig -t a counterdomain.com                   # returns set of Replicas

  $ dig -t srv _concoord._tcp.counterdomain.com  # returns set of Replicas with ports

  $ dig -t txt counterdomain.com                 # returns set of all nodes

  $ dig -t ns counterdomain.com                  # returns set of name servers

Connecting to ConCoord Objects
------------------------------

Once you have a ConCoord instance running with your object, it is easy
to access your object.

The proxy for the Counter object is also included in the distribution.
You can import and use this proxy object in your code. Depending on
how you set your name server up, you can access your object with the
ipaddr:port pair or the domainname. In the example below, the
ipaddr:port of both replica nodes are used. As a result, the client
will be able to do method invocations on the object as long as one of
the replicas is alive::

  >>> from concoord.proxy.counter import Counter
  >>> c = Counter("127.0.0.1:14000, 127.0.0.1:14001")
  >>> c.increment()
  >>> c.increment()
  >>> c.getvalue()
  2

At any point to reinitialize an object after it is deployed on
replicas, you should call __concoordinit__ function::

  >>> from concoord.proxy.counter import Counter
  >>> c = Counter("127.0.0.1:14000, 127.0.0.1:14001")
  >>> c.increment()
  >>> c.__concoordinit__()
  >>> c.increment()
  >>> c.getvalue()
  1

OpenReplica
===========

OpenReplica provides easily launch for concoord on remote machines,
and it is especially built to launch concoord instances on Amazon EC2
servers easily. In this section we cover how you can setup a set of
machines and launch concoord remotely using OpenReplica.

How to start using Amazon EC2
-----------------------------

You can easily launch your EC2 instances using the web interface
provided by Amazon AWS. In this example we launch an instance running
64-bit Amazon Linux. Before you launch your instance, you will have to
create a keypair to login to your instances, make sure to keep your
private key safe. The best way is to move your key-pair to the .ssh
directory once you download the [my-key-pair].pem file::

  $ mv [my-key-pair].pem ~/.ssh/
  $ ssh-add ~/.ssh/[my-key-pair].pem

Once you did these, now is the time to connect to your instance::

  $ ssh -i [my-key-pair].pem ec2-user@[public_dns_name]

After this point on, you should be able to connect to your instance
without explicitly passing the key as a parameter, as follows::

  $ ssh ec2-user@[public_dns_name]

To enable execution of remote sudo commands SSH into your instance and
run::

  $ sudo visudo

In the file that opens find the line 'Defaults requiretty' and add
line 'Defaults:ec2-user !requiretty' below it. Save the file and
exit. The file opens with the vi editor. If you are not familiar with
vi commands, to insert new text press i to go into insert mode and add
the new line. After you are done, press ESC and ZZ to save and exit.

At this point, your EC2 instance should be easily accessible.

Using OpenReplica
-----------------

Using OpenReplica developers can configure and remotely launch
ConCoord instances on remote machines easily. Firstly, OpenReplica
keeps the configuration information of machines that will be running
the ConCoord instance. Secondly, using ConCoord developers can easily
start replica and nameserver nodes on the machines that are added to
the configuration.  And lastly, using OpenReplica developers can
easily manage EC2 instances.

Like ConCoord, OpenReplica can be used as a commandline script. It
supports the following commands:

openreplica config - prints config file
openreplica addsshkey [sshkeyfilename] - adds sshkey filename to config
openreplica addusername [ssh username] - adds ssh username to config
openreplica addnode [publicdns] - adds public dns for node to config
openreplica setup [publicdns] - downloads and sets up concoord on the given node
openreplica replica [concoord arguments] - starts a replica node on EC2
openreplica nameserver [concoord arguments] - starts a nameserver node on EC2

Setting up the Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To use OpenReplica, you should first register the nodes you want to
use. To register nodes, you will need the filename of the sshkey you
use to ssh into these nodes, as well as the username.

To add the sshkey::

  $ openreplica addsshkey [my-key-pair].pem

To add the username::

  $ openreplica addusername ec2-user

To add a node::

  $ openreplica addnode [public_dns_name]

When adding nodes to OpenReplica, it automatically checks the nodes
for eligibility to run ConCoord and warns the user if an update or
change is required. Similarly, if ConCoord cannot connect to the node,
it lets the user know::

  $ openreplica addsshkey concoord.pem
  Adding SSHKEY to CONFIG: concoord.pem
  $ openreplica addusername ec2-user
  Adding USERNAME to CONFIG: ec2-user
  $ openreplica addnode ec2-54-186-26-155.us-west-2.compute.amazonaws.com
  Adding NODE to CONFIG: ec2-54-186-26-155.us-west-2.compute.amazonaws.com
  Cannot connect to node, check if it is up and running.

Starting ConCoord Instances
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once OpenReplica is set up, nodes can be started as if they are being
started on the local machine.

Starting Replica Nodes
++++++++++++++++++++++

To start a bootstrap replica node that doesn't need to be connected to
another replica::

  $ openreplica replica -o concoord.object.counter.Counter -a 127.0.0.1 -p 14000

To start replica nodes to join an active ConCoord instance::

  $ openreplica replica -o concoord.object.counter.Counter -b 127.0.0.1:14000 -a 127.0.0.1 -p 14001

The nodes can also be run in the debug mode or with a logger with the
commands shown below::

   Usage: openreplica replica [-h] [-a ADDR] [-p PORT] [-b BOOTSTRAP]
	                      [-o OBJECTNAME] [-l LOGGER] [-n DOMAIN]
			      [-r] [-w] [-d]

where,
  -h, --help            show this help message and exit
  -a ADDR, --addr ADDR  address for the node
  -p PORT, --port PORT  port for the node
  -b BOOTSTRAP, --boot BOOTSTRAP
                        address:port tuple for the bootstrap peer
  -o OBJECTNAME, --objectname OBJECTNAME
                        client object dotted name
  -l LOGGER, --logger LOGGER
                        logger address
  -n DOMAIN, --domainname DOMAIN
                        domain name that the name server will accept queries for
  -r, --route53         use Route53
  -w, --writetodisk     writing to disk on/off
  -d, --debug           debug on/off

Starting Replicas as Name Servers
+++++++++++++++++++++++++++++++++

You can dynamically locate nodes in a given ConCoord instance using
DNS queries if the instance includes replicas that can act as name
servers. There are two ways you can run a ConCoord Replica as a name
server.

* **Master Name Server:** Keeps track of the view and responds to DNS
  queries itself. Requires su privileges to bind to port 53.

* **Route53 Name Server:** Keeps track of the view and updates an Amazon
  Route53 account. Amazon Route53 answers to DNS queries on behalf of
  the slave name server. Requires a ready-to-use Amazon Route53
  account.

Master Name Server
++++++++++++++++++

To use a replica node as a master name server first you have to setup
the name server delegations (you can do this by updating the domain
name server information of any domain name you own from the domain
registrar you use (godaddy, namecheap etc.)). Once all the delegations
are setup for the ip address the replica uses, you can start a replica
node as a name server for counterdomain.com as follows::

  $ openreplica replica -o concoord.object.counter.Counter -a 127.0.0.1 -n counterdomain.com

And to start the replica to join an already running ConCoord instance,
provide the bootstrap::

  $ openreplica replica -o concoord.object.counter.Counter -a 127.0.0.1 -b 127.0.0.1:14000 -n counterdomain.com

When the replica starts running, you can send queries for
counterdomain.com and see the most current set of nodes as
follows::

  $ dig -t a counterdomain.com                   # returns set of Replicas

  $ dig -t srv _concoord._tcp.counterdomain.com  # returns set of Replicas with ports

  $ dig -t txt counterdomain.com                 # returns set of all nodes

  $ dig -t ns counterdomain.com                  # returns set of name servers

Amazon Route53 Name Server
++++++++++++++++++++++++++

First make sure that boto is installed on the machine you want to run
the Route53 name server. OpenReplica tries to do this automatically
when a replica is run as a Route53 name server, but if it fails to do
so, you can easily install boto on the machine you want as follows::

  $ pip install boto

Before starting a name server connected to Amazon Route53, you should
have a Route53 account set up and ready to receive requests. This is
done through the AWS Console (http://console.aws.amazon.com/route53), by
creating a new Hosted Zone to host your domain name.

After your Route53 account is set up, the name server can update
Route53 records every time the view of the system changes.

To use the Name Server to update Amazon Route53, you should provide
your AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY. You can retrieve
these from the AWS Console (http://console.aws.amazon.com/iam/), by
looking under the security credentials of the username that you used
while creating the Hosted Zone for your domain name. Once you have the
information, you can set up Route53 configuration easily as follows::

  $ openreplica route53 [public_dns AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY]

Once you make sure that your Route53 account is set up and the
configuration file includes your AWS credentials, you can start the
replica with a name server as follows::

  $ openreplica replica -o concoord.object.counter.Counter -n counterdomain.com -r

When the replica starts running, you can send queries for
counterdomain.com and see the most current set of nodes as follows::

  $ dig -t a counterdomain.com                   # returns set of Replicas

  $ dig -t srv _concoord._tcp.counterdomain.com  # returns set of Replicas with ports

  $ dig -t txt counterdomain.com                 # returns set of all nodes

  $ dig -t ns counterdomain.com                  # returns set of name servers

ADVANCED TUTORIAL
=================

ConCoordifying Python Objects
-----------------------------
For cases when the objects included in the ConCoord distribution do
not meet your coordination needs, ConCoord lets you convert your
local Python objects into distributable objects very easily.

To walk through the ConCoord approach, you will use a different
Counter object that increments and decrements by ten, namely
tencounter.py. Once you install ConCoord, you can create coordination
objects and save them anywhere in your filesystem. After you create
tencounter.py, you can save tencounter.py under /foo/tencounter.py::

  class TenCounter:
    def __init__(self, value=0):
     self.value = value

    def decrement(self):
      self.value -= 10

    def increment(self):
      self.value += 10

    def getvalue(self):
      return self.value

    def __str__(self):
      return "The counter value is %d" % self.value

Once you have created the object, update your PYTHONPATH accordingly,
so that the objects can be found and imported::

  $ export PYTHONPATH=$PYTHONPATH:/foo/

Clients will use a proxy object to do method calls on the object.
To create the proxy object automatically, you can use the following
command::

  $ concoord object -o tencounter.TenCounter


  Usage: concoord object [-h] [-o OBJECTNAME] [-t SECURITYTOKEN] [-p PROXYTYPE]
                         [-s] [-v]

where,
  -h, --help					show this help message and exit
  -o OBJECTNAME, --objectname OBJECTNAME	client object dotted name module.Class
  -t SECURITYTOKEN, --token SECURITYTOKEN	security token
  -p PROXYTYPE, --proxytype PROXYTYPE		0:BASIC, 1:BLOCKING,
     			    			2:CLIENT-SIDE BATCHING, 3:SERVER-SIDE BATCHING
  -s, --safe            			safety checking on/off
  -v, --verbose         			verbose mode on/off

This script will create a proxy file under the directory that the
object resides (i.e. /foo/)::

/foo/tencounterproxy.py := the proxy that can be used by the client

IMPORTANT NOTE: ConCoord objects treat __init__ functions specially in
two ways:

1) When Replicas go live, the object is instantiated calling the
__init__ without any arguments. Therefore, while implementing
coordination objects, the __init__ method should be implemented to be
able to run without explicit arguments. You can use defaults to
implement an __init__ method that accepts arguments.

2) In the proxy created, the __init__ function is used to initialize
the Client-Replica connection. This way, multiple clients can connect
to a ConCoord instance without reinitializing the object. During proxy
generation, the original __init__ function is renamed as
__concoordinit__, to reinitialize the object the user can call
__concoordinit__ at any point.

After this point on, you can use TenCounter just like we use Counter before.

Creating Source Bundles
-----------------------

You can create bundles to use at the server and client sides using the
Makefile provided. Remember to add the objects you have created in
these bundles.

Creating A Server Bundle
~~~~~~~~~~~~~~~~~~~~~~~~

To create a bundle that can run replicas::

  $ make server

Creating A Client Bundle
~~~~~~~~~~~~~~~~~~~~~~~~

To create a bundle that can run a client and connect to an existing
ConCoord instance::

  $ make client

Logging
-------

We have two kinds of loggers for ConCoord::
* Console Logger
* Network Logger

Both of these loggers are included under utils.py. To start the
NetworkLogger, use the logdaemon.py on the host you want to keep the
Logger.

Synchronization & Threading
---------------------------

ConCoord provides a distributed and fault-tolerant threading
library. The library includes:

*  Lock
*  RLock
*  Semaphore
*  BoundedSemaphore
*  Barrier
*  Condition

The implementations of distributed synchronization objects follow the
implementations in the Python threading library. We will walk through
an example below using the Semaphore object under
concoord/object/semaphore.py

In the blocking object implementation, the method invocations that use
an object from the threading library requires an extra argument
_concoord_command. This argument is used by the calling Replica node
to relate any blocking/unblocking method invocation to a specific
client. This way, even if the client disconnects and reconnects, the
ConCoord instance will remain in a safe state::

  from concoord.threadingobject.dsemaphore import DSemaphore

  class Semaphore:
    def __init__(self, count=1):
      self.semaphore = DSemaphore(count)

    def __repr__(self):
      return repr(self.semaphore)

    def acquire(self, _concoord_command):
      try:
	return self.semaphore.acquire(_concoord_command)
      except Exception as e:
        raise e

    def release(self, _concoord_command):
      try:
        return self.semaphore.release(_concoord_command)
      except Exception as e:
        raise e

    def __str__(self):
      return str(self.semaphore)

To create the proxy for this blocking object we will use the following command::

  $ concoord object -o concoord.object.semaphore.Semaphore -p 1

This command creates the proxy that supports blocking operations. Now
you can use blocking objects just like basic ConCoord objects. First,
we start the replica nodes the same way we did before as follows::

  $ concoord replica -o concoord.object.semaphore.Semaphore -a 127.0.0.1 -p 14000

To test the functionality, you can use multiple clients or print out
the Semaphore object as follows::

  >>> from semaphoreproxy import Semaphore
  >>> s = Semaphore("127.0.0.1:14000")
  >>> s.acquire()
  True
  >>> i = 10
  >>> i += 5
  >>> s
  <DSemaphore count=0>
  >>> s.release()
  >>> s
  <DSemaphore count=1>
  >>>

HOMEPAGE
========

Visit http://openreplica.org to get more information on ConCoord.

CONTACT
=======

If you believe you have found a bug or have a problem you need
assistance with, you can get in touch with us by emailing
concoord@systems.cs.cornell.edu