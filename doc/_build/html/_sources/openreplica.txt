Using OpenReplica
-----------------

OpenReplica provides easily launch for concoord on remote machines,
and it is especially built to launch concoord instances on Amazon EC2
servers easily. In this section we cover how you can setup a set of
machines and launch concoord remotely using OpenReplica.

How to start using Amazon EC2
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can easily launch your EC2 instances using the web interface
provided by Amazon AWS. In this example we launch an instance running
64-bit Amazon Linux. Before you launch your instance, you will have to
create a keypair to login to your instances, make sure to keep your
private key safe. The best way is to move your key-pair to the .ssh
directory once you download the [my-key-pair].pem file:

.. sourcecode:: console

  $ mv [my-key-pair].pem ~/.ssh/
  $ ssh-add ~/.ssh/[my-key-pair].pem

Once you did these, now is the time to connect to your instance:

.. sourcecode:: console

  $ ssh -i [my-key-pair].pem ec2-user@[public_dns_name]

After this point on, you should be able to connect to your instance
without explicitly passing the key as a parameter, as follows:

.. sourcecode:: console

  $ ssh ec2-user@[public_dns_name]

To enable execution of remote sudo commands SSH into your instance and run:

.. sourcecode:: console

  $ sudo visudo

In the file that opens find the line ``Defaults requiretty`` and add
line ``Defaults:ec2-user !requiretty`` below it. Save the file and
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

To add the sshkey:

.. sourcecode:: console

  $ openreplica addsshkey [my-key-pair].pem

To add the username:

.. sourcecode:: console

  $ openreplica addusername ec2-user

To add a node:

.. sourcecode:: console

  $ openreplica addnode [public_dns_name]

When adding nodes to OpenReplica, it automatically checks the nodes
for eligibility to run ConCoord and warns the user if an update or
change is required. Similarly, if ConCoord cannot connect to the node,
it lets the user know.

.. sourcecode:: console

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
another replica:

.. sourcecode:: console

  $ openreplica replica -o concoord.object.counter.Counter -a 127.0.0.1 -p 14000

To start replica nodes to join an active ConCoord instance:

.. sourcecode:: console

  $ openreplica replica -o concoord.object.counter.Counter -b 127.0.0.1:14000 -a 127.0.0.1 -p 14001

The nodes can also be run in the debug mode or with a logger with the
commands shown below:

``Usage: openreplica replica [-h] [-a ADDR] [-p PORT] [-b BOOTSTRAP] [-o OBJECTNAME] [-l LOGGER] [-w] [-d]``
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
+++++++++++++++++++++++++

Before starting a standalone nameserver node, first make sure
that you have at least one replica running. Once your replica nodes
are set up, you can start the nameserver to answer queries.

Starting a Standalone Nameserver
********************************

You can start the nameserver to answer queries for
``counterdomain.com`` as follows:

.. sourcecode:: console

  $ sudo openreplica nameserver -n counterdomain.com -o concoord.object.counter.Counter -b 127.0.0.1:14000 -t 1

Amazon Route 53 Nameserver
**************************

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

  $ openreplica nameserver -n counterdomain.com -o concoord.object.counter.Counter -b 127.0.0.1:14000 -t 3 -c configfilepath
