import os
import re
import sys

from setuptools import setup
from setuptools import find_packages

classifiers = [
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'Intended Audience :: System Administrators',
    'License :: OSI Approved :: BSD License',
    'Operating System :: MacOS :: MacOS X',
    'Operating System :: POSIX :: Linux',
    'Operating System :: Unix',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2.7',
]

setup(
    name='concoord',
    version='1.1.0',
    author='Deniz Altinbuken, Emin Gun Sirer',
    author_email='deniz@systems.cs.cornell.edu, egs@systems.cs.cornell.edu',
    packages=find_packages(),
    license='3-Clause BSD',
    url='http://openreplica.org/',
    description='Coordination service for distributed systems.',
    long_description=open('README').read(),
    classifiers=classifiers,
    entry_points={
        'console_scripts': ['concoord = concoord.main:main',
                            'openreplica = concoord.openreplica.main:main']
    },
    install_requires=[
        'python>=2.7',
        'msgpack-python',
        'dnspython',
    ],
)
