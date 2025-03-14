import numpy as np
import matplotlib.pyplot as plt
import random
import math

class Node:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.parent = None
        self.cost = 0.0

def euclidean_distance(node1, node2):
    return math.sqrt((node1.x - node2.x)**2 + (node1.y - node2.y)**2)

def get_random_node(goal, goal_sample_rate, x_max, y_max):
    if random.random() < goal_sample_rate:
        return Node(goal[0], goal[1])
    else:
        return Node(random.uniform(0, x_max), random.uniform(0, y_max))

def nearest_node(tree, node):
    return min(tree, key=lambda n: euclidean_distance(n, node))

def steer(from_node, to_node, max_step):
    distance = euclidean_distance(from_node, to_node)
    if distance > max_step:
        theta = math.atan2(to_node.y - from_node.y, to_node.x - from_node.x)
        new_node = Node(from_node.x + max_step * math.cos(theta), 
                        from_node.y + max_step * math.sin(theta))
        new_node.parent = from_node
        return new_node
    return to_node

def is_collision_free(node, obstacles):
    for (ox, oy, radius) in obstacles:
        if euclidean_distance(node, Node(ox, oy)) <= radius:
            return False
    return True

def find_nearby_nodes(tree, new_node, radius):
    return [node for node in tree if euclidean_distance(node, new_node) <= radius]

def choose_parent(new_node, nearby_nodes):
    if not nearby_nodes:
        return None
    parent = min(nearby_nodes, key=lambda n: n.cost + euclidean_distance(n, new_node))
    new_node.cost = parent.cost + euclidean_distance(parent, new_node)
    new_node.parent = parent
    return new_node

def rewire(tree, new_node, nearby_nodes):
    for node in nearby_nodes:
        new_cost = new_node.cost + euclidean_distance(new_node, node)
        if new_cost < node.cost:
            node.parent = new_node
            node.cost = new_cost

def extract_path(last_node):
    path = [(last_node.x, last_node.y)]
    while last_node.parent is not None:
        last_node = last_node.parent
        path.append((last_node.x, last_node.y))
    return path[::-1]

def rrt_star(start, goal, obstacles, x_max, y_max, max_iter=500, max_step=5.0, goal_sample_rate=0.1, radius=10.0):
    tree = [Node(start[0], start[1])]
    for _ in range(max_iter):
        rand_node = get_random_node(goal, goal_sample_rate, x_max, y_max)
        nearest = nearest_node(tree, rand_node)
        new_node = steer(nearest, rand_node, max_step)
        
        if is_collision_free(new_node, obstacles):
            nearby_nodes = find_nearby_nodes(tree, new_node, radius)
            new_node = choose_parent(new_node, nearby_nodes) or new_node
            tree.append(new_node)
            rewire(tree, new_node, nearby_nodes)
            
            if euclidean_distance(new_node, Node(goal[0], goal[1])) <= max_step:
                goal_node = Node(goal[0], goal[1])
                goal_node.parent = new_node
                goal_node.cost = new_node.cost + euclidean_distance(new_node, goal_node)
                return extract_path(goal_node)
    return None

# Example usage
start = (13, 70)
goal = (48, 32)
obstacles = [(40, 40, 10), (60, 60, 10), (50, 20, 10)]
path = rrt_star(start, goal, obstacles, 100, 100)

# Plot result
if path:
    plt.figure()
    plt.xlim(0, 100)
    plt.ylim(0, 100)
    for ox, oy, r in obstacles:
        circle = plt.Circle((ox, oy), r, color='r')
        plt.gca().add_patch(circle)
    plt.plot([x for x, y in path], [y for x, y in path], '-g')
    plt.scatter(start[0], start[1], c='b', marker='o')
    plt.scatter(goal[0], goal[1], c='r', marker='x')
    plt.show()

    
# ---------------------- TEMPORARY FUNCTION ------------------------------------
# A function which reads the content of the input file we are using as temporary input information.
def read_input_file(input_file_path):
    try:
        with open(input_file_path, 'r') as file:
            content = file.read()
            print("\nFile contents:")
            print(content)

    except FileNotFoundError:
        print(f"Error: The file at {file_path} was not found.")
    except IOError as e:
        print(f"Error opening file: {e}")


if __name__ == "__main__":
    file_path = input("Please enter the file path: ")
    read_input_file(file_path)
