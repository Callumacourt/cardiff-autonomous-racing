# Vehicle Commands Stamped message for EUFS
std_msgs/Header header

# Control commands sent to vehicle
float64 steering_angle_deg    # Steering angle in degrees
float64 torque_request       # Torque request in Nm
float64 brake_request        # Brake request (0-100%)
float64 rpm_request          # RPM request

# Mission control
bool mission_finished       # Mission completion flag
bool driving_flag           # Ready to drive flag

# Emergency controls
bool emergency_stop
bool ebs_request
string control_mode
