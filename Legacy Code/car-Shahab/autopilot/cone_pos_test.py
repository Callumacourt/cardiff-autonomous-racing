import airsim
import cv2
import numpy as np
import os
import setup_path 
import time

# connect to the AirSim simulator 
client = airsim.CarClient()
client.confirmConnection()
client.enableApiControl(True)
car_controls = airsim.CarControls()

"""
The spine name changes for each level I find the fastest way to find it is to 
play the simulator and drive the car into a cone. At the left of the screen you'll see
'Collision#46 with spline_cones_best_200 - ObjID -1'. The name is just the spline_cones_cones_best_200 
bit however the number can change depending the level.
"""

SPLINE_NAME = 'spline_cones_best_1180'

meshes = client.simGetMeshPositionVertexBuffers()

cone_positions = []
for mesh in meshes:
	if mesh.name == SPLINE_NAME:
		print(mesh.position.x_val, mesh.position.y_val, mesh.position.z_val)
	
	
#restore to original state
#client.reset()

client.enableApiControl(False)


            
