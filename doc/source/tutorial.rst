Getting Started
---------------
To use ConCoord and distribute your Python objects first you need to
create the local Python object. Once the object is created, ConCoord
will automatically create a proxy object and you will be able to do
remote method invocations when your object is distributed. For these
remote method invocations, a round of Paxos Consensus Protocol is run
by ConCoord to provide consistency between different copies of the
object.

Concoordifying Python Objects
-----------------------------
To walk you through the ConCoord approach, we will use the example
Counter coordination object we provided. In the source distribution
you can locate the Counter object under
``concoord/object/counter.py``. Once you install ConCoord, you can create
coordination objects and save them anywhere in your filesystem. To
demonstrate this, we will save ``counter.py`` under ``/foo/counter.py``.

.. sourcecode:: python

  class Counter:
    def __init__(self, value=0):
      self.value = value

    def decrement(self):
      self.value -= 1

    def increment(self):
      self.value += 1

    def getvalue(self):
      return self.value

    def __str__(self):
      return "The counter value is %d" % self.value

Once you have created the object, update your ``PYTHONPATH`` accordingly,
so that the objects can be found and imported:

.. sourcecode:: console

  $ export PYTHONPATH=$PYTHONPATH:/foo/

Clients will use a proxy object to do method calls on the ConCoord object.
To create a proxy for the ConCoord object, run the following command:

.. sourcecode:: console

  $ concoord object -o counter.Counter

``Usage: concoord object [-h] [-o OBJECTNAME] [-t SECURITYTOKEN] [-p PROXYTYPE] [-s] [-v]``

where,
  ``-h, --help``					show this help message and exit

  ``-o OBJECTNAME, --objectname OBJECTNAME``		client object dotted name module.Class

  ``-t SECURITYTOKEN, --token SECURITYTOKEN``		security token

  ``-p PROXYTYPE, --proxytype PROXYTYPE``		0:BASIC, 1:BLOCKING, 2:CLIENT-SIDE BATCHING, 3:SERVER-SIDE BATCHING

  ``-s, --safe``            				safety checking on/off

  ``-v, --verbose``         				verbose mode on/off

This script will create a proxy file under the directory that the
object resides (i.e. ``/foo/``):

``/foo/counterproxy.py`` := the proxy that can be used by the client

IMPORTANT NOTE: ConCoord objects treat ``__init__`` functions specially in
two ways:

1) When Replicas go live, the object is instantiated calling the ``__init__`` without any arguments. Therefore, while implementing coordination objects, the ``__init__`` method should be implemented to be able to run without explicit arguments. You can use defaults to implement an ``__init__`` method that accepts arguments.

2) In the proxy created, the ``__init__`` function is used to initialize the Client-Replica connection. This way, multiple clients can connect to a ConCoord instance without reinitializing the object. During proxy generation, the original ``__init__`` function is renamed as ``__concoordinit__``, to reinitialize the object the user can call ``__concoordinit__`` at any point.


Starting Nodes
--------------

To distribute your object you should start at least one replica and one acceptor.

Starting Replica Nodes
~~~~~~~~~~~~~~~~~~~~~~

To start the replica node, use the following command:

.. sourcecode:: console

  $ concoord replica -o counter.Counter

To start replica nodes to join an active ConCoord instance, use the
following command to connect to a bootstrap replica with ``ipaddr:port``:

.. sourcecode:: console

  $ concoord replica -o counter.Counter -b ipaddr:port

Starting Acceptor Nodes
~~~~~~~~~~~~~~~~~~~~~~~
To start an acceptor node that connects to the bootrstrap replica at
``ipaddr:port``, use the following command:

.. sourcecode:: console

  $ concoord acceptor -b ipaddr:port

Note that you can specify the port and the address of any node with
options ``-p`` and ``-a`` respectively. The nodes can also be run in the debug
and interactive modes or with a logger with the commands shown below:

``Usage: concoord [-h] [-a ADDR] [-p PORT] [-b BOOTSTRAP] [-o OBJECTNAME] [-l LOGGER] [-d] [-i]``
where,
  ``-h, --help``				 show this help message and exit

  ``-a ADDR, --addr ADDR``  	      	   	 addr for the node

  ``-p PORT, --port PORT``			 port for the node

  ``-b BOOTSTRAP, --boot BOOTSTRAP``		 address:port tuple for the bootstrap peer

  ``-o OBJECTNAME, --objectname OBJECTNAME``	 client object dotted name

  ``-l LOGGER, --logger LOGGER``		 logger address

  ``-d, --debug``           			 debug on/off

  ``-i, --interactive``     			 interactive shell on/off

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
answer queries for ``counterdomain`` as follows:

.. sourcecode:: console

  $ sudo concoord nameserver -n counterdomain -o counter.Counter -b ipaddr:port -t 1

When you set up the nameserver delegations, you can send queries for
``counterdomain`` and see the most current set of nodes as follows:

.. sourcecode:: console

  $ dig -t a counterdomain                   # returns set of Replicas

  $ dig -t srv _concoord._tcp.counterdomain  # returns set of Replicas with ports

  $ dig -t txt counterdomain                 # returns set of all nodes

  $ dig -t ns counterdomain                  # returns set of nameservers

If you want to run the nameserver without proper delegation setup, you
can query the nameserver bound to ``nsipaddr`` specifically as follows:

.. sourcecode:: console

  $ dig -t a counterdomain @nsipaddr         # returns set of Replicas

Slave Nameserver
++++++++++++++++

Before starting a slave nameserver node manually, you should have a
master nameserver set up and running. The master nameserver should be
set up to answer the queries for its slave nameservers. We provide
OpenReplica Nameserver as a ready to deploy master nameserver and a
Nameserver Coordination Object in our example objects set to keep
track of slave nameserver information. Using this coordination object,
the master nameserver can keep track of its slave nameserver
delegations and the slave nameserver can update the master every time
the view of its system changes.

Once your master nameserver is set up, you can start the slave
nameserver as follows:

.. sourcecode:: console

  $ concoord nameserver -n counterdomain -o counter.Counter -b ipaddr:port -t 2 -m masterdomain

When the slave nameserver starts running, you can send queries for
``counterdomain`` and see the most current set of nodes as follows:

.. sourcecode:: console

  $ dig -t a counterdomain                   # returns set of Replicas

  $ dig -t srv _concoord._tcp.counterdomain  # returns set of Replicas with ports

  $ dig -t txt counterdomain                 # returns set of all nodes

  $ dig -t ns counterdomain                  # returns set of nameservers

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

  $ concoord nameserver -n counterdomain -o counter.Counter -b ipaddr:port -t 3 -o configfilepath


Connecting to ConCoord Objects
------------------------------

Once you have a ConCoord instance running with your object, it is easy
to access your object.

Now we will use the proxy object we generated. You can import and use
this proxy object in your code. Depending on how you set your
nameserver node up, you can access your object with the ``ipaddr:port``
pair or the ``domainname``.

.. sourcecode:: pycon

  >>> from counterproxy import Counter
  >>> c = Counter(domainname)
  >>> c.increment()
  >>> c.increment()
  >>> c.getvalue()
  2

At any point to reinitialize an object after it is deployed on
replicas, you should call ``__concoordinit__`` function:

.. sourcecode:: pycon

  >>> from counterproxy import Counter
  >>> c = Counter(domainname)
  >>> c.increment()
  >>> c.__concoordinit__()
  >>> c.increment()
  >>> c.getvalue()
  1
