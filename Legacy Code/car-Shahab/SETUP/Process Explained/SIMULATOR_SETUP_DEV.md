## Getting Started
This is a guide explaining how to setup the simulator in Ubuntu 20.04. This setup allows for development of enviroment and for autopilot system. This installation is aimed for the development of the simulation enviroment. The reason the autopilot system is also installed is to test the performance of the autonomous system with the simulator. If you are planning in only working in the development of the autonomous system do not follow this instructions and follow the 'SIMULATOR_SETUP.md' file.

Make sure to follow the order of installation. If not it will not install properly.

## 0. Tools and documents needed for installation
Install the following:
``` commandline
sudo apt.get install git
sudo apt-get install git-lfs
sudo apt-get install python3-pip
```
Before starting download the car and simulator repository. 
``` commandline
cd Documents
git clone https://github.com/Cardiff-Autonomous-Racing/car.git
git clone https://github.com/Cardiff-Autonomous-Racing/simulation.git
cd simulation
git lfs install
```
## 1. Install UnrealEngine 4 (UE4)
For this installation it was followed the setup guide from the official page of UE4 (https://docs.unrealengine.com/4.26/en-US/SharingAndReleasing/Linux/BeginnerLinuxDeveloper/SettingUpAnUnrealWorkflow/). 
First we clone the Epic games repositroy from github and it is built in the Linux enviroment.
To download the repository go to website. Make sure you download the 4.24 branch or newer releases. If not it would not work. (https://github.com/EpicGames/UnrealEngine)
``` commandline
cd UnrealEngine
./Setup.sh
./GenerateProjectFiles.sh
make
cd
```
To check if UE4 has been properly install try and run it using the following commands:
``` commandline
cd UnrealEngine/Engine/Binaries/Linux
./UE4Editor
```
## 2. Building Airsim for UE4
Go and download the airsim repository (https://github.com/Microsoft/AirSim) and put the file in 'Home'
``` commandline
cd Airsim
./setup.sh
./build.sh
```
Then copy and paste the directory of 'Plugins' under the path '/airsim/Unreal' and paste the directory to the path '/Documents/simulation'
## 3. Installing CUDA and cudNN
Installing CUDA10.1 and cuDNN v7.6.4 in ubuntu 20.04. Since it is not supported from the official website this method is quicker. Before proceding this installation check your nvidia driver. Make sure is your driver version is >= 418.39
First install CUDA 10.1. 
``` commandline
sudo apt install nvidia-cuda-toolkit
```
To verify if CUDA was successful run this command:
``` commandline
nvcc -V
```
Then cuDNN v7.6.4 go to this website (https://developer.nvidia.com/rdp/cudnn-archive) and download the cuDNN v7.6.4 from September 27th, 2019. Make sure to download 'cuDNN Library for Linux' when downloading cuDNN v7.6.4
``` commandline
tar -xvzf cudnn-10.1-linux-x64-v7.6.4.38.tgz
sudo cp cuda/include/cudnn.h /usr/lib/cuda/include/
sudo cp cuda/lib64/libcudnn* /usr/lib/cuda/lib64/
sudo chmod a+r /usr/lib/cuda/include/cudnn.h /usr/lib/cuda/lib64/libcudnn*
echo 'export LD_LIBRARY_PATH=/usr/lib/cuda/lib64:$/usr/lib/nvidia-cuda-toolkit' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/lib/cuda/include:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc
```
To verify if cuDNN was successful run this command:
``` commandline
cat /usr/lib/cuda/include/cudnn.h | grep CUDNN_MAJOR -A 2
```
## 4. Install pyCUDA
For installing pyCUDA
``` commandline
sudo apt-get install python3-pycuda
```
## 5. Install libpng12-0
Installing libpng12-0:
``` commandline
sudo add-apt-repository ppa:linuxuprising/libpng12
sudo apt update
sudo apt install libpng12-0
```
## 6. Install Boost C++
For installing Boost C++ following this webpage (https://www.osetc.com/en/how-to-install-boost-on-ubuntu-16-04-18-04-linux.html)
``` commandline
sudo apt install libboost-dev
sudo apt install libboost-all-dev
pip3 install boost
```
To verify installation do:
``` commandline
cat /usr/include/boost/version.hpp | grep "BOOST_LIB_VERSION"
```
## 7. Install OpenCV-Python
For installing OpenCV-Python it was followed the following webpage (https://docs.opencv.org/master/d2/de6/tutorial_py_setup_in_ubuntu.html) and then it was reinstalled using pip3.
``` commandline
sudo apt-get install python3-opencv
sudo apt-get install cmake
sudo apt-get install gcc g++
sudo apt-get install python3-dev python3-numpy
sudo apt-get install libavcodec-dev libavformat-dev libswscale-dev
sudo apt-get install libgstreamer-plugins-base1.0-dev libgstreamer1.0-dev
sudo apt-get install libgtk-3-dev
pip3 install opencv-python
```
## 8. Install neat
For installing neat:
``` commandline
pip3 install neat
```
## 9. Install numpy
For installing wxPython:
``` commandline
pip3 install numpy
```
## 10. Install matplotlib
For installing matplotlib:
``` commandline
sudo apt-get install python3-matplotlib
```
## 11. Install scipy
For installing matplotlib:
``` commandline
sudo apt-get install python3-scipy
```
## 12. Install OpenGL
For installing OpenGL:
``` commandline
sudo apt-get install python3-opengl
```
## 13. Install FTGL
For installing FTGL follow this commands:
``` commandline
sudo apt-get install libftgl2
sudo apt-get install -y libftgl-dev
```
install pyFTGL from here (https://github.com/theodorik/pyftgl)
``` commandline
sudo -i
cd ..
cd usr/lib/x86_64-linux-gnu
sudo ln -s libboost_python38.so libboost_python3.so
```
Close the terminal and open a new one and do this commands
``` commandline
cd pyftgl
python3 setup.py build
sudo python3 setup.py install
```
## 14. Install X-11
For installing X-11:
``` commandline
sudo apt-get install xauth
sudo apt-get install xorg
sudo apt-get install openbox
```
## 15. Install wxPython
For installing wxPython download 'wxPython-4.1.1-cp38-cp38-linux_x86_64.whl' from webpage (https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-20.04/). Then put file in our 'Home' and finally run the following commands:
NEED TO CHECK IF IT IS THE FIRST OR THE SECOND THE ONE WHICH WORKS
``` commandline
sudo apt-get install python3-venv
python3 -m venv builder_py
source builder_py/bin/activate
which python3
which pip3
pip3 download wxPython
pip3 install -U pip
pip3 install -U six wheel setuptools
pip3 wheel -v wxPython-4.1.1.tar.gz  2>&1 | tee build.log
pip3 install wxPython-4.1.1-cp38-cp38-linux_x86_64.whl
```
Now close the terminal and reopen it.
``` commandline
sudo apt install python3-pip make gcc libgtk-3-dev libgstreamer-gl1.0-0 freeglut3 freeglut3-dev python3-gst-1.0 libglib2.0-dev ubuntu-restricted-extras libgstreamer-plugins-base1.0-dev
sudo apt-get install python3-wxgtk4.0
pip3 install --user wxPython
```
To verify installation do:
``` commandline
python3 -c "import wx; a=wx.App(); wx.Frame(None,title='hello world').Show(); a.MainLoop();"
```
## 16. Install line profiler
Installing line profiler
``` commandline
cd Documents/car/autopilot
pip3 install line_profiler
```
## 17. Install airsim
Installing airsim for autopilot. In a previous stage you had build airsim for UE4. They are not the same installation so do not skip.
``` commandline
cd Documents/car/autopilot
pip3 install airsim
```
## 18. Install ap
Installing airsim for autopilot. In a previous stage you had build airsim for UE4. They are not the same installation so do not skip.
``` commandline
cd Documents/car/autopilot/ap
python3 setup.py build
cd ..
ln -s ap/build/lib.linux-86_64-3.8/ap.cpython-38-x86_64-linux-gnu.so
```
If the symbolic link of the file 'ap.cpython-38-x86_64-linux-gnu.so' does not work just copy and paste the file in the path '/car/autopilot'.
## 19. Install zsh
THIS IS NOT NEEDED. But is a preference from the user. For more info do your research. This modifies you shell. from 'bash' which is the default in ubuntu to 'zsh'
``` commandline
sudo apt install zsh
echo $SHELL
chsh -s /usr/bin/zsh
cd
zsh
1
1
0
```
To change back to 'bash' if you want to then do
``` commandline
chsh -s /usr/bin/bash
```
After changing of shell either from 'bash' to 'zsh' or viceversa reboot your computer. The shell used in terminal will not be fixed to the one choosen unless you reboot your comupter.
# 20 Running the simulator with autopilot system
Copy the file 'settings.json' located in the path '/car/autopilot' and paste in the path 'airsim'. Make sure to paste the file on the airsim directory created in step 2.
``` commandline
cp ~/Documents/car/autopilot/settings.json ~/AirSim/settings.json
```
Go to the directory 'car/autopilot' and open the file 'config.py'. After opening this file modify the file by changing "self.HIDPI = True" to "self.HIDPI = False".

After run the simulator by going to UE4 and opening the simulator project.
``` commandline
cd UnrealEngine/Engine/Binaries/Linux
./UE4Editor
```
Finally, run the autopilot system by: 
``` commandline
cd Documents/car/autopilot
python3 autopilot.py
```

Now you are ready to start developing a better simulation enviroment which increases the frame speed when running the autopilot system. 
Good luck. You will need it.
