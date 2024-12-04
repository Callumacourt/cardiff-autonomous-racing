# Simulator getting started

Here you will find some basic documentation on getting started with the simulator. If you happen to find a mistake or wish to add new information then please edit this document.

The simulator is a 2D environment witch models a car and a track. It is built to run with Python 3 and is known to run on Python 3.6 and 3.7. Please make sure you setup and run the environment with Python 3.

### Setup

#### 1. Install the following

**Python packages**

* [wxPython](https://wiki.wxpython.org/How%20to%20install%20wxPython) - Depending on your operation you may need to build from source (see their documentation for more)
* pyopengl
* [MultiNEAT](https://github.com/peter-ch/MultiNEAT) - You will need to build this from source
* neat
* numpy

**Other programs and tools**

* X11 - Window system (possibly just needed on Linux?)

#### 2. Last bits

Set the environmental `export GDK_BACKEND=x11`.
To run the simulation you will want to be located in the simulator directory where you can and enter the command `python ./play.py`.

Train an agent with neat: `python ./train_multineat.py`

Get help: `python ./play.py -h`

### Issues

Bellow you will find solutions to a few issues you may run into.

###### **Segmentation fault (core dumped)**
* re-build ftgl and / or simgeom and add the built files into the simulator directory. A readme on how to do this can be found in the folder ftgl. **DO NOT** commit the new binary files to the repo.

###### **received signal SIGSEGV, Segmentation fault. 0x00007fffe807aad8 in _XGetRequest () from /lib64/libX11.so.6**
* run the command `export GDK_BACKEND=x11`
