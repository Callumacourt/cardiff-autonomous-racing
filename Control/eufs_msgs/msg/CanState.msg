# CAN State message for EUFS
std_msgs/Header header

# AS (Autonomous System) State  
uint8 AS_OFF = 0
uint8 AS_READY = 1
uint8 AS_DRIVING = 2
uint8 AS_EMERGENCY_BRAKE = 3
uint8 AS_FINISHED = 4
uint8 as_state

# AMI (Autonomous Mission Indicator) State
uint8 AMI_NOT_SELECTED = 0
uint8 AMI_ACCELERATION = 1
uint8 AMI_SKIDPAD = 2
uint8 AMI_AUTOCROSS = 3
uint8 AMI_TRACK_DRIVE = 4
uint8 AMI_EBS_TEST = 5
uint8 AMI_INSPECTION = 6
uint8 AMI_MANUAL_DRIVING = 7
uint8 ami_state

# Mission Status
uint8 MISSION_NOT_SELECTED = 0
uint8 MISSION_SELECTED = 1
uint8 MISSION_RUNNING = 2
uint8 MISSION_FINISHED = 3
uint8 mission_status

# EBS (Emergency Brake System) State
bool ebs_state

# Additional CAN state info
bool can_active
int32 error_count
string status
