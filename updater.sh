# !/bin/bash
# auto update the bot with the latest github commit and restart the bot service
wget https://github.com/CharmingDays/Kurusaki clone
mv clone/kurusaki copy
sudo mr -r clone kurusaki
mv copy kurusaki
sudo systemctl restart kurusaki.service