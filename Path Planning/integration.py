# Continuously moves towards local goal given by perception info
import time
from rrt_star import rrt_star, PathStatus
from mock_perception import get_cones
from mock_car import getCurrentPos
from mock_control import follow_path


def get_centerline_points(left_cones, right_cones):
    return [((lx + rx) / 2, (ly + ry) / 2) for (lx, ly), (rx, ry) in zip(left_cones, right_cones)]

last_goal_idx = 0

def get_next_local_goal(centerline, current_pos, lookahead=5.0):
    global last_goal_idx
    cx, cy = current_pos
    for i in range(last_goal_idx, len(centerline)):
        pt = centerline[i]
        dist = ((pt[0] - cx) ** 2 + (pt[1] - cy) ** 2) ** 0.5
        if dist >= lookahead:
            last_goal_idx = i
            return pt
    return centerline[-1]  # fallback to last point if none found


def get_current_obstacles(left_cones, right_cones, cone_radius = 1.0):
    obstacles = [(x, y, cone_radius) for (x, y) in left_cones + right_cones] 
    return obstacles

def has_finished(current_pos, centerline, threshold=0.5):
    last_pt = centerline[-1]
    dist = ((current_pos[0] - last_pt[0]) ** 2 + (current_pos[1] - last_pt[1]) ** 2) ** 0.5
    return dist < threshold

def handle_no_path_found():
    # handle the case where no path is found (e.g., stop vehicle)
    print("No path found")

def wait_for_next_update():
    # wait x amount of time if no update?
    pass

if __name__ == "__main__":
    x_max, y_max = 500, 500  # or whatever fits your track
    while True:
        left_cones, right_cones = get_cones()
        start = getCurrentPos()
        centerline = get_centerline_points(left_cones, right_cones)
        goal = get_next_local_goal(centerline, start, lookahead=2.0)
        obstacles = get_current_obstacles(left_cones, right_cones)
        result = rrt_star(start, goal, obstacles, x_max, y_max, max_iter=200, max_step=2, goal_sample_rate=0.05)
        print("Start:", start, "Goal:", goal)
        if result.status in [PathStatus.SUCCESS, PathStatus.PARTIAL]:
            follow_path(result.path)
        else:
            handle_no_path_found()

        # Only check for finish if the goal is the last centerline point
        if goal == centerline[-1]:
            if has_finished(getCurrentPos(), centerline):
                print("Finished! Car has reached the end of the track.")
                break

        time.sleep(0.2)