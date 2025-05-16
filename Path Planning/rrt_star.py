import matplotlib
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import random
import math
import logging

logging.basicConfig(level=logging.ERROR)
matplotlib.use('TkAgg')


# TODO: Implement Exception Handling
# TODO: Implement Logging
# TODO: Implement Path Smoothing to make path less jagged
# TODO: Implement off-set for obstacles of car size to avoid a crash


class Node:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.parent = None
        self.children = []
        self.cost = 0.0

# actual distance between 2 nodes
def euclidean_distance(node1, node2):
    return math.sqrt((node1.x - node2.x) ** 2 + (node1.y - node2.y) ** 2)

def get_random_node(goal, goal_sample_rate, x_max, y_max):
    if random.random() < goal_sample_rate:
        return Node(goal[0], goal[1])
    else:
        return Node(random.uniform(0, x_max), random.uniform(-20, y_max))


def nearest_node(tree, node):
    return min(tree, key=lambda n: euclidean_distance(n, node))


def steer(from_node, to_node, max_step):
    distance = euclidean_distance(from_node, to_node)
    if distance > max_step:
        # Calculates the angle theta (in radians) between the line connecting two points (from_node and to_node) and the positive x-axis.
        theta = math.atan2(to_node.y - from_node.y, to_node.x - from_node.x)
        new_node = Node(from_node.x + max_step * math.cos(theta),
                        from_node.y + max_step * math.sin(theta))
        new_node.parent = from_node
        return new_node
    return to_node

"""
Checks that a node is not within an obstacle radius, as well as if the path between two nodes
does not intersect an obstacle if the node has a parent

PARAM - (step_size) - The distance at which to create temporary nodes between two nodes, to check for obstacle collision
PARAM -Tolerance - The distance from the obstacle that we accept
"""
def is_collision_free(node, obstacles, parent=None, step_size=1, tolerance= 2):
    if parent is None:
        # Check only the node itself
        for (ox, oy, radius) in obstacles:
            if euclidean_distance(node, Node(ox, oy)) <= radius + tolerance:
                return False
        return True

    distance = euclidean_distance(parent, node)
    if distance == 0:  # Avoid division by zero
        return True

    try:
        steps = max(1, int(distance / step_size))
        for i in range(steps + 1):
            x = parent.x + i * (node.x - parent.x) / steps
            y = parent.y + i * (node.y - parent.y) / steps
            for (ox, oy, radius) in obstacles:
                if euclidean_distance(Node(x, y), Node(ox, oy)) <= radius + tolerance:
                    return False
    except ZeroDivisionError:
        logging.error("Division by zero encountered. Values: parent=(%.2f, %.2f), node=(%.2f, %.2f), distance=%.5f, step_size=%.5f",
                      parent.x, parent.y, node.x, node.y, distance, step_size)
        return False

    return True




def find_neighbours(tree, node, min_radius=5.0, use_adaptive_radius=True):
    n = len(tree)
    dimension = 2
    scaling_factor = 20

    if use_adaptive_radius and n > 1:
        search_radius = max(
            min_radius,
            scaling_factor * (math.log(n) / n) ** (1 / dimension)
        )
    else:
        search_radius = min_radius

    return [
        other_node for other_node in tree
        if other_node != node and euclidean_distance(node, other_node) <= search_radius
    ]


def choose_parent(new_node, nearby_nodes):
    if not nearby_nodes:
        return None
    # Compares nodes around the new node to find the one with the lowest cost
    parent = min(nearby_nodes, key=lambda n: n.cost + euclidean_distance(n, new_node))
    new_node.cost = parent.cost + euclidean_distance(parent, new_node)
    new_node.parent = parent
    return new_node


# Rewires the nearby nodes to the new node if it is cheaper
def rewire(new_node, nearby_nodes, obstacles):
    for neighbor in nearby_nodes:
        # Skip if neighbor is the parent of new_node or is new_node itself
        if neighbor == new_node.parent or neighbor == new_node:
            continue

        # Check if the path between new_node and neighbor is collision-free
        midpoint = Node((new_node.x + neighbor.x) / 2, (new_node.y + neighbor.y) / 2)
        if not is_collision_free(midpoint, obstacles, parent=new_node, tolerance = 2):
            continue

        # Calculate potential new cost
        potential_new_cost = new_node.cost + euclidean_distance(new_node, neighbor)

        # Only rewire if it improves the cost
        if potential_new_cost < neighbor.cost:
            # Update parent-child relationship
            if neighbor.parent:
                try:
                    neighbor.parent.children.remove(neighbor)
                except ValueError:
                    # Handle case where neighbor is not in parent's children list
                    pass

            # Update parent, cost, and children lists
            neighbor.parent = new_node
            neighbor.cost = potential_new_cost
            new_node.children.append(neighbor)

            # Propagate cost updates to descendants
            update_descendants_cost(neighbor)


# Updates node costs down the branch of the tree/path
def update_descendants_cost(node):
    stack = [node]
    while stack:
        current = stack.pop()
        for child in current.children:
            child.cost = current.cost + euclidean_distance(current, child)
            stack.append(child)


# Extracts the path from the start node to the goal node (Sets as final path)
def extract_path(last_node):
    path = [(last_node.x, last_node.y)]
    while last_node.parent is not None:
        last_node = last_node.parent
        path.append((last_node.x, last_node.y))
    return path[::-1]

#Run loop
def rrt_star(start, goal, obstacles, x_max, y_max, max_iter=500, max_step=5, goal_sample_rate=0.05, radius=10.0):
    tree = [Node(start[0], start[1])]
    for _ in range(max_iter):
        rand_node = get_random_node(goal, goal_sample_rate, x_max, y_max)
        nearest = nearest_node(tree, rand_node)
        new_node = steer(nearest, rand_node, max_step)

        if is_collision_free(new_node, obstacles, parent=nearest, tolerance=2):
            nearby_nodes = find_neighbours(tree, new_node, min_radius=radius)
            new_node = choose_parent(new_node, nearby_nodes) or new_node
            tree.append(new_node)
            rewire(new_node, nearby_nodes, obstacles)

            if euclidean_distance(new_node, Node(goal[0], goal[1])) <= max_step:
                goal_node = Node(goal[0], goal[1])
                goal_node.parent = new_node
                goal_node.cost = new_node.cost + euclidean_distance(new_node, goal_node)
                return extract_path(goal_node), tree
    return None, tree


# New plot result function for visualisations
def plot(path, obstacles, start, goal, tree=None, x_max=100, y_max=100):
    plt.figure(figsize=(10, 8))
    
    # Set the plot limits
    plt.xlim(0, x_max)
    plt.ylim(0, y_max)
    
    # Plot obstacles
    for ox, oy, radius in obstacles:
        circle = plt.Circle((ox, oy), radius, color='red', alpha=0.5)
        plt.gca().add_patch(circle)
    
    # Plot the tree if provided
    if tree:
        for node in tree:
            if node.parent:
                plt.plot([node.x, node.parent.x], [node.y, node.parent.y], 'c-', alpha=0.5, label='Tree' if node == tree[1] else "")
    
    # Plot the path if found
    if path:
        plt.plot([x for x, y in path], [y for x, y in path], '-g', linewidth=2, label='Path')
        plt.scatter([x for x, y in path], [y for x, y in path], c='green', marker='o', s=20, label='Path Nodes')
    else:
        plt.title("No path found")
    
    # Plot start and goal
    plt.scatter(start[0], start[1], c='blue', marker='o', s=100, label='Start')
    plt.scatter(goal[0], goal[1], c='purple', marker='*', s=150, label='Goal')
    
    # Add grid, legend, and show the plot
    plt.grid(True)
    plt.legend()
    plt.title("RRT* Path Planning")
    plt.axis('equal')
    plt.show()

# Example usage
# start = (13, 70)
# goal = (48, 32)
# obstacles = [(40, 40, 10), (60, 60, 10), (50, 20, 10)]
# path = rrt_star(start, goal, obstacles, 100, 100)
# plot(path)
