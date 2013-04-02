Tutorial
===================

Getting Started
------------------------
To use ConCoord, first you need to create the local python object to
represent the state you want to replicate. To walk you through the
ConCoord approach, we will use one of the example coordination objects
we have provided, namely Counter. In the source distribution you can
locate the Counter object under ``concoord/object/counter.py``. Once you
install ConCoord, you can create coordination objects and save them
anywhere in your filesystem. To demonstrate this, we will save
``counter.py`` under ``/foo/counter.py``.

.. sourcecode:: python
	class Counter():
	    def __init__(self):
            	self.value = 0

    	    def decrement(self):
                self.value -= 1

    	    def increment(self):
                self.value += 1

	    def getvalue(self):
                return self.value
    
	    def __str__(self):
            	return "The counter value is %d" % self.value

Concoordifying Python Objects
------------------------
To create concoord objects you can use:

.. sourcecode:: console

	$ concoord object -f /foo/counter.py -c Counter -s -v

``Usage: concoord object -f objectfilepath -c classname -s safe -v verbose``

where ``objectfilepath`` := path of the object you want to concoordify
      	  ``classname`` := name of the class that you'll use to access your object
	  ``safe`` := boolean flag to include safety checks for the object
	  ``verbose`` := boolean flag to turn on verbose outputs

This script will create the proxy under the directory that the object resides (i.e. ``/foo/``):

* ``/foo/counter.pyproxy`` := the proxy that can be used like the original object by the client

Remember to rename the file back to the original filename before you
import it on the client side. To avoid confusion, we will
name it ``counterproxy.py`` in this tutorial.

.. sourcecode:: console

	    $ mv /foo/counter.pyproxy /foo/counterproxy.py

Once you have created the objects, update your ``PYTHONPATH`` accordingly,
so that the objects can be found and imported:

.. sourcecode:: console

	    $ export PYTHONPATH=$PYTHONPATH:/foo/

Starting Nodes Manually
------------------------
To start the system you need to start at least one replica and one
acceptor. To support bootstrapping through DNS queries, you will also
need at least one nameserver node that has the necessary delegation
set up for the address it is responsible for. Once the nameserver node 
is set up, you can send dig queries to the nameserver and learn the 
node to bootstrap, the current set of nodes and the current set of
replicas.

* For bootstrapping concoord requires at least one replica node. If a
  nameserver node is up, bootstrap can be the domainname for the
  concoord instance as new nodes can retrieve the bootstrap node
  automatically through DNS queries. If the nameserver is not running,
  bootstrap is a list of ipaddr:port pairs.


* Note that for the system to be able to add new nodes and accept
  client requests, there has to be at least one replica and one
  acceptor node present initially.

Starting Replica Nodes
^^^^^^^^^^^^^^^^^^^^^^^^
To start the bootstrap replica node manually, use the following
command:

.. sourcecode:: console

	$ concoord replica -f counter.py -c Counter

Note that you can specify the port the replica binds to with option
``-p``, if not specified port defaults to the first available port,
randomly chosen between 14000 and 15000.


To start replica nodes to join an active concoord instance, use the
following command:

.. sourcecode:: console

	$ concoord replica -f counter.py -c Counter -b ipaddr:port

Starting Acceptor Nodes
^^^^^^^^^^^^^^^^^^^^^^^^
To start an acceptor node manually, use the following command:

.. sourcecode:: console

	$ concoord acceptor -b ipaddr:port
	
Starting Nameserver Nodes
^^^^^^^^^^^^^^^^^^^^^^^^
There are three ways you can run a ConCoord Nameserver.

* **Standalone Nameserver** Keeps track of the view and responds to DNS
  queries itself. Requires su privileges to bind to Port 53.
* **Slave Nameserver** Keeps track of the view and updates a master
  nameserver that answers to DNS queries on behalf of the slave
  nameserver. Requires an active master nameserver. 
* **Route53 Nameserver** Keeps track of the view and updates an Amazon
  Route53 account. Amazon Route53 answers to DNS queries on behalf of the slave
  nameserver. Requires a ready-to-use Amazon Route53 account.

Standalone Nameserver
^^^^^^^^^^^^^^^^^^^^^^^^
Before starting a standalone nameserver node manually, first make sure
that you have at least one replica and one acceptor running. Once your
replica and acceptor nodes are set up, you can start the nameserver to
answer queries for **counterdomain** as follows:

.. sourcecode:: console

	$ sudo concoord nameserver -n counterdomain -f counter.py -c Counter -b ipaddr:port -t 1
	
When you set up the nameserver delegations, you can send queries for
counterdomain and see the most current set of nodes as follows:

.. sourcecode:: console

	$ dig -t a counterdomain                              # returns set of Replicas

	$ dig -t srv _concoord._tcp.counterdomain  	      # returns set of Replicas with ports

	$ dig -t txt counterdomain		              # returns set of all nodes

	$ dig -t ns counterdomain		              # returns set of nameservers

Slave Nameserver
^^^^^^^^^^^^^^^^^^^^^^^^ 
Before starting a slave nameserver node manually, you should have a
master nameserver set up and running. The master nameserver should be
set up to answer the queries for its slave nameservers. We provide
OpenReplica Nameserver as a ready to deploy master nameserver and a
Nameserver Coordination Object in our example objects set to keep track
of slave nameserver information. Using this coordination object, the
master nameserver can keep track of its slave nameserver delegations
and the slave nameserver can update the master every time the view of
its system changes.

Once your master nameserver is set up, you can start the slave nameserver as follows:

.. sourcecode:: console

	$ concoord nameserver -n counterdomain -f counter.py -c Counter -b ipaddr:port -t 2 -m masterdomain

When the slave nameserver starts running, you can send queries for counterdomain and see the most current set of nodes as follows:

.. sourcecode:: console

	$ dig -t a counterdomain		             # returns set of Replicas

	$ dig -t srv _concoord._tcp.counterdomain  	     # returns set of Replicas with ports

	$ dig -t txt counterdomain		             # returns set of all nodes

	$ dig -t ns counterdomain		             # returns set of nameservers

Amazon Route 53 Nameserver
^^^^^^^^^^^^^^^^^^^^^^^^
Before starting a nameserver connected to Amazon Route 53, you should have a
Route 53 account set up and ready to receive requests. After your
Route 53 account is ready, the nameserver can update the master every time the view of
its system changes automatically.

To use Amazon Route 53 you can pass your credentials into the methods
that create connections or edit them in the configuration file.

	  AWS_ACCESS_KEY_ID - Your AWS Access Key ID
	  AWS_SECRET_ACCESS_KEY - Your AWS Secret Access Key

Once you make sure that your Route53 account is set up and your
credentials are updated, you can start the nameserver as follows:

.. sourcecode:: console

	$ concoord nameserver -n counterdomain -f counter.py -c	Counter -b ipaddr:port -t 3 -o configfilepath

Starting Nodes Automatically
------------------------
We have a script we use for openreplica.org to start desired number of
nodes on PlanetLab servers automatically. This script is included for
your reference.

    ``concoord/openreplica/openreplicainitializer.py``

* Note that the script requires host and user-specific credentials and
  you will have to edit the script for your own use.

* Note that the nameserver nodes are started in the slave mode.

You can run the script as follows:

.. sourcecode:: console

	$ concoord initialize -s counterdomain -f /foo/counter.py -c Counter -r 3 -a 3 -n 3

Adding Nodes Automatically
------------------------
We also have a script we use for openreplica.org to add nodes on
PlanetLab servers automatically. This script is included for your
reference.

    ``concoord/openreplica/openreplicaaddnode.py``

* Note that the script requires host and user-specific credentials and
  you will have to edit the script for your own use.

You can run the script as follows:

.. sourcecode:: console

	$ concoord addnode -t nodetype -s counterdomain -f /foo/counter.py -c Counter -b bootstrap

where ``nodetype`` := 1 for Acceptor, 2 for Replica, 3 for Nameserver
          ``bootstrap`` := ipaddr:port or domainname for an instance that has a nameserver

Connecting to ConCoord Objects
------------------------
Once you have concoord up and running for your object, it is easy to
access your object.

Now we will use the proxy object we generated at (3.1) and saved under
``/foo/concoordproxy.py``. Now you can import and use this proxy object in
your code. Depending on how you set your nameserver node up, you can
access your object with the **ipaddr:port** pair or the **domainname**.

.. sourcecode:: pycon

	>>> from counterproxy import Counter
	>>> c = Counter(domainname)
	>>> c.increment()
	>>> c.increment()
	>>> c.getvalue()
	2

* Note that the objects on the Replica side are initialized without
  parameters. For you this has two implications:

1. While implementing your objects you should create your  ``__init__``
    functions to be called without parameters.
2. Keep in mind that when you initialize an object through the proxy,
    it only connects to the specified bootstrap, it does not reinitialize
    the object. This way multiple clients can connect to the same object
    using their proxies without reinitializing the object.
3. At any point to reinitialize an object after it is deployed on
    replicas, you should call ``__concoordinit__`` function:

.. sourcecode:: pycon

	>>> from counterproxy import Counter
	>>> c = Counter(domainname)
	>>> c.increment()
	>>> c.__concoordinit__()
	>>> c.increment()
	>>> c.getvalue()
	1
	    
