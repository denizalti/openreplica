---
layout: page
---

OpenReplica was built to provide an object-oriented coordination service for Distributed Systems.
Unlike the widely-used counterparts such as ZooKeeper and Chubby, OpenReplica does not
use a file-system API, instead it enables servers to coordinate over objects
that can run code. This way required coordination behavior can be implemented
as an object!

OpenReplica provides availability, reliability and fault-tolerance in distributed systems. It is designed to maintain long-lived, critical state (such as configuration information) and to synchronize distributed components. It works as follows: you define a Python object that encapsulates the state you want replicated, along with methods that can update it, and can synchronize threads that access it. You give it to OpenReplica, your object gets geographically distributed automatically, and you receive a proxy through which multiple clients can access the replicated object transparently. To the rest of your application, your replicated object appears as a regular Python object when you use the provided proxy.

OpenReplica ensures that new object replicas are dynamically created to compensate for any node or network failures involving your nodes. Our current implementation executes replicas on PlanetLab hosts distributed at academic sites around the globe, on failure independent hosts. You could also use the code behind OpenReplica to deploy on other hosts, and integrate with DNS and Amazon Route 53.

OpenReplica is similar to services such as Google's Chubby and Yahoo's ZooKeeper, except for a critical difference: OpenReplica provides an object-oriented interface to applications. Overall, OpenReplica differs from existing systems in the following ways:

* **High Performance:** Coupled with the concurrent Paxos protocol our implementation uses, the object-based API obviates the need for costly serialization and achieves much higher performance than other systems.
* **Dynamic Implementation:** OpenReplica enables any server to be replaced at run-time. There are no statically designated servers, or configuration files -- any and all servers can be changed on the fly.
* **DNS Integration:** Clients locate the up-to-date replicas through DNS. OpenReplica enables you to run your own authoritative DNS server, or to use a subdomain under openreplica.org, or to use Amazon's Route 53.
* **Easy to use:** Smoothly integrates into your existing Python program, no external interfaces needed. Even complex coordination functionality, such as implementing synchronization objects like semaphores, is straight-forward.

**How does OpenReplica work?**

OpenReplica is powered by ConCoord, a novel coordination service that provides replication and synchronization support for large-scale distributed systems. ConCoord employs an object-oriented approach, in which the system actively creates and maintains live replicas for user-provided objects. Through ConCoord, the clients are able to access these replicated objects transparently as if they are local objects. The ConCoord approach proposes using these replicated objects to implement coordination constructs in large-scale distributed systems, in effect establishing a transparent way of providing a coordination service.

<img src="../static/concoord.jpg" width="100%" vspace="0">

**ConCoord Design**

To support complex distributed synchronization constructs, ConCoord presents a novel mechanism that enables the replicated objects to control the execution flow of their clients, in essence providing blocking and non-blocking method invocations on a replicated object. ConCoord employs Paxos as the underlying consensus protocol to tolerate crash failures of hosts and the underlying network. To facilitate deployments in dynamic cloud environments, the implementation supports view changes, which permit any number of servers to be replaced at runtime. Integration with DNS enables clients to easily locate the most current set of replicas.

<br>
<br>
This website is built and maintained by [Deniz Altınbüken, Ph.D.](https://denizaltinbuken.com) OpenReplica is not actively maintained but it is available as an open-source project. If you have questions, you can contact me at [hello@{{ site.address }}](mailto:hello@{{ site.address }})
