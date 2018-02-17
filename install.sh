#!/bin/bash

sudo yum update -y &&
sudo yum groupinstall "Development tools" -y &&
mkdir -p src &&
cd src &&
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz &&
tar xvf ta-lib-0.4.0-src.tar.gz &&
cd ta-lib &&
./configure &&
make &&
sudo make install &&
cd .. &&
sudo yum install python36 python36-virtualenv -y &&
python3 -m virtualenv env &&
source env/bin/activate &&
pip install git+https://github.com/s4w3d0ff/python-poloniex.git &&
pip install -r requirements.txt &&
echo "Done!"
