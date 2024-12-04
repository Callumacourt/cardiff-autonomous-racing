#!/bin/sh
echo "---"
echo "installing UnrealEngine"
echo "---"
#Change the name of the directory if needed
cd UnrealEngine
./Setup.sh
./GenerateProjectFiles.sh
make
cd ..
echo "---"
echo "installing Airsim"
echo "---"
#Change the name of the directory if needed
cd Airsim
./setup.sh
./build.sh
cd ..
