#!/bin/bash
# install the libs
pip install -r requirements.txt
sudo cp kurusaki.service /etc/systemd/system/
sudo systemctl enable kurusaki.service
sudo systemctl start kurusaki.service
