#!/bin/bash
#setup the docker images/containers for discord
sudo docker build -t kurusaki .
sudo docker network create discord #creat network
sudo docker run -d --name kurusaki --net discord kurusaki