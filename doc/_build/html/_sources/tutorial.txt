Getting Started
---------------

To use ConCoord you need a Python object that can be used for the
coordination of your distributed system. In the ConCoord distribution,
we offer ready-to-use objects that cover the most common coordination
needs. So first, let's start a ConCoord instance with an object in
the distribution, namely Counter under ``concoord/object/counter.py``.

Starting Nodes
--------------

To distribute your object you should start at least one replica.

Starting Replica Nodes
~~~~~~~~~~~~~~~~~~~~~~

To start a bootstrap replica node that doesn't need to be connected to
another replica:

.. sourcecode:: console

  $ concoord replica -o concoord.object.counter.Counter -a 127.0.0.1 -p 14000

To start replica nodes to join an active ConCoord instance, use the
following command to connect to another replica:

.. sourcecode:: console

  $ concoord replica -o concoord.object.counter.Counter -b 127.0.0.1:14000 -a 127.0.0.1 -p 14001

Note that you can specify the port and the address of any node with
options ``-p`` and ``-a`` respectively. The nodes can also be run in
the debug mode or with a logger with the commands shown below:

``Usage: concoord replica [-h] [-a ADDR] [-p PORT] [-b BOOTSTRAP] [-o OBJECTNAME] [-l LOGGER] [-n DOMAIN] [-r] [-w] [-d]``

where,
  ``-h, --help``				 show this help message and exit

  ``-a ADDR, --addr ADDR``  	      	   	 address for the node

  ``-p PORT, --port PORT``			 port for the node

  ``-b BOOTSTRAP, --boot BOOTSTRAP``		 address:port tuple for the bootstrap peer

  ``-o OBJECTNAME, --objectname OBJECTNAME``	 client object dotted name

  ``-l LOGGER, --logger LOGGER``		 logger address

  ``-n DOMAIN, --domainname DOMAIN``             domain name that the name server will accept queries for

  ``-r, --route53``                              use Route53

  ``-w, --writetodisk``           		 writing to disk on/off

  ``-d, --debug``           			 debug on/off

Starting Replicas as Name Servers
~~~~~~~~~~~~~~~~~~~~~~~~~

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
+++++++++++++++++++++

To use a replica node as a master name server first you have to setup
the name server delegations (you can do this by updating the domain
name server information of any domain name you own from the domain
registrar you use (godaddy, namecheap etc.)). Once all the delegations
are setup for the ip address the replica uses, you can start a replica
node as a name server for ``counterdomain.com`` as follows:

.. sourcecode:: console

  $ sudo concoord replica -o concoord.object.counter.Counter -a 127.0.0.1 -n counterdomain.com

And to start the replica to join an already running ConCoord instance,
provide the bootstrap:

.. sourcecode:: console

  $ sudo concoord replica -o concoord.object.counter.Counter -a 127.0.0.1 -b 127.0.0.1:14000 -n counterdomain.com

When the replica starts running, you can send queries for
``counterdomain.com`` and see the most current set of nodes as
follows:

.. sourcecode:: console

  $ dig -t a counterdomain.com                   # returns set of Replicas

  $ dig -t srv _concoord._tcp.counterdomain.com  # returns set of Replicas with ports

  $ dig -t txt counterdomain.com                 # returns set of all nodes

  $ dig -t ns counterdomain.com                  # returns set of name servers


If you want to run the name server without proper delegation setup, you
can query the name server bound to ``127.0.0.1`` specifically as follows:

.. sourcecode:: console

  $ dig -t txt counterdomain.com @127.0.0.1      # returns set of all nodes

Note that this would only work for a, srv and txt queries, since ns
queries require absolute dns names or origins, not an ip address.

Amazon Route53 Name Server
++++++++++++++++++++++++++

First make sure that boto is installed on the machine you want to run
the Route53 name server. You can easily install boto as follows::

  $ pip install boto

Before starting a name server connected to Amazon Route53, you should
have a Route53 account set up and ready to receive requests. This is
done through the AWS Console (http://console.aws.amazon.com/route53), by
creating a new Hosted Zone to host your domain name.

After your Route53 account is set up, the name server can update
Route53 records every time the view of the system changes.

To use the Name Server to update Amazon Route53, you should provide
your ``AWS_ACCESS_KEY_ID`` and ``AWS_SECRET_ACCESS_KEY``. You can retrieve
these from the AWS Console (http://console.aws.amazon.com/iam/), by
looking under the security credentials of the username that you used
while creating the Hosted Zone for your domain name. Once you have the
information, you can set up Route53 configuration easily as follows:

.. sourcecode:: console

  $ concoord route53id [AWS_ACCESS_KEY_ID]
  $ concoord route53key [AWS_SECRET_ACCESS_KEY]

Once you make sure that your Route53 account is set up and the
configuration file includes your AWS credentials, you can start the
replica with a name server as follows:

.. sourcecode:: console

  $ concoord replica -o concoord.object.counter.Counter -n counterdomain.com -r

When the replica starts running, you can send queries for
``counterdomain.com`` and see the most current set of nodes as follows:

.. sourcecode:: console

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
``ipaddr:port`` pair or the domainname. In the example below, the
``ipaddr:port`` of both replica nodes are used. As a result, the
client will be able to do method invocations on the object as long as
one of the replicas is alive:

.. sourcecode:: pycon

  >>> from concoord.proxy.counter import Counter
  >>> c = Counter("127.0.0.1:14000, 127.0.0.1:14001")
  >>> c.increment()
  >>> c.increment()
  >>> c.getvalue()
  2

At any point to reinitialize an object after it is deployed on
replicas, you should call ``__concoordinit__`` function:

.. sourcecode:: pycon

  >>> from concoord.proxy.counter import Counter
  >>> c = Counter("127.0.0.1:14000, 127.0.0.1:14001")
  >>> c.increment()
  >>> c.__concoordinit__()
  >>> c.increment()
  >>> c.getvalue()
  1