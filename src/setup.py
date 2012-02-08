import sys
from distutils.core import setup

concoordversion = '0.1.0'

classifiers = [ 'Development Status :: 3 - Alpha'
              , 'Intended Audience :: Developers'
              , 'Intended Audience :: System Administrators'
              , 'License :: OSI Approved :: BSD License'
              , 'Operating System :: MacOS :: MacOS X'
              , 'Operating System :: POSIX :: Linux'
              , 'Operating System :: Unix'
              , 'Programming Language :: Python'
              ]

ldesc = "ConCoord is a novel coordination service that provides replication and
	synchronization support for large-scale distributed systems. ConCoord
	employs an object-oriented approach, in which the system actively
	creates and maintains live replicas for user-provided objects. Through
	ConCoord, the clients are able to access these replicated objects
	transparently as if they are local objects.  The ConCoord approach
	proposes using these replicated objects to implement coordination
	constructs in large-scale distributed systems, in effect establishing
	a transparent way of providing a coordination service."

setup(name='concoord',
      version=concoordversion,
      author='Deniz Altinbuken, Emin Gun Sirer',
      author_email='deniz@systems.cs.cornell.edu, egs@systems.cs.cornell.edu',
      packages=['concoord', 'concoord.objects', 'concoord.threadingobjects', 'concoord.openreplica'],
      package_data={'concoord.openreplica': ['data/openreplicakey', 'data/eligiblenodes.txt', 'data/plnodes.txt']},
      license='2-Clause BSD',
      url='http://openreplica.org/',
      description='ConCoord Coordination Service for Distributed Systems',
      long_description=ldesc,
      classifiers=classifiers,
      
      )
