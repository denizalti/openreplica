Advanced Tutorial
===================

Creating Source Bundles
------------------------
You can create bundles to use at the server and client sides using the
Makefile provided under ``concoord/``

Remember to add the objects you have created in these bundles.

Creating A Server Bundle
^^^^^^^^^^^^^^^^^^^^^^^^
To create a bundle that can run replica, acceptor and nameserver nodes:

.. sourcecode:: console

	$ make server

Creating A Client Bundle
^^^^^^^^^^^^^^^^^^^^^^^^
To create a bundle that can run a client and connect to an existing ConCoord instance:

.. sourcecode:: console

	$ make client

Logging
------------------------
We have two kinds of loggers for ConCoord:
* Console Logger
* Network Logger

Both of these loggers are included under utils.py

To start the NetworkLogger, use the logdaemon.py on the host you want to keep the Logger.

.. sourcecode:: console
        $ python logdaemon.py

Synchronization & Threading
------------------------
ConCoord provides a distributed and fault-tolerant threading
library. The library includes:

* Lock
* RLock
* Semaphore
* BoundedSemaphore
* Barrier
* Condition

The implementations of distributed synchronization objects follow the
implementations in the Python threading library.

