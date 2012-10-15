#!/bin/sh

cd ../src && rm -rf dist/ && python setup.py sdist --formats=zip,gztar,bztar,tar
scp dist/* deniz@egs-110.cs.cornell.edu:/var/www/openreplica.src