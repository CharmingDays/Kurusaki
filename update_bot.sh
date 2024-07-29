# !/bin/bash
# auto update the bot with the latest github commit and restart the bot service
local_hash=$(cat ~/local_hash.txt)
latest_commit=$(git ls-remote https://github.com/CharmingDays/Kurusaki HEAD | awk '{ print $1 }')
if [[ $local_hash == $latest_commit ]]; then
        echo "No new changes commited"
        exit 1
else
    echo "Stoping Kurusaki Docker Container..."
    sudo docker stop kurusaki
    echo "Removing Kurusaki Docker Container and image..."
    sudo docker rm kurusaki
    sudo docker rmi kurusaki
    echo "cloning latest commit..."
    git clone https://github.com/CharmingDays/Kurusaki clone #clone the latest commit
    echo "Replacing files..."
    mv clone/kurusaki kurusaki_copy #move the bot folder to a new folder
    mv kurusaki/.env kurusaki_copy #move the .env file to the new folder
    sudo rm -r clone kurusaki #remove the old bot folder
    mv kurusaki_copy kurusaki #rename the folder back to kurusaki
    cd kurusaki
    echo "Building Kurusaki Docker Container..."
    chmod +x docker.sh
    ./docker.sh
fi