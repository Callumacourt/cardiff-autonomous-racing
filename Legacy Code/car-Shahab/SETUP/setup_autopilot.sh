#!/bin/sh


echo "---"
echo "installing CUDA"
echo "---"
sudo apt install nvidia-cuda-toolkit
echo "---"
echo "installing CUDNN"
echo "---"
tar -xvzf cudnn-10.1-linux-x64-v7.6.4.38.tgz
sudo cp cuda/include/cudnn.h /usr/lib/cuda/include/
sudo cp cuda/lib64/libcudnn* /usr/lib/cuda/lib64/
sudo chmod a+r /usr/lib/cuda/include/cudnn.h /usr/lib/cuda/lib64/libcudnn*
echo 'export LD_LIBRARY_PATH=/usr/lib/cuda/lib64:$/usr/lib/nvidia-cuda-toolkit' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/lib/cuda/include:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc
echo "---"
echo "----Checking if CUDA has been installed properly---"
echo "---"
nvcc -V
echo "---"
echo "----Checking if CUDNN has been installed properly---"
echo "---"
cat /usr/lib/cuda/include/cudnn.h | grep CUDNN_MAJOR -A 2
echo "---"
echo "installing LIBPNG12-0"
sudo apt-get update
sudo apt install libpng12-0
echo "---"
echo "installing PYCUDA"
echo "---"
sudo apt-get install python3-pycuda
pip3 install pycuda
echo "---"
echo "installing BOOST C++"
echo "---"
sudo apt install libboost-dev
sudo apt install libboost-all-dev
pip3 install boost
echo "---"
echo "installing OPENCV"
echo "---"
sudo apt-get install python3-opencv
sudo apt-get install cmake
sudo apt-get install gcc g++
sudo apt-get install python3-dev python3-numpy
sudo apt-get install libavcodec-dev libavformat-dev libswscale-dev
sudo apt-get install libgstreamer-plugins-base1.0-dev libgstreamer1.0-dev
sudo apt-get install libgtk-3-dev
sudo pip3 install opencv-python
echo "---"
echo "installing NEAT"
echo "---"
pip3 install neat
echo "---"
echo "installing NUMPY"
echo "---"
sudo pip3 install numpy
echo "---"
echo "installing MATPLOTLIB"
echo "---"
sudo apt-get install python3-matplotlib
echo "---"
echo "installing SCIPY"
echo "---"
sudo apt-get install python3-scipy
echo "---"
echo "installing OPENGL"
echo "---"
sudo apt-get install python3-opengl
echo "---"
echo "installing FTGL"
echo "---"
sudo apt-get install libftgl2
sudo apt-get install -y libftgl-dev
echo "---¡¡¡READ_THIS!!!---"
echo "Now run the following commands in the terminal (just copy and paste the commands):"
echo "---"
echo "cd .."
echo "cd usr/lib/x86_64-linux-gnu"
echo "sudo ln -s libboost_python38.so libboost_python3.so"
echo "exit"
echo "---"
sudo -i
cd pyftgl
sudo python3 setup.py build
sudo python3 setup.py install
cd ..
echo "---"
echo "installing X-11"
echo "---"
sudo apt-get install xauth
sudo apt-get install xorg
sudo apt-get install openbox
echo "---"
echo "installing PSUTIL"
echo "---"
pip3 install psutil
echo "---"
echo "installing WXPYTHON"
echo "---"
sudo apt install python3-pip make gcc libgtk-3-dev libgstreamer-gl1.0-0 freeglut3 freeglut3-dev python3-gst-1.0 libglib2.0-dev ubuntu-restricted-extras libgstreamer-plugins-base1.0-dev
sudo apt-get install python3-wxgtk4.0
pip3 install --user wxPython

#this path can or should be modified depending on where the repositories are located
cd ..
cd ~/Documents/car/autopilot

echo "---"
echo "installing LINE PROFILER"
echo "---"
pip3 install line_profiler
echo "---"
echo "installing AIRSIM"
echo "---"
pip3 install msgpack-rpc-python
pip3 install airsim
echo "---"
echo "BUILDING AP"
echo "---"
cd ap
sudo python3 setup.py build
cd ..
ln -s ap/build/lib.linux-86_64-3.8/ap.cpython-38-x86_64-linux-gnu.so
echo "---"
echo "REBOOT YOUR SYSTEM BEFORE USING IT"
echo "---"
echo "CONGRATULATIONS"
echo "Now you are ready to start developing on the autopilot system."
echo "---"
echo "---"
echo "If you have a problem with ap running the 'autopilot.py' script then delete the 'ap.cpython-38-x86_64-linux-gnu.so' copied script from the autopilot folder and manually copy and paste it to the autopilot folder. This script is found in the following path '~/car/autopilot/ap/build/lib.linux-86_3.8'. This will fix the issue"
