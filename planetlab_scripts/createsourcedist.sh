#!/bin/sh

cd ../src && rm -rf dist/ && python setup.py sdist --formats=zip,gztar,bztar,tar