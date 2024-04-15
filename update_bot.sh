# !/bin/bash
# auto update the bot with the latest github commit and restart the bot service
sudo docker stop kurusaki
sudo docker rm kurusaki
sudo docker rmi kurusaki
git clone https://github.com/CharmingDays/Kurusaki clone #clone the latest commit
mv clone/kurusaki kurusaki_copy #move the bot folder to a new folder
mv kurusaki/.env kurusaki_copy #move the .env file to the new folder
sudo rm -r clone kurusaki #remove the old bot folder
mv kurusaki_copy kurusaki #rename the folder back to kurusaki   
cd kurusaki
chmod +x docker.sh
./docker.sh