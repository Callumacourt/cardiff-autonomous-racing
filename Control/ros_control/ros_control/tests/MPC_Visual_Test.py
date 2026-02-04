"""
Some tests for the control team's MPC algorithm

This requires ros2 humble to be installed on your system in order to work

matplotlib graphs will be stored in test_plots/

run with pytest MPC_Visual_Test.py -v
"""

import os, sys, pytest, pathlib

import matplotlib.pyplot as plt


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from MPC.main import Model_Predictive_Control
from model.vehical_model import Dynamics_Model, Vehicle_Constants, Vehicle_Input, Vehicle_State
from nav_msgs.msg import Path
from geometry_msgs.msg import PoseStamped,Pose
from std_msgs.msg import Header

def convertListToPath(pointsList:list[tuple[float,float]]) -> Path:
    poseList = []
    for point in pointsList:
        pose = PoseStamped()
        pose.pose.position.x = float(point[0])
        pose.pose.position.y = float(point[1])
        pose.pose.position.z = 0.0
        poseList.append(pose)
    
    path = Path()
    path.poses = poseList
    path.header = Header()
    return path

def convertStatesToList(states:list[Vehicle_State]) -> list[float]:
    points = []
    for state in states:
        point = (state.xpos, state.ypos)
        points.append(point)

    return points

def isPathGoodEnough(desiredPath, predictedPath) -> bool:
    return False

path_straight = [(0,0),(1,0),(2,0),(3,0),(4,0),(5,0),(6,0),(7,0),(8,0),(9,0)]
#path_straight = [(0,0),(0,1),(0,2),(0,3),(0,4),(0,5),(0,6),(0,7),(0,8),(0,9)]
path_slight_bend_left = []
path_slight_bend_right = []
path_hard_bend_left = []
path_hard_bend_right = []
path_hairpin_left = []
path_hairpin_right = []
path_chicane_left = []
path_chicane_right = []

mpc_timestep = 0.5

mpc = Model_Predictive_Control(mpc_timestep)

@pytest.fixture
def save_plot():
    """Fixture that returns a function to save plots with auto-naming"""
    plot_dir = pathlib.Path("test_plots")
    plot_dir.mkdir(exist_ok=True)
    
    def _save(desiredPath, predictedPath, name:str):

        desired_x = [v[0] for v in desiredPath]
        desired_y = [v[1] for v in desiredPath]

        predicted_x = [v[0] for v in predictedPath]
        predicted_y = [v[1] for v in predictedPath]

        max_coord = max(max(max(desired_x),max(desired_y)),max(max(predicted_x),max(predicted_y)))
        min_coord = min(min(min(desired_x),min(desired_y)),min(min(predicted_x),min(predicted_y)))


        fig, ax = plt.subplots()
        # plot the 2 lines
        ax.plot(desired_x,desired_y, "o-", label="Desired")
        ax.plot(predicted_x,predicted_y, "o-", label="Predicted")

        #highlight beginning and end
        ax.plot(desired_x[0], desired_y[0], 'go', markersize=12, label="Start")
        ax.plot(desired_x[-1], desired_y[-1], 'ro', markersize=12, label="End")

        ax.plot(predicted_x[0], predicted_y[0], 'go', markersize=12)
        ax.plot(predicted_x[-1], predicted_y[-1], 'ro', markersize=12)

        ax.set_title(name)
        ax.set_xlim(min_coord-1, max_coord+1)
        ax.set_ylim(min_coord-1, max_coord+1)
        ax.legend()

        filepath = plot_dir / f"{name.replace(" ","_")}.png"
        fig.savefig(filepath, dpi=100, bbox_inches='tight')
        plt.close(fig)
        print(f"\nPlot saved: {filepath}")
    
    return _save

class TestMPCFromStationaryAnd0_0:
    """Tests the MPC algorithm, when the car starts at 0rpm and from 0,0"""

    def test_straight_line(self,save_plot):
        """Test if MPC algorithm works with a straight line (like in the acceleration mission)"""

        #TEMPORARY
        #predictedPath = [(1,0),(2,1),(3,2),(4,3),(4,4),(3,5),(2,6),(1,7),(1,8),(1,9)]

        initial_state = Vehicle_State(x_pos=0,y_pos=0,x_speed=0,y_speed=0,yaw_angle=0,yaw_rate=0,wheel_rpm=0,steering_angle_rad=0)

        # get the inputs the MPC algorithm produces
        predictedInputs = mpc.main(initial_state,
                                   convertListToPath(path_straight),
                                   [Vehicle_Input(1,0) for x in range(10)]
                                   )
        
        # convert those inputs into points for a comparison
        predictedStates = mpc.forward_simulation(initial_state, predictedInputs)

        # convert states into points
        predictedPath = convertStatesToList(predictedStates)
        print(f"path: {predictedPath}")
        print(f"States: {[(state.directional_velocity,state.steering_angle_rad) for state in predictedStates]}")
        print(f"inputs: {[(inp.acceleration,inp.steering_angle) for inp in predictedInputs]}")
        
        save_plot(path_straight, predictedPath, "Straight line")

        assert isPathGoodEnough(path_straight, predictedPath)

        
    
    def test_slight_bend_left(self):
        """Test if the MPC algorithm works with a slight bend to the left"""
        assert isPathGoodEnough(path_slight_bend_left, predictedPath)

    def test_slight_bend_right(self):
        """Test if the MPC algorithm works with a slight bend to the right"""
        assert isPathGoodEnough(path_slight_bend_right, predictedPath)

    def test_hard_bend_left(self):
        """Test if the MPC algorithm works with a hard bend to the left"""
        assert isPathGoodEnough(path_hard_bend_left, predictedPath)

    def test_hard_bend_right(self):
        """Test if the MPC algorithm works with a hard bend to the right"""
        assert isPathGoodEnough(path_hard_bend_right, predictedPath)

    def test_hairpin_left(self):
        """Test if the MPC algorithm works with a hairpin left"""
        assert isPathGoodEnough(path_hairpin_left, predictedPath)

    def test_hairpin_right(self):
        """Test if the MPC algorithm works with a hairpin right"""
        assert isPathGoodEnough(path_hairpin_right, predictedPath)

    def test_chicane_left(self):
        """Test if the MPC algorithm works with a left-right chicane"""
        assert isPathGoodEnough(path_chicane_left, predictedPath)

    def test_chicane_right(self):
        """Test if the MPC algorithm works with a right-left chicane"""
        assert isPathGoodEnough(path_chicane_right, predictedPath)

class TestMPCAtSpeedAnd0_0:
    """Tests the MPC algorithm when the car is at speed, and located at 0,0"""

    def test_straight_line(self):
        """Test if MPC algorithm works with a straight line (like in the acceleration mission)"""
        assert isPathGoodEnough(path_straight, predictedPath)
    
    def test_slight_bend_left(self):
        """Test if the MPC algorithm works with a slight bend to the left"""
        assert isPathGoodEnough(path_slight_bend_left, predictedPath)

    def test_slight_bend_right(self):
        """Test if the MPC algorithm works with a slight bend to the right"""
        assert isPathGoodEnough(path_slight_bend_right, predictedPath)

    def test_hard_bend_left(self):
        """Test if the MPC algorithm works with a hard bend to the left"""
        assert isPathGoodEnough(path_hard_bend_left, predictedPath)

    def test_hard_bend_right(self):
        """Test if the MPC algorithm works with a hard bend to the right"""
        assert isPathGoodEnough(path_hard_bend_right, predictedPath)

    def test_hairpin_left(self):
        """Test if the MPC algorithm works with a hairpin left"""
        assert isPathGoodEnough(path_hairpin_left, predictedPath)

    def test_hairpin_right(self):
        """Test if the MPC algorithm works with a hairpin right"""
        assert isPathGoodEnough(path_hairpin_right, predictedPath)

    def test_chicane_left(self):
        """Test if the MPC algorithm works with a left-right chicane"""
        assert isPathGoodEnough(path_chicane_left, predictedPath)

    def test_chicane_right(self):
        """Test if the MPC algorithm works with a right-left chicane"""
        assert isPathGoodEnough(path_chicane_right, predictedPath)

class TestMPCAtSpeedAndArbitraryLocation:
    """Tests the MPC algorithm when the car is at speed, and at any arbitrary location"""
    def test_straight_line(self):
        """Test if MPC algorithm works with a straight line (like in the acceleration mission)"""
        assert isPathGoodEnough(path_straight, predictedPath)
    
    def test_slight_bend_left(self):
        """Test if the MPC algorithm works with a slight bend to the left"""
        assert isPathGoodEnough(path_slight_bend_left, predictedPath)

    def test_slight_bend_right(self):
        """Test if the MPC algorithm works with a slight bend to the right"""
        assert isPathGoodEnough(path_slight_bend_right, predictedPath)

    def test_hard_bend_left(self):
        """Test if the MPC algorithm works with a hard bend to the left"""
        assert isPathGoodEnough(path_hard_bend_left, predictedPath)

    def test_hard_bend_right(self):
        """Test if the MPC algorithm works with a hard bend to the right"""
        assert isPathGoodEnough(path_hard_bend_right, predictedPath)

    def test_hairpin_left(self):
        """Test if the MPC algorithm works with a hairpin left"""
        assert isPathGoodEnough(path_hairpin_left, predictedPath)

    def test_hairpin_right(self):
        """Test if the MPC algorithm works with a hairpin right"""
        assert isPathGoodEnough(path_hairpin_right, predictedPath)

    def test_chicane_left(self):
        """Test if the MPC algorithm works with a left-right chicane"""
        assert isPathGoodEnough(path_chicane_left, predictedPath)

    def test_chicane_right(self):
        """Test if the MPC algorithm works with a right-left chicane"""
        assert isPathGoodEnough(path_chicane_right, predictedPath)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])