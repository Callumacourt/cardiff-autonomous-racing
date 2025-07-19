# Wheel Speeds Stamped message for EUFS
std_msgs/Header header

# Individual wheel speeds in m/s
float64 front_left_speed
float64 front_right_speed
float64 rear_left_speed
float64 rear_right_speed

# Steering angle feedback in degrees
float64 steering_angle

# Speed calculation info
float64 speed_fl  # Front left wheel speed
float64 speed_fr  # Front right wheel speed  
float64 speed_rl  # Rear left wheel speed
float64 speed_rr  # Rear right wheel speed
string speed_units
bool is_valid
