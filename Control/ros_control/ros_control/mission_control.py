from eufs_msgs.msg import CanState
from MPC.main import Model_Predictive_Control
from model.vehical_model import Vehicle_State
from nav_msgs.msg import Path
from mission_flag_enums import *
import math

class Mission_Control:
    def __init__(self,mpc_unit:Model_Predictive_Control,timer_period:float,logger,trigger_ebs) -> None:
        self.__static_A_flag = AFlag.LEFT#flag that indicates the progress through the static inspection A mission
        self.__static_B_flag = BFlag.ACCELERATE#flag that indicates the progress through the static inspection B mission
        self.__autonomous_demo_flag = demoFlag.LEFT#flag that indicates the progress through the autonomous demonstration mission
        self.__skidpan_flag = SkidpanFlag.StraightToTimekeepingLine # flag that indicates the progress through the skipan mission

        self.__accelFlag = accelFlag.ACCELERATE#Flag that indicates the progress through the accelleration mission
        self.__autocrossFlag = autocrossFlag.START#Flag that indicates the progress through the autocross mission
        self.__mission_complete = False

        self.__ami_state = CanState.AMI_NOT_SELECTED
        self.__as_state = CanState.AS_OFF

        self.mpc_unit = mpc_unit
        self.timer_period = timer_period

        self.logger = logger#ros2 logger passed through from cmd node
        self.trigger_ebs = trigger_ebs# trigger ebs function passed through from cmd node

        self.i = 0
        self.time_at_event_start = 0
    

    def reset_mission_progress(self):
        self.__static_A_flag = AFlag.LEFT
        self.__static_B_flag = BFlag.ACCELERATE
        self.__autonomous_demo_flag = demoFlag.LEFT
        self.__skidpan_flag = SkidpanFlag.StraightToTimekeepingLine
        self.__accelFlag = accelFlag.ACCELERATE
        self.__autocrossFlag = autocrossFlag.START

    def __acceleration(self,current_state:Vehicle_State,desired_path:Path) -> tuple[float, float]:
        acceleration = 0.0
        steering_angle = 0.0
        # msg.drive.speed=10.0    
        self.logger().info("AS_Driving")
        # accelerate along path
        if self.__accelFlag == accelFlag.ACCELERATE:
            self.logger().info("Sub task: Accelerate")
            distance_travelled = math.sqrt(current_state.xpos**2 + current_state.ypos**2) #distance to origin (0,0)
            if distance_travelled < 75:
                try:
                    commands = self.mpc_unit.main(initial_state=current_state,required_path=desired_path)#get required path from path planning, not sure where to get initial state from
                    acceleration = commands.acceleration 
                    steering_angle = commands.steering_angle
                except Exception as e:
                    acceleration = 0.0
                    steering_angle = 0.0
            else:
                self.__accelFlag = accelFlag.BRAKE
        #Brake after 75m travelled 
        if self.__accelFlag == accelFlag.BRAKE: 
            self.logger().info("Sub task: Brake")
            try:
                commands = self.mpc_unit.main(initial_state=current_state,required_path=desired_path)#let mpc brake and make any steering adjustments needed
                #cost function will need to now reward braking and massivly penalise accelerating or high speeds
                acceleration = commands.acceleration 
                steering_angle = commands.steering_angle
            except Exception as e:
                acceleration = -3.0 #might need to be increased
                steering_angle = 0.0

            if current_state.wheels_rpm <= 0.1:
                self.__accelFlag = accelFlag.COMPLETE

        if self.__accelFlag == accelFlag.COMPLETE and not self.__mission_complete:
            #set mission complete
            self.__mission_complete = True
            self.__accelFlag = accelFlag.ACCELERATE
            #self.logger().info("Mission complete published!")

        # try:
        #     commands = self.mpc_unit.main(initial_state=current_state,required_path=desired_path)#get required path from path planning, not sure where to get initial state from
        #     acceleration = commands.acceleration 
        #     steering_angle = commands.steering_angle
        # except Exception as e:
        #     if current_state.directional_velocity < 5.0 or current_state.wheels_rpm < 200:
        #         pass
        
        # acceleration = 1.0 # make sure these are floats
        # steering_angle = 0.0
        # self.logger().info(f'created accelleration command')
        # # msg.drive.steering_angle_velocity
        # # msg.drive.jerk
        # #self.publisher_.publish(msg)
        # #self.logger().info(f'Publishing: "{msg.drive}"')
        # #self.logger().info(f'Publishing: "{msg.drive}" \n & {msg.header}')
        return float(acceleration),float(steering_angle)

    def __skidpan(self, current_state:Vehicle_State, desiredPath:Path) -> tuple[float,float]:

        self.logger().info("AS_Skidpan")

        acceleration = 0.0
        steering_angle = 0.0

        if self.__skidpan_flag == SkidpanFlag.StraightToTimekeepingLine:
            # go straight until line crossed
            acceleration = 2.0
            # if line crossed
                #self.__skidpan_flag = SkidpanFlag.Right
        if self.__skidpan_flag == SkidpanFlag.Right:
            pass
            # go around the right loop twice

            # if line crossed twice
                #self.__skidpan_flag = SkidpanFlag.Left
        if self.__skidpan_flag == SkidpanFlag.Left:
            pass
            # go around the left loop twice

            # if timing line crossed twice
                #self.__skidpan_flag = SkidpanFlag.StopInZone
        if self.__skidpan_flag == SkidpanFlag.StopInZone:
            # stop the car in the finish zone

            # rn just slow car down with -acc, in the future have a cost function specifically for stopping at a point
            acceleration = -5

            if current_state.wheels_rpm < 0.1 and not self.__mission_complete:
                self.__mission_complete = True


        return acceleration, steering_angle

    def __track_drive(self) -> tuple[float,float]:
        return 0.0,0.0

    def __autocross(self, current_state:Vehicle_State, desired_path:Path) -> tuple[float,float]:
        acceleration = 0.0
        steering_angle = 0.0
        self.logger().info("AS_Driving")
        #accelerate to start line
        if self.__autocrossFlag == autocrossFlag.START:
            self.logger().info("Sub task: START")
            #go straight until start line crossed

            #if line crossed
            #    self.__autocrossFlag = autocrossFlag.LAP
        
        if self.__autocrossFlag == autocrossFlag.LAP:
            self.logger().info("Sub task: LAP")
            #follow path using MPC inputs

            #if finish line crossed
            #    self.__autocrossFlag = autocrossFlag.BRAKE
            
        if self.__autocrossFlag == autocrossFlag.BRAKE:
            self.logger().info("Sub task: BRAKE")
            #Brake until stopped

            if current_state.wheels_rpm <= 0.1:
                self.__autocrossFlag = autocrossFlag.COMPLETE

        if self.__autocrossFlag == autocrossFlag.COMPLETE:
            #set mission complete
            self.__mission_complete = True
            self.__autocrossFlag = autocrossFlag.START


        return acceleration, steering_angle

    def __static_A(self,current_state:Vehicle_State) -> tuple[float, float]:
        self.logger().info("AS_Driving")

        acceleration = 0.0
        steering_angle = 0.0
        #steer all the way one way
        if self.__static_A_flag == AFlag.LEFT:
            self.logger().info("Sub task: Steer left")

            steering_angle = 0.5
            if current_state.steering_angle_rad >= 0.41:
                self.__static_A_flag = AFlag.RIGHT
        #steer all the way in the opposite direction
        if self.__static_A_flag == AFlag.RIGHT:
            self.logger().info("Sub task: Steer right")
            steering_angle = -0.5
            if current_state.steering_angle_rad <=-0.41:
                self.__static_A_flag = AFlag.CENTRE
        #steering back to centre
        if self.__static_A_flag == AFlag.CENTRE:
            self.logger().info("Sub task: Steer centre")
            steering_angle = 0.0
            if abs(current_state.steering_angle_rad) <= 0.01:
                self.__static_A_flag = AFlag.ACCELERATE
        #wheels to 200rpm
        if self.__static_A_flag == AFlag.ACCELERATE:
            self.logger().info("Sub task: Accelerate to 200rpm")
            self.logger().info(f"Current RPM: {current_state.wheels_rpm}")
            if current_state.wheels_rpm < 200.0:
                acceleration = 2.0
            else:
                self.__static_A_flag = AFlag.BRAKE
        #stop car
        if self.__static_A_flag == AFlag.BRAKE:
            self.logger().info("Sub task: Brake to zero")
            self.logger().info(f"Current RPM: {current_state.wheels_rpm}")

            acceleration = -4.0
            if current_state.wheels_rpm <= 0.1:
                self.__static_A_flag = AFlag.COMPLETE
        # set AS_FINISHED
        if self.__static_A_flag == AFlag.COMPLETE and not self.__mission_complete:
            #set mission complete
            self.__mission_complete = True
            self.__static_A_flag = AFlag.LEFT
            #self.logger().info("Mission complete published!")
        
        return float(acceleration), float(steering_angle)

    def __static_B(self,current_state:Vehicle_State) -> tuple[float, float]:
        acceleration = 0.0
        steering_angle = 0.0
        if self.__static_B_flag == BFlag.ACCELERATE:
            self.logger().info("Sub task: accelerate to 50rpm")
            if current_state.wheels_rpm < 50.0:
                acceleration = 20.0
            else:
                self.__static_B_flag = BFlag.EMGCBRAKE

        if self.__static_B_flag == BFlag.EMGCBRAKE:
            self.trigger_ebs()
            self.__static_B_flag = BFlag.ACCELERATE
        
        return float(acceleration), float(steering_angle)


    def __autonomous_demo(self,current_state:Vehicle_State) -> tuple[float, float]:
        acceleration = 0.0
        steering_angle = 0.0
        #steering left and right and return to straight
        if self.__autonomous_demo_flag == demoFlag.LEFT:
            self.logger().info("Sub task: steering left")
            steering_angle = 0.5
            if current_state.steering_angle_rad >= 0.41:
                self.__autonomous_demo_flag = demoFlag.RIGHT
        if self.__autonomous_demo_flag == demoFlag.RIGHT:
            self.logger().info("Sub task: steering right")
            steering_angle = -0.5
            if current_state.steering_angle_rad <= -0.41:
                self.__autonomous_demo_flag = demoFlag.CENTRE
        if self.__autonomous_demo_flag == demoFlag.CENTRE:
            self.logger().info("Sub task: Steer centre")
            steering_angle = 0.0
            if abs(current_state.steering_angle_rad) <= 0.01:
                self.__autonomous_demo_flag = demoFlag.ACCELERATE
        #accellerate for 10m to at least 15kph
        if self.__autonomous_demo_flag == demoFlag.ACCELERATE: # THIS DOES NOT CURRENTLY WORK (distance check is always true)
            self.set_time_at_event_start(self.i)
            self.logger().info("Sub task: accelleration for 10m")
            acceleration = 2.0
            #check if 10m have passed using suvat
            if 0.5 * 2.0 * (((self.i-self.time_at_event_start)/self.timer_period)**2) >= 10:
                self.__autonomous_demo_flag = demoFlag.BRAKE
        #stop within a furthur 10m
        if self.__autonomous_demo_flag == demoFlag.BRAKE:
            self.logger().info("Sub task: break to stop")
            acceleration = -2.0
            if current_state.wheels_rpm == 0.0:
                self.__autonomous_demo_flag = demoFlag.REPEAT
                self.time_at_event_start = 0 #ONLY DO THIS IN BITS OF CODE NOT IN A LOOP, otherwise your timer will be continually reset
        #accellerate for a furthur 10m to at least 15kph
        if self.__autonomous_demo_flag == demoFlag.REPEAT:
            self.set_time_at_event_start(self.i)
            self.logger().info("Sub task: Accelerate a further 10m")
            acceleration = 2.0
            #check if 10m have passed using suvat
            if 0.5 * 2.0 * (((self.i-self.time_at_event_start)/self.timer_period)**2) >= 10:
                self.__autonomous_demo_flag = demoFlag.EMGCBRAKE
                self.time_at_event_start = 0
        #deploy ebs
        if self.__autonomous_demo_flag == demoFlag.EMGCBRAKE:
            self.trigger_ebs()
            self.__autonomous_demo_flag = demoFlag.LEFT
        
        return float(acceleration),float(steering_angle)

    def set_can_states(self,AMI:CanState.ami_state,AS:CanState.ami_state):
        self.__ami_state = AMI
        self.__as_state = AS

    def get_message(self,current_state:Vehicle_State,desired_path:Path=None) -> tuple[float, float]:
        self.i+=1

        if not self.__mission_complete:
            if self.__ami_state == CanState.AMI_ACCELERATION:
                if self.__as_state == CanState.AS_DRIVING:
                    return self.__acceleration(current_state,desired_path)
            elif self.__ami_state == CanState.AMI_SKIDPAD:
                if self.__as_state == CanState.AS_DRIVING:
                    return self.__skidpan(current_state=current_state, desiredPath=desired_path)
            elif self.__ami_state == CanState.AMI_AUTOCROSS:
                if self.__as_state == CanState.AS_DRIVING:
                    return self.__autocross(current_state=current_state, desired_path=desired_path)
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

    def set_time_at_event_start(self,time):
        if self.time_at_event_start == 0:
            self.time_at_event_start = time

if __name__ == "__main__":
    mission_controler = Mission_Control()
    print(mission_controler.get_message())
