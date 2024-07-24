#!/bin/bash
#setup the docker images/containers for discord
sudo docker build -t kurusaki .
sudo docker network create discord #creat network
cd lavalink
sudo docker build -t lavalink .
sudo docker run -d --name kurusaki --net discord -v /home/kurusaki:/kurusaki_data kurusaki