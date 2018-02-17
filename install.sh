#!/bin/bash

sudo yum update -y &&
sudo yum groupinstall "Development tools" -y &&
mkdir src &&
cd src &&
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz &&
tar xvf ta-lib-0.4.0-sr.tar.gz &&
cd ta-lib &&
./configure &&
make &&
sudo make install &&
cd .. &&
sudo yum install python36 python36-virtualenv &&
python3 -m virtualenv env &&
source env/bin/activate &&
pip install -r requirements.txt &&
echo "Done!"
