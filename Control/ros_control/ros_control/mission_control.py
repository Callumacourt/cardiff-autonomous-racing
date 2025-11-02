from eufs_msgs.msg import CanState
from MPC.main import Model_Predictive_Control
from model.vehical_model import Vehicle_State
from nav_msgs.msg import Path

class Mission_Control:
    def __init__(self,mpc_unit:Model_Predictive_Control,timer_period:float,logger) -> None:
        self.__static_A_flag = 0#flag that indicates the progress through the static inspection A mission
        self.__static_B_flag = 0#flag that indicates the progress through the static inspection B mission
        self.__autonomous_demo_flag = 0#flag that indicates the progress through the autonomous demonstration mission

        self.__mission_complete = False

        self.__ami_state = CanState.AMI_NOT_SELECTED
        self.__as_state = CanState.AS_OFF

        self.mpc_unit = mpc_unit
        self.timer_period = timer_period

        self.logger = logger
    

    def reset_mission_progress(self):
        self.__static_A_flag = 0
        self.__static_B_flag = 0
        self.__autonomous_demo_flag = 0

    def __acceleration(self,current_state:Vehicle_State,desired_path:Path) -> tuple[float, float]:
        acceleration = 0.0
        steering_angle = 0.0
        # msg.drive.speed=10.0    
        self.logger().info("AS_Driving")

        try:
            commands = self.mpc_unit.main(initial_state=current_state,required_path=desired_path)#get required path from path planning, not sure where to get initial state from
            acceleration = commands.acceleration 
            steering_angle = commands.steering_angle
        except Exception as e:
            if current_state.directional_velocity < 5.0 or current_state.wheels_rpm < 200:
                pass
        acceleration = 1.0 # make sure these are floats
        steering_angle = 0.0
        self.logger().info(f'created accelleration command')
        # msg.drive.steering_angle_velocity
        # msg.drive.jerk
        #self.publisher_.publish(msg)
        #self.logger().info(f'Publishing: "{msg.drive}"')
        #self.logger().info(f'Publishing: "{msg.drive}" \n & {msg.header}')
        return float(acceleration),float(steering_angle)

    def __skidpan(self) -> tuple[float,float]:
        return 0.0,0.0

    def __track_drive(self) -> tuple[float,float]:
        return 0.0,0.0

    def __autocross(self) -> tuple[float,float]:
        return 0.0,0.0

    def __static_A(self,current_state:Vehicle_State) -> tuple[float, float]:
        self.logger().info("AS_Driving")

        acceleration = 0.0
        steering_angle = 0.0
        #steer all the way one way
        if self.__static_A_flag == 0:
            self.logger().info("Sub task: Steer left")

            steering_angle = 0.5
            if current_state.steering_angle_rad >= 0.41:
                self.__static_A_flag = 1
        #steer all the way in the opposite direction
        if self.__static_A_flag == 1:
            self.logger().info("Sub task: Steer right")
            steering_angle = -0.5
            if current_state.steering_angle_rad <=-0.41:
                self.__static_A_flag = 2
        #steering back to centre
        if self.__static_A_flag == 2:
            self.logger().info("Sub task: Steer centre")
            steering_angle = 0.0
            if current_state.steering_angle_rad == 0.0:
                self.__static_A_flag = 3
        #wheels to 200rpm
        if self.__static_A_flag == 3:
            self.logger().info("Sub task: Accelerate to 200rpm")
            self.logger().info(f"Current RPM: {current_state.wheels_rpm}")
            if current_state.wheels_rpm < 200.0:
                acceleration = 2.0
            else:
                self.__static_A_flag = 4
        #stop car
        if self.__static_A_flag == 4:
            self.logger().info("Sub task: Brake to zero")
            self.logger().info(f"Current RPM: {current_state.wheels_rpm}")

            acceleration = -4.0
            if current_state.wheels_rpm <= 0.1:
                self.__static_A_flag = 5
        # set AS_FINISHED
        if self.__static_A_flag == 5 and not self.__mission_complete:
            #set mission complete
            self.__mission_complete = True
            self.__static_A_flag = 0
            #self.logger().info("Mission complete published!")
        
        return float(acceleration), float(steering_angle)

    def __static_B(self,current_state:Vehicle_State) -> tuple[float, float]:
        acceleration = 0.0
        steering_angle = 0.0
        if self.__static_B_flag == 0:
            self.logger().info("Sub task: accelerate to 50rpm")
            if current_state.wheels_rpm < 50.0:
                acceleration = 20.0
            else:
                self.__static_B_flag = 1

        if self.__static_B_flag == 1:
            self.trigger_ebs()
            self.__static_B_flag = 0
        
        return float(acceleration), float(steering_angle)


    def __autonomous_demo(self,current_state:Vehicle_State) -> tuple[float, float]:
        acceleration = 0.0
        steering_angle = 0.0
        #steering left and right and return to straight
        if self.__autonomous_demo_flag == 0:
            self.logger().info("Sub task: steering left")
            steering_angle = 0.5
            if current_state.steering_angle_rad >= 0.41:
                self.__autonomous_demo_flag = 1
        if self.__autonomous_demo_flag == 1:
            self.logger().info("Sub task: steering right")
            steering_angle = -0.5
            if current_state.steering_angle_rad <= -0.41:
                self.__autonomous_demo_flag = 2
        if self.__autonomous_demo_flag == 2:
            self.logger().info("Sub task: Steer centre")
            steering_angle = 0.0
            if current_state.steering_angle_rad == 0.0:
                self.__autonomous_demo_flag = 3
        #accellerate for 10m to at least 15kph
        if self.__autonomous_demo_flag == 3: # THIS DOES NOT CURRENTLY WORK (distance check is always true)
            self.set_time_at_event_start(self.i)
            self.logger().info("Sub task: accelleration for 10m")
            acceleration = 2.0
            #check if 10m have passed using suvat
            if 0.5 * 2.0 * (((self.i-self.time_at_event_start)/self.timer_period)**2) >= 10:
                self.__autonomous_demo_flag = 4
        #stop within a furthur 10m
        if self.__autonomous_demo_flag == 4:
            self.logger().info("Sub task: break to stop")
            acceleration = -2.0
            if current_state.wheels_rpm == 0.0:
                self.__autonomous_demo_flag = 5
                self.time_at_event_start = 0 #ONLY DO THIS IN BITS OF CODE NOT IN A LOOP, otherwise your timer will be continually reset
        #accellerate for a furthur 10m to at least 15kph
        if self.__autonomous_demo_flag == 5:
            self.set_time_at_event_start(self.i)
            self.logger().info("Sub task: Accelerate a further 10m")
            acceleration = 2.0
            #check if 10m have passed using suvat
            if 0.5 * 2.0 * (((self.i-self.time_at_event_start)/self.timer_period)**2) >= 10:
                self.__autonomous_demo_flag = 6
                self.time_at_event_start = 0
        #deploy ebs
        if self.__autonomous_demo_flag == 6:
            self.trigger_ebs()
            self.__autonomous_demo_flag = 0
        
        return float(acceleration),float(steering_angle)

    def set_can_states(self,AMI:CanState.ami_state,AS:CanState.ami_state):
        self.__ami_state = AMI
        self.__as_state = AS

    def get_message(self,current_state:Vehicle_State,desired_path:Path=None) -> tuple[float, float]:
        self.logger().info("Test message A")
        if not self.__mission_complete:
            if self.__ami_state == CanState.AMI_ACCELERATION:
                if self.__as_state == CanState.AS_DRIVING:
                    return self.__acceleration(current_state,desired_path)
            elif self.__ami_state == CanState.AMI_SKIDPAD:
                if self.__as_state == CanState.AS_DRIVING:
                    return self.__skidpan()
            elif self.__ami_state == CanState.AMI_AUTOCROSS:
                if self.__as_state == CanState.AS_DRIVING:
                    return self.__autocross()
            elif self.__ami_state == CanState.AMI_TRACK_DRIVE:
                if self.__as_state == CanState.AS_DRIVING:
                    return self.__track_drive()
            elif self.__ami_state == CanState.AMI_DDT_INSPECTION_A:
                if self.__as_state == CanState.AS_DRIVING:
                    return self.__static_A(current_state)
            elif self.__ami_state == CanState.AMI_DDT_INSPECTION_B:
                if self.__as_state == CanState.AS_DRIVING:
                    return self.__static_B(current_state)
            elif self.__ami_state == CanState.AMI_AUTONOMOUS_DEMO:
                if self.__as_state == CanState.AS_DRIVING:
                    return self.__autonomous_demo(current_state)
            elif self.__ami_state == CanState.AMI_NOT_SELECTED:
                return 0.0,0.0
            
        

        #fallback in case of bad can state
        return 0.0,0.0
    
    def get_mission_complete(self) -> bool:
        return self.__mission_complete


if __name__ == "__main__":
    mission_controler = Mission_Control()
    print(mission_controler.get_message())
