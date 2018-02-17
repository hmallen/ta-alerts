#!/bin/bash

sudo yum update &&
sudo yum groupinstall "Development tools" &&
mkdir src &&
cd src &&
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz &&
tar xvf ta-lib-0.4.0-sr.tar.gz &&
cd ta-lib &&
./configure &&
make &&
sudo make install &&
echo "Done!"
