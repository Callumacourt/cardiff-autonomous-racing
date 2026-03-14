from enum import Enum

class AFlag(Enum):
    """
    Represents the current progress of the static inspection A mission
    and what the vehicle's current objective is.
    """
    LEFT = 0 #Turn Steering all the way to the left
    RIGHT = 1
    CENTRE = 2 #Centre the steering wheel
    ACCELERATE = 3 #Accelerate to 200rpm
    BRAKE = 4 #Brake to complete stop
    COMPLETE = 5 #Mission A has been complete

class BFlag(Enum):
    """
    Represents the current progress of the static inspection B mission
    and what the vehicle's current objective is. 
    """
    ACCELERATE = 0 #Accelerate to 50rpm
    EMGCBRAKE = 1 #Activate emergency brake

class demoFlag(Enum):
    """
    Represents the current progress of the autonomous demonstration
    mission and what the vehicle's current objective is. 
    """
    LEFT = 0 #Turn Steering all the way to the left
    RIGHT = 1
    CENTRE = 2 #Centre the steering wheel
    ACCELERATE = 3 #Accelerate for 10m
    BRAKE = 4 #Brake to complete stop
    REPEAT = 5 #Accelerate for another 10m
    EMGCBRAKE = 6 #Activate emergency brake

class accelFlag(Enum):
    """
    Represents the current progress of the Accelleration
    mission and what the vehicle's current objective is. 
    """
    ACCELERATE = 0
    BRAKE = 1
    COMPLETE = 2