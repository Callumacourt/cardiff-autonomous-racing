import matplotlib
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import random
import math

matplotlib.use('TkAgg')


class Node:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.parent = None
        self.children = []
        self.cost = 0.0


def euclidean_distance(node1, node2):
    return math.sqrt((node1.x - node2.x) ** 2 + (node1.y - node2.y) ** 2)


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
    parent = min(nearby_nodes, key=lambda n: n.cost + euclidean_distance(n, new_node))
    new_node.cost = parent.cost + euclidean_distance(parent, new_node)
    new_node.parent = parent
    return new_node


def rewire(new_node, nearby_nodes, obstacles):
    nodes_rewired = 0
    total_cost_improvement = 0

    for neighbor in nearby_nodes:
        # Skip if neighbor is the parent of new_node or is new_node itself
        if neighbor == new_node.parent or neighbor == new_node:
            continue

        # Check if the path between new_node and neighbor is collision-free
        midpoint = Node((new_node.x + neighbor.x) / 2, (new_node.y + neighbor.y) / 2)
        if not is_collision_free(midpoint, obstacles):
            continue

        # Calculate potential new cost
        potential_new_cost = new_node.cost + euclidean_distance(new_node, neighbor)

        # Only rewire if it improves the cost
        if potential_new_cost < neighbor.cost:
            # Calculate cost improvement
            cost_improvement = neighbor.cost - potential_new_cost

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

            # Update stats (just to show rewiring is working)
            nodes_rewired += 1
            total_cost_improvement += cost_improvement

    if total_cost_improvement > 0:
        print(f"Cost improvement: {total_cost_improvement:.4f}")

    return nodes_rewired, total_cost_improvement


def update_descendants_cost(node):
    stack = [node]
    while stack:
        current = stack.pop()
        for child in current.children:
            child.cost = current.cost + euclidean_distance(current, child)
            stack.append(child)


def extract_path(last_node):
    path = [(last_node.x, last_node.y)]
    while last_node.parent is not None:
        last_node = last_node.parent
        path.append((last_node.x, last_node.y))
    return path[::-1]


def rrt_star(start, goal, obstacles, x_max, y_max, max_iter=5000, max_step=5.0, goal_sample_rate=0.1, radius=10.0):
    tree = [Node(start[0], start[1])]
    for _ in range(max_iter):
        rand_node = get_random_node(goal, goal_sample_rate, x_max, y_max)
        nearest = nearest_node(tree, rand_node)
        new_node = steer(nearest, rand_node, max_step)

        if is_collision_free(new_node, obstacles):
            nearby_nodes = find_neighbours(tree, new_node, min_radius=radius)
            new_node = choose_parent(new_node, nearby_nodes) or new_node
            tree.append(new_node)
            rewire(new_node, nearby_nodes, obstacles)

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
