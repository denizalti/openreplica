OpenReplica
-----------

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

``Usage: openreplica replica [-h] [-a ADDR] [-p PORT] [-b BOOTSTRAP] [-o OBJECTNAME] [-l LOGGER] [-n DOMAIN] [-r] [-w] [-d]``

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
+++++++++++++++++++++++++

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

  $ openreplica replica -o concoord.object.counter.Counter -a 127.0.0.1 -n counterdomain.com

And to start the replica to join an already running ConCoord instance,
provide the bootstrap:

.. sourcecode:: console

  $ openreplica replica -o concoord.object.counter.Counter -a 127.0.0.1 -b 127.0.0.1:14000 -n counterdomain.com

When the replica starts running, you can send queries for
``counterdomain.com`` and see the most current set of nodes as
follows:

.. sourcecode:: console

  $ dig -t a counterdomain.com                   # returns set of Replicas

  $ dig -t srv _concoord._tcp.counterdomain.com  # returns set of Replicas with ports

  $ dig -t txt counterdomain.com                 # returns set of all nodes

  $ dig -t ns counterdomain.com                  # returns set of name servers

Amazon Route53 Name Server
++++++++++++++++++++++++++

First make sure that boto is installed on the machine you want to run
the Route53 name server. OpenReplica tries to do this automatically
when a replica is run as a Route53 name server, but if it fails to do
so, you can easily install boto on the machine you want as follows:

.. sourcecode:: console

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

  $ openreplica route53 [public_dns AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY]


Once you make sure that your Route53 account is set up and the
configuration file includes your AWS credentials, you can start the
replica with a name server as follows:

.. sourcecode:: console

  $ openreplica replica -o concoord.object.counter.Counter -n counterdomain.com -r

When the replica starts running, you can send queries for
``counterdomain.com`` and see the most current set of nodes as follows:

.. sourcecode:: console

  $ dig -t a counterdomain.com                   # returns set of Replicas

  $ dig -t srv _concoord._tcp.counterdomain.com  # returns set of Replicas with ports

  $ dig -t txt counterdomain.com                 # returns set of all nodes

  $ dig -t ns counterdomain.com                  # returns set of name servers
