Creating Source Bundles
-----------------------

You can create bundles to use at the server and client sides using the
``Makefile`` provided under ``concoord/``

Remember to add the objects you have created in these bundles.

Creating A Server Bundle
~~~~~~~~~~~~~~~~~~~~~~~~

To create a bundle that can run replica, acceptor and nameserver
nodes:

.. sourcecode:: console

  $ make server

Creating A Client Bundle
~~~~~~~~~~~~~~~~~~~~~~~~

To create a bundle that can run a client and connect to an existing
ConCoord instance:

.. sourcecode:: console

  $ make client

Logging
-------

We have two kinds of loggers for ConCoord:

* Console Logger
* Network Logger

Both of these loggers are included under ``utils.py``. To start the
``NetworkLogger``, use the ``logdaemon.py`` on the host you want to keep the
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
an example below using the ``Semaphore`` object under
``concoord/object/semaphore.py``

In the blocking object implementation, the method invocations that use
an object from the threading library requires an extra argument
``_concoord_command``. This argument is used by the calling Replica node
to relate any blocking/unblocking method invocation to a specific
client. This way, even if the client disconnects and reconnects, the
ConCoord instance will remain in a safe state.

.. sourcecode:: python

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

To create the proxy for this blocking object we will use the following command:

.. sourcecode:: console

  $ concoord object -o semaphore.Semaphore -p 1

This command creates the proxy that supports blocking operations. Now
you can use blocking objects just like basic ConCoord objects. First,
we start the replica, acceptor and nameserver nodes the same way we
did before as follows:

.. sourcecode:: console

  $ concoord replica -o semaphore.Semaphore -a 127.0.0.1 -p 14000

.. sourcecode:: console

  $ concoord acceptor -b 127.0.0.1:14000

.. sourcecode:: console

  $ sudo concoord nameserver -n semaphoredomain -o semaphore.Semaphore -b 127.0.0.1:14000 -t 1

To test the functionality, you can use multiple clients or print out the ``Semaphore`` object as follows:

.. sourcecode:: pycon

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
