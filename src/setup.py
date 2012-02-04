import sys
from distutils.core import setup

concoordversion = '1.0.0'

classifiers = [ 'Development Status :: 3 - Alpha'
              , 'Intended Audience :: Developers'
              , 'Intended Audience :: System Administrators'
              , 'License :: OSI Approved :: BSD License'
              , 'Operating System :: MacOS :: MacOS X'
              , 'Operating System :: POSIX :: Linux'
              , 'Operating System :: Unix'
              , 'Programming Language :: Python :: 2.7'
              ]

setup(name='ConCoord',
      version=concoordversion,
      author='Deniz Altinbuken Emin Gun Sirer',
      author_email='deniz@systems.cs.cornell.edu egs@systems.cs.cornell.edu',
      packages=['concoord', 'concoord.objects', 'concoord.threadingobjects', 'concoord.openreplica'],
      package_data={'concoord.openreplica': ['data/openreplicakey', 'data/eligiblenodes.txt', 'data/plnodes.txt']},
      license='2-clause BSD',
      url='http://openreplica.org/',
      download_url='http://openreplica.org/XXX',
      description='ConCoord Coordination Service for Distributed Systems',
      long_description=open('README.txt').read(),
      classifiers=classifiers,
      )
