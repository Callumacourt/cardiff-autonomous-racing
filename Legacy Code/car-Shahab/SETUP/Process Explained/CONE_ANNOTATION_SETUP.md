This guide explains how to install and run the cone annotation tool.

## 1. Download repositories needed
Download the car and car_data repositories:
``` commandline
cd Documents
git clone https://github.com/Cardiff-Autonomous-Racing/car.git
git clone https://github.com/Cardiff-Autonomous-Racing/car_data.git
```
The toolkits needed to run this program are also downloaded in the toolkits needed for making the autopilot system work. So make sure to follow from step 3 to 16 from the document 'SIMULATOR_SETUP.md'.
## 2. run the cone annotation tool
To open the tool follow this commands
``` commandline
cd Documents/car/cones/cone_tool
python3 cone_tool.py
```

Now you are ready to but the corresponding colored boxes to the matching colored cones. Please annotate as much as you can as you would be helping the training of the cone detection neural network.
