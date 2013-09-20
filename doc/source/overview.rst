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

.. image:: _static/concoord.jpg
    :align: center


