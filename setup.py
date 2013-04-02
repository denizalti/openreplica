
import os
import re
import sys

from setuptools import setup
from setuptools import find_packages


v = open(os.path.join(os.path.dirname(__file__), 'concoord', '__init__.py'), 'r')
VERSION = re.match(r".*__version__ = '(.*?)'", v.read(), re.S).group(1)


classifiers = [
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'Intended Audience :: System Administrators',
    'License :: OSI Approved :: BSD License',
    'Operating System :: MacOS :: MacOS X',
    'Operating System :: POSIX :: Linux',
    'Operating System :: Unix',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2.6',
    'Programming Language :: Python :: 2.7',
]


ldesc="""ConCoord is a novel coordination service that provides replication and
synchronization support for large-scale distributed systems. ConCoord employs an
object-oriented approach, in which the system actively creates and maintains
live replicas for user-provided objects. Through ConCoord, the clients areable
to access these replicated objects transparently as if they are local objects.
The ConCoord approach proposes using these replicated objects to implement
coordination constructs in large-scale distributed systems, in effect
establishing a transparent way of providing a coordination service."""


setup(
    name='concoord',
    version=VERSION,
    author='Deniz Altinbuken, Emin Gun Sirer',
    author_email='deniz@systems.cs.cornell.edu, egs@systems.cs.cornell.edu',
    packages=find_packages(),
    data_files=[('/etc/bash_completion.d', ['scripts/bash_completion/concoord'])],
    license='3-Clause BSD',
    url='http://openreplica.org/',
    description='Coordination service for distributed systems.',
    long_description=ldesc,
    classifiers=classifiers,
    entry_points={
        'console_scripts': [
            'concoord=concoord.main:main',
        ]
    },
    install_requires=[
        'dnspython>=1.9.4',
    ],

)
