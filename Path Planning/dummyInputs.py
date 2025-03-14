import numpy as np


def generate_dummy_data(num_steps=100, track_width=10, max_distance=200, step_size=5):

    close_left = []
    close_right = []
    far_left = []
    far_right = []

    for i in range(num_steps):
        x_pos = i * step_size
        y_offset = np.sin(i * 0.1) * 5  # Simulating a curved track
        z = 0  # Flat track

        half_width = track_width / 2

        # Define the four key points
        close_left.append([x_pos, y_offset + half_width, z])
        close_right.append([x_pos, y_offset - half_width, z])
        far_left.append([x_pos + step_size, y_offset + half_width, z])
        far_right.append([x_pos + step_size, y_offset - half_width, z])

    # Convert to NumPy array and return
    data = np.array([close_left, close_right, far_left, far_right]).transpose((1, 0, 2))
    return data


def save_to_file(data, filename="inputs.txt"):
    num_steps = data.shape[0]
    with open(filename, 'w') as f:
        f.write(
            "Index\tClose Left (x,y,z)\tClose Right (x,y,z)\tFar Left (x,y,z)\tFar Right (x,y,z)\n")
        for i in range(num_steps):
            close_l = ','.join(f"{v:.2f}" for v in data[i][0])
            close_r = ','.join(f"{v:.2f}" for v in data[i][1])
            far_l = ','.join(f"{v:.2f}" for v in data[i][2])
            far_r = ','.join(f"{v:.2f}" for v in data[i][3])
            f.write(f"{i}\t{close_l}\t{close_r}\t{far_l}\t{far_r}\n")

    print(f"Data saved to '{filename}'")


if __name__ == "__main__":
    mock_data = generate_dummy_data(num_steps=100, track_width=12, max_distance=300, step_size=5)
    save_to_file(mock_data, filename="inputs.txt")
