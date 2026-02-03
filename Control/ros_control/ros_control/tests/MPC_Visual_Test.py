import os, sys
import pytest


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from MPC.main import Model_Predictive_Control
from nav_msgs.msg import Path
from geometry_msgs.msg import PoseStamped,Pose
from std_msgs.msg import Header

def convertListToPoses(pointsList:list[tuple[float,float]]) -> list[PoseStamped]:
    poseList = []
    for point in pointsList:
        pose = PoseStamped()
        pose.pose.position.x = point[0]
        pose.pose.position.y = point[1]
        pose.pose.position.z = 0.0
        poseList.append(pose)
    
    return poseList

def isPathGoodEnough(desiredPath, predictedPath) -> bool:
    return False

class TestMPCFromStationaryAnd0_0:
    """Tests the MPC algorithm, when the car starts at 0rpm and from 0,0"""

    def test_straight_line(self):
        """Test if MPC algorithm works with a straight line (like in the acceleration mission)"""
        assert isPathGoodEnough(desiredPath, predictedPath)
    
    def test_bend_left(self):
        """Test if the MPC algorithm works with a bend to the left"""
        assert isPathGoodEnough(desiredPath, predictedPath)

    def test_bend_right(self):
        """Test if the MPC algorithm works with a bend to the right"""
        assert isPathGoodEnough(desiredPath, predictedPath)

    def test_hairpin_left(self):
        """Test if the MPC algorithm works with a hairpin left"""
        assert isPathGoodEnough(desiredPath, predictedPath)

    def test_hairpin_right(self):
        """Test if the MPC algorithm works with a hairpin right"""
        assert isPathGoodEnough(desiredPath, predictedPath)

    def test_chicane_left(self):
        """Test if the MPC algorithm works with a left-right chicane"""
        assert isPathGoodEnough(desiredPath, predictedPath)

    def test_chicane_right(self):
        """Test if the MPC algorithm works with a right-left chicane"""
        assert isPathGoodEnough(desiredPath, predictedPath)

class TestMPCAtSpeedAnd0_0:
    """Tests the MPC algorithm when the car is at speed, and located at 0,0"""

    def test_straight_line(self):
        """Test if MPC algorithm works with a straight line (like in the acceleration mission)"""
        assert isPathGoodEnough(desiredPath, predictedPath)
    
    def test_bend_left(self):
        """Test if the MPC algorithm works with a bend to the left"""
        assert isPathGoodEnough(desiredPath, predictedPath)

    def test_bend_right(self):
        """Test if the MPC algorithm works with a bend to the right"""
        assert isPathGoodEnough(desiredPath, predictedPath)

    def test_hairpin_left(self):
        """Test if the MPC algorithm works with a hairpin left"""
        assert isPathGoodEnough(desiredPath, predictedPath)

    def test_hairpin_right(self):
        """Test if the MPC algorithm works with a hairpin right"""
        assert isPathGoodEnough(desiredPath, predictedPath)

    def test_chicane_left(self):
        """Test if the MPC algorithm works with a left-right chicane"""
        assert isPathGoodEnough(desiredPath, predictedPath)

    def test_chicane_right(self):
        """Test if the MPC algorithm works with a right-left chicane"""
        assert isPathGoodEnough(desiredPath, predictedPath)

class TestMPCAtSpeedAndArbitraryLocation:
    """Tests the MPC algorithm when the car is at speed, and at any arbitrary location"""
    def test_straight_line(self):
        """Test if MPC algorithm works with a straight line (like in the acceleration mission)"""
        assert isPathGoodEnough(desiredPath, predictedPath)
    
    def test_bend_left(self):
        """Test if the MPC algorithm works with a bend to the left"""
        assert isPathGoodEnough(desiredPath, predictedPath)

    def test_bend_right(self):
        """Test if the MPC algorithm works with a bend to the right"""
        assert isPathGoodEnough(desiredPath, predictedPath)

    def test_hairpin_left(self):
        """Test if the MPC algorithm works with a hairpin left"""
        assert isPathGoodEnough(desiredPath, predictedPath)

    def test_hairpin_right(self):
        """Test if the MPC algorithm works with a hairpin right"""
        assert isPathGoodEnough(desiredPath, predictedPath)

    def test_chicane_left(self):
        """Test if the MPC algorithm works with a left-right chicane"""
        assert isPathGoodEnough(desiredPath, predictedPath)

    def test_chicane_right(self):
        """Test if the MPC algorithm works with a right-left chicane"""
        assert isPathGoodEnough(desiredPath, predictedPath)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])