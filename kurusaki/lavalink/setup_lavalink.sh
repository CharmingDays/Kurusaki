#!/bin/bash
# install java 18
sudo apt install openjdk-18-jre-headless -y
# create service file
sudo cp lavalink.service /etc/systemd/system/
sudo systemctl enable lavalink.service
sudo systemctl reload-daemon
sudo systemctl start lavalink.service
