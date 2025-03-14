# Path Planning Section

## Description
This section of the codebase is the path planning algorithm that uses the RRT* approach to generate an optimised path for an autonomous vehicle. This will interpret data from the perception team, process a path and send it to the control team.

## Project Structure
Here is the structure of the project:
 - **main.py** - The main file which runs the project and links all the parts of the project.
 - **dummyInputs.py** - This generates the initial dummy data that we needed before we had the outputs from perception.
 - **inputs.txt** - This file stores the input data that the algorithm needs to run.
 - **rrt(star).py** - This code contains the RRT* algorithm that we are using to generate the path.
 - **gui.py** - This code generates the GUI allowing for easy visualisation of the path.

**Follow the structure of this repository as it is fundamental for it to work.**


## Getting started

Libraries that need to be installed:
- numpy
- matplotlib
- pygame

**If you are on university computers, you can install these libraries using pip to avoid the admin username and password.**

**For example: pip install whatever_library_you_need**

When starting the project, **run dummyInputs.py** to generate a basic 3D-array in the **inputs.txt file**.
This array represents a racetrack that has a basic curve - this data is formatted:
 **Index	Close Left (x,y,z)	Close Right (x,y,z)	Far Left (x,y,z)	Far Right (x,y,z)** 

This will then allow you to run the main.py file which will generate the path and display it in a GUI.

## Visuals

## How the Code works

## Usage

## FAQ

## Support

If there is something wrong with the code or you need help, please reach out to the **Path Planning Team Leader, Dominick George**. I would be happy to help you. My email is **GeorgeD8@cardiff.ac.uk**.

## Contributors

- Dominick George
- Harley Doe
- Thomas Brown
- Timothee Lux
- Callum A'court
- Alexander Stephens
- Shaina Ashok Patel
- Romilly Nash