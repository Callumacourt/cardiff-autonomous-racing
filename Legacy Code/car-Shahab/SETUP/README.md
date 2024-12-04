## Getting Started
This is a guide explaining how to setup the packaged version of the simulator in Ubuntu 20.04.This installation is aimed purely on the development of autopilot system. The reason this installation is done it is because the simulation is less heavy on your GPU. If your aim is to develop the enviroment for the simualtion do not follow this installation guide and go the 'SIMULATOR_SETUP_DEV.md' file.
## 0. Tools and documents needed for installation
Install the following:
``` commandline
sudo apt.get install git
sudo apt-get install git-lfs
sudo apt-get install python3-pip
```

Make sure that the following repoistories or packages downloaded are in the Documents folder
1. UnrealEngine
1. car repository
1. packaged version of the simulator
1. AirSim
1. pyftgl

Download the car repository.
``` commandline
cd Documents
git clone https://github.com/Cardiff-Autonomous-Racing/car.git
```
To download the packaged version follow this link (https://cf.sharepoint.com/teams/CardiffAutonomusRacing/Shared%20Documents/General/Simulator/car_sim_packaged.tar.gz). After downloading the packaged version make sure is in the path 'Documents'.

Then cuDNN v7.6.4 go to this website (https://developer.nvidia.com/rdp/cudnn-archive) and download the cuDNN v7.6.4 from September 27th, 2019. Make sure to download 'cuDNN Library for Linux' when downloading cuDNN v7.6.4

Download airsim repository (https://github.com/Microsoft/AirSim)

Download pyftgl repository (https://github.com/theodorik/pyftgl)

For this installation it was followed the setup guide from the official page of UE4 (https://docs.unrealengine.com/4.26/en-US/SharingAndReleasing/Linux/BeginnerLinuxDeveloper/SettingUpAnUnrealWorkflow/) To download the repository go to website. Make sure you download the 4.24 branch or newer releases. If not it would not work. (https://github.com/EpicGames/UnrealEngine)
## 1 installing all dependecies for autopilot
Now lets install all the dependecies that the autopilot system requires. Make sure that the paths in the bash script correspond to the location of your folder in your system.
``` commandline
cd Documents/car_master/SETUP
sudo chmod +x setup_autopilot.sh
./setup_autopilot.sh
```
Go to the directory 'car/autopilot' and open the file 'config.py'. After opening this file modify the file by changing "self.HIDPI = True" to "self.HIDPI = False".

## 2 Installing the simulator
Now the UnrealEngine4 and the AirSim downloaded before are going to be built. Make sure that the paths in the bash script correspond to the location of your folder in your system.
``` commandline
cd Documents/car_master/SETUP
sudo chmod +x setup_simulator.sh
./setup_simulator.sh
```
Copy the file 'settings.json' located in the path '/car/autopilot' and paste in the path 'airsim'. Make sure to paste the file on the airsim directory created in step 2.
``` commandline
cp ~/Documents/car/autopilot/settings.json ~Documents/AirSim/settings.json
```

## 3 Running the simulator with autopilot system
After run the simulator by going to UE4 and opening the simulator project.
``` commandline
cd Documents/car_sim_packaged
./CARSim.sh
```
If it does not work and has an error similar to this one:
``` commandline
X Error of failed request:  BadDrawable (invalid Pixmap or Window parameter)
  Major opcode of failed request:  149 ()
  Minor opcode of failed request:  4
  Resource id in failed request:  0x2a00041
  Serial number of failed request:  378
  Current serial number in output stream:  388
terminating with uncaught exception of type std::__1::system_error: mutex lock failed: Invalid argument
Signal 6 caught.
Segmentation fault (core dumped)
```
This means that Vulkan does not work. This is due to your hardware being old. Do not worry this happened to me, you are not the only one with old hardware. To solve this error you need to run it with the predecessor of Vulkan which is OpenGL. This is done by running this command:
``` commandline
./CARSim.sh -opengl
```
If it does not work and has an error similar to this one:
``` commandline
Error of failed request:  BadValue (integer parameter out of range for operation)
Major opcode of failed request:  152 (GLX)
Minor opcode of failed request:  3 (X_GLXCreateContext)
Value in failed request:  0x0
Serial number of failed request:  109
Current serial number in output stream:  110 terminating with uncaught exception of type std::__1::system_error: mutex lock failed: Invalid argument Signal 6 caught. Malloc Size=65538 LargeMemoryPoolOffset=65554  CommonUnixCrashHandler: Signal=6 Failed to find symbol file, expected location: "/home/samuel/Documents/car_sim_packaged/CARSim/Binaries/Linux/CARSim-Linux-Test.sym" Segmentation fault (core dumped)
```
Then make sure that the correct driver is installed. This can be checked in ubuntu by going to the "Software & updates" app and go to "Additional Drivers". Make sure you have a NVIDIA driver greater than 418.39.

Finally, open a new terminal and run the autopilot system: 
``` commandline
cd /car/autopilot
python3 autopilot.py
```

Now you are ready to start developing on the autopilot system.
Good luck. You will need it.
