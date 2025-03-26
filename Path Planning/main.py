import os
from dummy_inputs import generate_dummy_data, save_to_file
from rrt_star import rrt_star, Node , plot


# ---------------------- TEMPORARY FUNCTION ------------------------------------
# A function which reads the content of the input file we are using as temporary input information.
def read_input_file(input_file_path):
    try:
        with open(input_file_path, 'r') as file:
            lines = file.readlines()
            lines[0].strip()
            data = [line.strip().split('\t') for line in lines[1:]]

            # gets midpoint between 2 first points to get start
            start_x = (float(data[0][1].split(',')[0]) + float(data[0][2].split(',')[0])) / 2
            start_y = (float(data[0][1].split(',')[1]) + float(data[0][2].split(',')[1])) / 2
            start = (start_x, start_y)

            # gets midpoint between 2 last points to get goal
            goal_x = (float(data[-1][1].split(',')[0]) + float(data[-1][2].split(',')[0])) / 2
            goal_y = (float(data[-1][1].split(',')[1]) + float(data[-1][2].split(',')[1])) / 2
            goal = (goal_x, goal_y)

            # Finds all other points to set to obstacles
            obstacles = []
            for line in data:
                for i in range(1, 5):
                    x, y, _ = map(float, line[i].split(','))
                    obstacles.append((x, y, 1.0))

            # calls rrt* algorithm to make path
            path = rrt_star(start, goal, obstacles, 500, 500)

            if path:
                print("Path found:", path)
                # plots the path if found for visuals
                plot(path, obstacles, start, goal)
            else:
                print("No path found.")

    except FileNotFoundError:
        # Generate dummy data and save to file
        mock_data = generate_dummy_data(num_steps=100, track_width=12, max_distance=300, step_size=5)
        save_to_file(mock_data, filename=input_file_path)

        # Run the function again to read the newly created file
        read_input_file(input_file_path)
    except IOError as e:
        print(f"Error opening file: {e}")


if __name__ == "__main__":
    # Install the required packages
    os.system('pip install -r requirements.txt')

    file_path = 'inputs.txt'
    read_input_file(file_path)
