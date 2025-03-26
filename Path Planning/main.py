import os
from rrt_star import rrt_star, Node


# ---------------------- TEMPORARY FUNCTION ------------------------------------
# A function which reads the content of the input file we are using as temporary input information.
def read_input_file(input_file_path):
    try:
        with open(input_file_path, 'r') as file:
            lines = file.readlines()
            header = lines[0].strip()
            data = [line.strip().split('\t') for line in lines[1:]]

            # Extract start, goal, and obstacles
            start = (float(data[0][1].split(',')[0]), float(data[0][1].split(',')[1]))
            goal = (float(data[-1][3].split(',')[0]), float(data[-1][3].split(',')[1]))
            obstacles = []
            for line in data:
                for i in range(1, 4):
                    x, y, _ = map(float, line[i].split(','))
                    obstacles.append((x, y, 1.0))  # Assuming a default radius of 1.0 for obstacles

            # Call the RRT* algorithm
            path = rrt_star(start, goal, obstacles, 500, 500)

            if path:
                print("Path found:", path)
            else:
                print("No path found.")

    except FileNotFoundError:
        print(f"Error: The file at {file_path} was not found.")
    except IOError as e:
        print(f"Error opening file: {e}")


if __name__ == "__main__":
    # Install the required packages
    os.system('pip install -r requirements.txt')

    file_path = 'inputs.txt'
    read_input_file(file_path)
