import os, sys
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


if __name__ == "__main__":
    #
    timer_period = 0.01
    mpc = Model_Predictive_Control(timer_period, 5)

    #create 1st path
    path1 = Path()
    path1.header = Header()
    path1.poses = convertListToPoses([(0,0),(0,1),(0,2),(0,3),(0,4),(0,5),(0,5),(0,6),(0,7),(0,8),(0,9)])
    #create 2nd path
    #create 3rd path
    #create 4th path