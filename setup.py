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
    'Programming Language :: Python :: 2.7',
]

extra = {}

install_requires=[
    'python>=2.7',
    'msgpack-python',
    'dnspython',
    'six',
]

if sys.version_info >= (3,):
    extra['use_2to3'] = True
    #extra['convert_2to3_doctests'] = ['src/your/module/README.txt']
    #extra['use_2to3_fixers'] = ['lib2to3.print']
    install_requires = ['msgpack-python',
                        'dnspython3',
                        'six',
                    ]
    print ("install_requires is %r extra is %r" %(install_requires, extra))

setup(
    name='concoord',
    version=VERSION,
    author='Deniz Altinbuken, Emin Gun Sirer',
    author_email='deniz@systems.cs.cornell.edu, egs@systems.cs.cornell.edu',
    packages=find_packages(),
    license='3-Clause BSD',
    url='http://openreplica.org/',
    description='Coordination service for distributed systems.',
    long_description=open('README').read(),
    classifiers=classifiers,
    entry_points={
        'console_scripts': ['concoord = concoord.main:main',]
    },
    install_requires = install_requires,
    **extra
)
