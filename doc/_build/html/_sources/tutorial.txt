Getting Started
---------------

To use ConCoord you need a Python object that can be used for the
coordination of your distributed system. In the ConCoord distribution,
we offer ready-to-use objects that cover the most common coordination
needs. So first, let's start a ConCoord instance with an object in
the distribution, namely Counter under concoord/object/counter.py.

Starting Nodes
--------------

To distribute your object you should start at least one replica and one acceptor.

Starting Replica Nodes
~~~~~~~~~~~~~~~~~~~~~~

To start a bootstrap replica node that doesn't need to be connected to another replica, use the following command:

.. sourcecode:: console

  $ concoord replica -o concoord.object.counter.Counter -a 127.0.0.1 -p 14000

To start replica nodes to join an active ConCoord instance, use the following command to connect to another replica:

.. sourcecode:: console

  $ concoord replica -o concoord.object.counter.Counter -b 127.0.0.1:14000 -a 127.0.0.1 -p 14001

Starting Acceptor Nodes
~~~~~~~~~~~~~~~~~~~~~~~

To start an acceptor node that connects to the bootstrap replica at
``127.0.0.1:14000``, use the following command:

.. sourcecode:: console

  $ concoord acceptor -b 127.0.0.1:14000

To run ConCoord in durable mode, where acceptors write to disk, you
can set the ``-w`` option:

.. sourcecode:: console

  $ concoord acceptor -b 127.0.0.1:14000 -w

Note that you can specify the port and the address of any node with options
``-p`` and ``-a`` respectively. The nodes can also be run in the debug
mode or with a logger with the commands shown below:

``Usage: concoord [-h] [-a ADDR] [-p PORT] [-b BOOTSTRAP] [-o OBJECTNAME] [-l LOGGER] [-w] [-d]``
where,
  ``-h, --help``				 show this help message and exit

  ``-a ADDR, --addr ADDR``  	      	   	 addr for the node

  ``-p PORT, --port PORT``			 port for the node

  ``-b BOOTSTRAP, --boot BOOTSTRAP``		 address:port tuple for the bootstrap peer

  ``-o OBJECTNAME, --objectname OBJECTNAME``	 client object dotted name

  ``-l LOGGER, --logger LOGGER``		 logger address

  ``-w, --writetodisk``           		 writing to disk on/off

  ``-d, --debug``           			 debug on/off

Starting Nameserver Nodes
~~~~~~~~~~~~~~~~~~~~~~~~~

You can dynamically locate nodes in a given ConCoord instance using
DNS queries if the instance includes nameserver nodes. There are three
ways you can run a ConCoord Nameserver.

* **Standalone Nameserver** Keeps track of the view and responds to DNS
  queries itself. Requires su privileges to bind to Port 53.

* **Slave Nameserver** Keeps track of the view and updates a master
  nameserver that answers to DNS queries on behalf of the slave
  nameserver. Requires an active master nameserver.

* **Route53 Nameserver** Keeps track of the view and updates an Amazon
  Route53 account. Amazon Route53 answers to DNS queries on behalf of
  the slave nameserver. Requires a ready-to-use Amazon Route53
  account.

Standalone Nameserver
+++++++++++++++++++++

Before starting a standalone nameserver node manually, first make sure
that you have at least one replica and one acceptor running. Once your
replica and acceptor nodes are set up, you can start the nameserver to
answer queries for ``counterdomain.com`` as follows:

.. sourcecode:: console

  $ sudo concoord nameserver -n counterdomain.com -o concoord.object.counter.Counter -b 127.0.0.1:14000 -t 1

When you set up the nameserver delegations, you can send queries for
``counterdomain.com`` and see the most current set of nodes as follows:

.. sourcecode:: console

  $ dig -t a counterdomain.com                   # returns set of Replicas

  $ dig -t srv _concoord._tcp.counterdomain.com  # returns set of Replicas with ports

  $ dig -t txt counterdomain.com                 # returns set of all nodes

  $ dig -t ns counterdomain.com                  # returns set of nameservers

If you want to run the nameserver without proper delegation setup, you
can query the nameserver bound to ``127.0.0.1`` specifically as follows:

.. sourcecode:: console

  $ dig -t txt counterdomain.com @127.0.0.1      # returns set of all nodes

Slave Nameserver
++++++++++++++++

Before starting a slave nameserver node manually, you should have a
master nameserver set up and running. The master nameserver should be
set up to answer the queries for its slave nameservers. We provide
OpenReplica Nameserver (``concoord/openreplica/openreplicanameserver.py``)
as a ready to deploy master nameserver and a Nameserver Coordination Object
(``concoord/object/nameservercoord.py``) in our example objects to keep
track of slave nameserver information. Using this coordination object,
the master nameserver can keep track of its slave nameserver
delegations and the slave nameserver can update the master every time
the view of its system changes.

Once your master nameserver is set up, you can start the slave
nameserver as follows:

.. sourcecode:: console

  $ concoord nameserver -n counterdomain.com -o concoord.object.counter.Counter -b 127.0.0.1:14000 -t 2 -m masterdomain.com

When the slave nameserver starts running, you can send queries for
``counterdomain.com`` and see the most current set of nodes as follows:

.. sourcecode:: console

  $ dig -t a counterdomain.com                   # returns set of Replicas

  $ dig -t srv _concoord._tcp.counterdomain.com  # returns set of Replicas with ports

  $ dig -t txt counterdomain.com                 # returns set of all nodes

  $ dig -t ns counterdomain.com                  # returns set of nameservers

Amazon Route 53 Nameserver
++++++++++++++++++++++++++

Before starting a nameserver connected to Amazon Route 53, you should
have a Route 53 account set up and ready to receive requests. After
your Route 53 account is ready, the nameserver can update the master
every time the view of its system changes automatically.

To use Amazon Route 53 you can pass your credentials into the methods
that create connections or edit them in the configuration file.

     AWS_ACCESS_KEY_ID - Your AWS Access Key ID
     AWS_SECRET_ACCESS_KEY - Your AWS Secret Access Key

Once you make sure that your Route53 account is set up and your
credentials are updated, you can start the nameserver as follows:

.. sourcecode:: console

  $ concoord nameserver -n counterdomain.com -o concoord.object.counter.Counter -b 127.0.0.1:14000 -t 3 -o configfilepath

Connecting to ConCoord Objects
------------------------------

Once you have a ConCoord instance running with your object, it is easy
to access your object.

The proxy for the Counter object is also included in the distribution.
You can import and use this proxy object in your code. Depending on
how you set your nameserver node up, you can access your object with
the ``ipaddr:port`` pair or the domainname. In the example below, the
``ipaddr:port`` of both replica nodes are used. As a result, the client
will be able to do method invocations on the object as long as one of
the replicas is alive:

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