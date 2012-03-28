Creating Source Bundles
------------------------
      To create bundles to use at the server and client sides you can
      use the Makefile provided under 'concoord/'

      Remember to add the objects you have created in these
      bundles.

Creating A Server Bundle
------------------------
To create a bundle that can run replica, acceptor and nameserver nodes:

.. sourcecode:: console

	$ make server


Creating A Client Bundle
------------------------
To create a bundle that can run a client and connect to an existing
ConCoord instance:

.. sourcecode:: console
	$ make client

Logging
------------------------
We have two kinds of loggers for ConCoord:
* Console Logger
* Network Logger

Both of these loggers are included under utils.py

To start the NetworkLogger, use the logdaemon.py on the host you
want to keep the Logger.

.. sourcecode:: console
        $ python logdaemon.py

Synchronization & Threading
------------------------

Nameserver Options
===================

Running A Master Nameserver
------------------------

Running A Slave Nameserver
------------------------

Amazon Route 53
------------------------
To use Amazon Route 53 you can pass your credentials into the methods
that create connections.  Alternatively, boto will check for the
existance of the following environment variables to ascertain your credentials:

	  AWS_ACCESS_KEY_ID - Your AWS Access Key ID
	  AWS_SECRET_ACCESS_KEY - Your AWS Secret Access Key
