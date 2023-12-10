#!/bin/bash

# install the libs
pip install -r requirements.txt
# install java 18
sudo apt install openjdk-18-jre-headless -y
python -m spacy download en_core_web_lg