def get_mock_cones(num_steps=10, track_width=10.0, step_size=2.0):
    """
    Generate mock left and right cone positions for a straight track
    Returns two lists: left_cones, right_cones, each as [(x, y), ...]
    """
    left_cones = []
    right_cones = []
    half_width = track_width / 2
    for i in range(num_steps):
        x = i * step_size
        left_cones.append((x, half_width))
        right_cones.append((x, -half_width))
    return left_cones, right_cones

def get_cones():
    """
    Simulate perception callback: returns current left and right cones.
    """
    left_cones, right_cones = get_mock_cones()
    return left_cones, right_cones

if __name__ == "__main__":
    left_cones, right_cones = get_cones()
    print("Left cones:", left_cones)