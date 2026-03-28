from time import time, sleep
import numpy as np


WHEEL_RADIUS = 0.253


class Timestep:
    def __init__(self, length, expected_acceleration, initial_rpm):
        """
        Parameters
        -
        length: float, this is the time in seconds between the start of the timestep and the end of the timestep - this should be the same as for the MPC algorithm. I think?
        
        expected_acceleration: float, this is the acceleration in m/s^2 we want the car to do for this timestep
        
        initial_rpm: float, this is the RPM of the wheel when the timestep begins
        """
        self._length = length
        self._expected_acceleration = expected_acceleration
        self._initial_rpm = initial_rpm
        self._expected_final_rpm = self._calculate_expected_rpm()
        self._initial_time = time()
        self._final_time = self._initial_time + self._length

    def _calculate_expected_rpm(self):
        # convert RPM to velocity (m/s)
        u = self._initial_rpm * 2 * np.pi * WHEEL_RADIUS / 60

        # apply acceleration (currently assumes infinite grip, and no delay between sending a command and the motor implementing it)
        v = u + self._expected_acceleration * self._length # v = u + at

        # convert velocity back to RPM
        return v * 60 / (2 * np.pi * WHEEL_RADIUS)
    
    # just getters, none of the attributes should change once a timestep has begun
    def get_expected_acceleration(self):
        return self._expected_acceleration
    def get_initial_rpm(self):
        return self._initial_rpm
    def get_expected_final_rpm(self):
        return self._expected_final_rpm
    def get_initial_time(self):
        return self._initial_time
    def get_final_time(self):
        return self._final_time



class Symmetric_Wheelslip_Detector:
    def __init__(self, timestep_size=0.05):
        self.timestep_size = timestep_size
    
    def start_timestep(self, expected_acceleration, initial_rpm):
        self._current_timestep = Timestep(length=self.timestep_size, expected_acceleration=expected_acceleration, initial_rpm=initial_rpm)
    
    def _calculate_experienced_acceleration(self, current_rpm):
        """
        Should this calculate experienced acceleration from the initial to current or from previous to current?
        """
        initial_time = self._current_timestep.get_initial_time()
        delta_t = time() - initial_time
        u = self._current_timestep.get_initial_rpm() * 2 * np.pi * WHEEL_RADIUS / 60
        v = current_rpm * 2 * np.pi * WHEEL_RADIUS / 60

        return (v - u) / delta_t

    def check_for_wheelslip(self, current_rpm):
        """
        Parameters
        -
        current_rpm

        Returns
        -
        mask - a value between 0 and 1, showing how much to scale the acceleration by to avoid wheelslip
        """
        current_time = time()
        if current_time > self._current_timestep.get_final_time():
            print(f"WARNING, wheelslip timestep is {current_time - self._current_timestep.get_final_time()} seconds out of date! Unexpected TC/ABS may occur!")
        
        experienced_acceleration = self._calculate_experienced_acceleration(current_rpm)
        # if expected acceleration < 0, then car is breaking, check if rpm is too low
        if self._current_timestep.get_expected_acceleration() < 0:
            # if experienced > expected, then the wheels have not locked, so all is fine
            if experienced_acceleration > self._current_timestep.get_expected_acceleration():
                mask =  1
            else:
                mask = self._current_timestep.get_expected_acceleration() / experienced_acceleration

        # if expected acceleration > 0, then car is accelerating, check if rpm is too high
        elif self._current_timestep.get_expected_acceleration() > 0:
            # if actual acceleration is < expected, then all is fine, keep going
            if experienced_acceleration < self._current_timestep.get_expected_acceleration():
                mask = 1
            else:
                # return the ratio between expected and experienced. This way experienced * ratio = expected
                mask = self._current_timestep.get_expected_acceleration() / experienced_acceleration
            
        # if expected acceleration == 0, then car is coasting, nothing should change?
        else:
            mask = 1


        # used absolute value, in case expected > 0 and experienced < 0, which might happen soon after an acceleration command is given, if the car was slowing down previously?
        return abs(mask) 
        


if __name__ == "__main__":
    t = 0.05 # the time in seconds between mpc predictions

    ws_det = Symmetric_Wheelslip_Detector(timestep_size=t)

    current_rpm = 50.0 # the rpm of the car's wheel (modeling the car as only having a single wheel for now)

    desired_acceleration = 1.0 # the acceleration in ms^-2 for the car to achieve over the next time step

    # set predicted rpm after acceleration for t seconds
    ws_det.start_timestep(expected_acceleration=desired_acceleration, initial_rpm=current_rpm)

    mini_steps = 20

    future_rpms = [current_rpm + x*0.15 for x in range(mini_steps)]
    # wait t seconds
    for i in range(0, mini_steps):
        sleep(t/mini_steps)
        print(future_rpms[i], ws_det.check_for_wheelslip(future_rpms[i]))

    # check what acceleration was achieved


    """
    Thought: if the expected acceleration is higher than the car can handle, 
    wont the RPMs still match the expected values, since the motor will just do what is necessary to get there?
    Or, since the motors work via torque requests will the motors always overshoot the rpm we want if the wheels start spinning?
    I don't know enough about torque to tell.

    This is the data we send TO the car, if this helps:
    ai2vcu_data_.AI2VCU_ESTOP_REQUEST = ebs_state_;
    ai2vcu_data_.AI2VCU_BRAKE_PRESS_REQUEST_pct = braking_;
    ai2vcu_data_.AI2VCU_AXLE_TORQUE_REQUEST_Nm = torque_;
    ai2vcu_data_.AI2VCU_STEER_ANGLE_REQUEST_deg = steering_;
    ai2vcu_data_.AI2VCU_AXLE_SPEED_REQUEST_rpm = rpm_request_;

    Btw, rpm_request is always the rpm limit, whenever acceleration > 0, otherwise it is 0. 

    """