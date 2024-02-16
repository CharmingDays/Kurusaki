#!/bin/bash
sudo docker build -t lavalink
docker run -d -p 2333:2333/tcp -p 2333:2333/udp --name lavalink_server --restart always lavalink