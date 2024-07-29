#!/bin/bash
docker build --no-cache -t lavalink .
docker run -d -p 2333:2333/tcp -p 2333:2333/udp --name lavalink --net discord --restart always -v /home/ubuntu/kurusaki/lavalink:/lavalink_data lavalink