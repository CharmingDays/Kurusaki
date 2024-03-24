#!/bin/bash
#setup the docker images/containers for discord
sudo docker build -t kurusaki.
sudo docker network create discord
cd lavalink
sudo docker build -t lavalink .
sudo docker run -d -p 2333:2333/tcp -p 2333:2333/udp --name lavalink --net discord --restart always lavalink
sudo docker run -d --name kurusaki --net discord kurusaki