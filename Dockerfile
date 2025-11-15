FROM osrf/ros:humble-desktop-full
SHELL ["/bin/bash", "-c"]

RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-colcon-common-extensions \
    python3-rosdep \
    git \
    wget \
    cmake \
    build-essential \
    libeigen3-dev \
    libopencv-dev \
    python3-opencv \
    libsuitesparse-dev \
    libatlas-base-dev \
    libgoogle-glog-dev

# Copy test data
COPY test_data/ /workspace/test_data/
COPY Control/ /workspace/Control/
COPY Path_Planning/ /workspace/Path_Planning/
COPY perception_ws/ /workspace/perception_ws/

COPY requirements.txt /workspace/requirements.txt
WORKDIR /workspace
RUN pip3 install -r requirements.txt

#build control
WORKDIR /workspace/Control
RUN rm -rf eufs_msgs
RUN mkdir eufs
WORKDIR /workspace/Control/eufs
#get eufs stuff
RUN git clone https://gitlab.com/eufs/eufs_msgs.git
RUN echo 'export EUFS_MASTER=/workspace/Control/eufs' >> ~/.bashrc
RUN source ~/.bashrc
#rosdep
RUN rosdep init || true
RUN rosdep update
RUN rosdep install --from-paths $EUFS_MASTER --ignore-src -r -y

RUN colcon build
RUN . install/setup.bash

#build path planning

#build perception

# Default command
CMD ["bash"]