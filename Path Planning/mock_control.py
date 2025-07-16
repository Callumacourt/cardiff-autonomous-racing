from mock_car import setCurrentPos

def follow_path(path):
    """
    Simulate following the path by moving to the next point.
    """
    print("path in control:", path)
    if path and len(path) > 1:
        next_point = path[1]  # Move to the next point
        setCurrentPos(next_point[0], next_point[1])
    elif path:
        # Only one point, move there
        setCurrentPos(path[0][0], path[0][1])