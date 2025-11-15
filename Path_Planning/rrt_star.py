import matplotlib
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import random
import math
import logging
from typing import List, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum

logging.basicConfig(level=logging.INFO)
matplotlib.use('Agg')  # Use headless backend for Docker containers


# TODO: Implement Exception Handling
# TODO: Implement Logging
# TODO: Implement Path Smoothing to make path less jagged

class PathPlanningError(Exception):
    """Base exception for path planning errors"""
    pass

class CollisionError(PathPlanningError):
    """Raised when a collision is detected"""
    pass

class BoundaryError(PathPlanningError):
    """Raised when a point is outside valid boundaries"""
    pass

class NumericalError(PathPlanningError):
    """Raised when numerical instability is detected"""
    pass

class ResourceError(PathPlanningError):
    """Raised when resource constraints are exceeded"""
    pass

class PathStatus(Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"

@dataclass
class PathResult:
    path: Optional[List[Tuple[float, float]]]
    tree: List['Node']
    status: PathStatus
    error: Optional[Exception] = None

class Node:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.parent: Optional[Node] = None
        self.children: List[Node] = []
        self.cost: float = 0.0
        self._validate_coordinates()

    def _validate_coordinates(self):
        """Validate node coordinates"""
        if not (isinstance(self.x, (int, float)) and isinstance(self.y, (int, float))):
            raise ValueError(f"Invalid coordinates: x={self.x}, y={self.y}")
        if math.isnan(self.x) or math.isnan(self.y):
            raise NumericalError("NaN coordinates detected")

# actual distance between 2 nodes
def euclidean_distance(node1: Node, node2: Node) -> float:
    try:
        return math.sqrt((node1.x - node2.x) ** 2 + (node1.y - node2.y) ** 2)
    except (TypeError, ValueError) as e:
        raise NumericalError(f"Error calculating distance: {str(e)}")

def get_random_node(goal: Tuple[float, float], goal_sample_rate: float, x_max: float, y_max: float) -> Node:
    try:
        if not (0 <= goal_sample_rate <= 1):
            raise ValueError(f"Invalid goal sample rate: {goal_sample_rate}")
        
        if random.random() < goal_sample_rate:
            return Node(goal[0], goal[1])
        else:
            x = random.uniform(0, x_max)
            y = random.uniform(-20, y_max)
            return Node(x, y)
    except Exception as e:
        raise PathPlanningError(f"Error generating random node: {str(e)}")


def nearest_node(tree: List[Node], node: Node) -> Node:
    if not tree:
        raise PathPlanningError("Empty tree provided")
    try:
        return min(tree, key=lambda n: euclidean_distance(n, node))
    except Exception as e:
        raise PathPlanningError(f"Error finding nearest node: {str(e)}")


def steer(from_node: Node, to_node: Node, max_step: float) -> Node:
    try:
        distance = euclidean_distance(from_node, to_node)
        if distance > max_step:
            # Calculates the angle theta (in radians) between the line connecting two points (from_node and to_node) and the positive x-axis.
            theta = math.atan2(to_node.y - from_node.y, to_node.x - from_node.x)
            new_node = Node(from_node.x + max_step * math.cos(theta),
                            from_node.y + max_step * math.sin(theta))
            new_node.parent = from_node
            return new_node
        return to_node
    except Exception as e:
        raise PathPlanningError(f"Error in steering: {str(e)}")

"""
Checks that a node is not within an obstacle radius, as well as if the path between two nodes
does not intersect an obstacle if the node has a parent

PARAM - (step_size) - The distance at which to create temporary nodes between two nodes, to check for obstacle collision
PARAM -Tolerance - The distance from the obstacle that we accept
"""
def is_collision_free(node: Node, obstacles: List[Tuple[float, float, float]], 
                     parent: Optional[Node] = None, step_size: float = 1, 
                     tolerance: float = 2) -> bool:
    try:
        if parent is None:
            # Check only the node itself
            for (ox, oy, radius) in obstacles:
                if euclidean_distance(node, Node(ox, oy)) <= radius + tolerance:
                    return False
            return True

        distance = euclidean_distance(parent, node)
        if distance == 0:  # Avoid division by zero
            return True

        steps = max(1, int(distance / step_size))
        for i in range(steps + 1):
            x = parent.x + i * (node.x - parent.x) / steps
            y = parent.y + i * (node.y - parent.y) / steps
            for (ox, oy, radius) in obstacles:
                if euclidean_distance(Node(x, y), Node(ox, oy)) <= radius + tolerance:
                    return False
        return True
    except Exception as e:
        logging.error(f"Collision check error: {str(e)}")
        return False




def find_neighbours(tree: List[Node], node: Node, min_radius: float = 5.0, use_adaptive_radius: bool = True) -> List[Node]:
    try:
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
    except Exception as e:
        raise PathPlanningError(f"Error finding neighbours: {str(e)}")


def choose_parent(new_node: Node, nearby_nodes: List[Node]) -> Optional[Node]:
    try:
        if not nearby_nodes:
            return None
        # Compares nodes around the new node to find the one with the lowest cost
        parent = min(nearby_nodes, key=lambda n: n.cost + euclidean_distance(n, new_node))
        new_node.cost = parent.cost + euclidean_distance(parent, new_node)
        new_node.parent = parent
        return new_node
    except Exception as e:
        raise PathPlanningError(f"Error choosing parent: {str(e)}")


# Rewires the nearby nodes to the new node if it is cheaper
def rewire(new_node: Node, nearby_nodes: List[Node], obstacles: List[Tuple[float, float, float]]) -> None:
    try:
        total_cost_improvement = 0
        nodes_rewired = 0
        cost_improvement = 0

        for neighbor in nearby_nodes:
            # Skip if neighbor is the parent of new_node or is new_node itself
            if neighbor == new_node.parent or neighbor == new_node:
                continue

            # Check if the path between new_node and neighbor is collision-free
            midpoint = Node((new_node.x + neighbor.x) / 2, (new_node.y + neighbor.y) / 2)
            if not is_collision_free(midpoint, obstacles, parent=new_node, tolerance = 0.3):
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

    except Exception as e:
        logging.error(f"Rewiring error: {str(e)}")


# Updates node costs down the branch of the tree/path
def update_descendants_cost(node: Node) -> None:
    try:
        stack = [node]
        while stack:
            current = stack.pop()
            for child in current.children:
                child.cost = current.cost + euclidean_distance(current, child)
                stack.append(child)
    except Exception as e:
        logging.error(f"Error updating descendant costs: {str(e)}")


# Extracts the path from the start node to the goal node (Sets as final path)
def extract_path(last_node: Node) -> List[Tuple[float, float]]:
    try:
        path = [(last_node.x, last_node.y)]
        while last_node.parent is not None:
            last_node = last_node.parent
            path.append((last_node.x, last_node.y))
        return path[::-1]
    except Exception as e:
        raise PathPlanningError(f"Error extracting path: {str(e)}")

#Run loop
def rrt_star(start: Tuple[float, float], goal: Tuple[float, float],
             obstacles: List[Tuple[float, float, float]], x_max: float, y_max: float,
             max_iter: int = 500, max_step: float = 5, goal_sample_rate: float = 0.05,
             radius: float = 10.0) -> PathResult:
    tree = []  # Initialize the tree to avoid UnboundLocalError
    try:
        # Input validation
        # if not (0 <= start[0] <= x_max and 0 <= start[1] <= y_max):
        #     raise BoundaryError(f"Start position {start} outside boundaries")
        # if not (0 <= goal[0] <= x_max and 0 <= goal[1] <= y_max):
        #     raise BoundaryError(f"Goal position {goal} outside boundaries")

        # Initialize tree with start node
        tree = [Node(start[0], start[1])]
        best_path = None
        best_cost = float('inf')

        for iteration in range(max_iter):
            try:
                rand_node = get_random_node(goal, goal_sample_rate, x_max, y_max)
                nearest = nearest_node(tree, rand_node)
                new_node = steer(nearest, rand_node, max_step)

                if is_collision_free(new_node, obstacles, parent=nearest, tolerance=0.3):
                    nearby_nodes = find_neighbours(tree, new_node, min_radius=radius)
                    new_node = choose_parent(new_node, nearby_nodes) or new_node
                    tree.append(new_node)
                    rewire(new_node, nearby_nodes, obstacles)

                    # Check if we can reach the goal
                    if euclidean_distance(new_node, Node(goal[0], goal[1])) <= max_step:
                        goal_node = Node(goal[0], goal[1])
                        goal_node.parent = new_node
                        goal_node.cost = new_node.cost + euclidean_distance(new_node, goal_node)

                        # Update best path if this one is better
                        if goal_node.cost < best_cost:
                            best_path = extract_path(goal_node)
                            best_cost = goal_node.cost

                            # Early termination if we have a good enough path
                            if best_cost < max_step * 2:
                                return PathResult(best_path, tree, PathStatus.SUCCESS)

            except Exception as e:
                logging.warning(f"Iteration {iteration} failed: {str(e)}")
                continue

        # Return best path found or None if no path found
        if best_path:
            return PathResult(best_path, tree, PathStatus.PARTIAL)
        return PathResult(None, tree, PathStatus.FAILED)

    except Exception as e:
        logging.error(f"RRT* planning failed: {str(e)}")
        return PathResult(None, tree, PathStatus.FAILED, error=e)


# New plot result function for visualisations
def plot(path: Optional[List[Tuple[float, float]]], obstacles: List[Tuple[float, float, float]],
         start: Tuple[float, float], goal: Tuple[float, float], tree: Optional[List[Node]] = None,
         x_max: float = 100, y_max: float = 100, show_tree: bool = True, 
         cone_data: Optional[dict] = None) -> None:
    """
    Enhanced plot function with support for cone visualization
    
    Args:
        cone_data: Dictionary with keys 'left_cones', 'right_cones', 'centerline' 
                  containing lists of (x, y) tuples
    """
    try:
        plt.figure(figsize=(12, 8))
        
        # Set the plot limits with some padding
        plt.xlim(-5, x_max + 5)
        plt.ylim(-20, y_max + 5)
        
        # Plot obstacles
        for i, (ox, oy, radius) in enumerate(obstacles):
            circle = plt.Circle((ox, oy), radius, color='red', alpha=0.5)
            plt.gca().add_patch(circle)
            if i == 0:  # Add label only for first obstacle
                circle.set_label('Obstacles')
        
        # Plot cone data if provided
        if cone_data:
            if 'left_cones' in cone_data and cone_data['left_cones']:
                left_x = [cone[0] for cone in cone_data['left_cones']]
                left_y = [cone[1] for cone in cone_data['left_cones']]
                plt.scatter(left_x, left_y, c='blue', marker='s', s=60, 
                           alpha=0.8, label='Left Cones', edgecolors='darkblue')
            
            if 'right_cones' in cone_data and cone_data['right_cones']:
                right_x = [cone[0] for cone in cone_data['right_cones']]
                right_y = [cone[1] for cone in cone_data['right_cones']]
                plt.scatter(right_x, right_y, c='orange', marker='s', s=60, 
                           alpha=0.8, label='Right Cones', edgecolors='darkorange')
            
            if 'centerline' in cone_data and cone_data['centerline']:
                center_x = [point[0] for point in cone_data['centerline']]
                center_y = [point[1] for point in cone_data['centerline']]
                plt.plot(center_x, center_y, '--', color='gray', linewidth=2, 
                        alpha=0.7, label='Centerline')
        
        # Plot the tree if provided and requested
        if tree and show_tree:
            tree_plotted = False
            for node in tree:
                if node.parent:
                    plt.plot([node.x, node.parent.x], [node.y, node.parent.y], 
                            'c-', alpha=0.3, linewidth=0.5)
                    if not tree_plotted:
                        plt.plot([node.x, node.parent.x], [node.y, node.parent.y], 
                                'c-', alpha=0.3, linewidth=0.5, label='RRT* Tree')
                        tree_plotted = True
        
        # Plot the path if found
        if path:
            plt.plot([x for x, y in path], [y for x, y in path], '-g', linewidth=3, label='Planned Path')
            plt.scatter([x for x, y in path], [y for x, y in path], c='green', marker='o', s=30, alpha=0.8)
        else:
            plt.title("No path found")
        
        # Plot start and goal
        plt.scatter(start[0], start[1], c='blue', marker='o', s=150, label='Start', 
                   edgecolors='darkblue', linewidth=2)
        plt.scatter(goal[0], goal[1], c='purple', marker='*', s=200, label='Goal',
                   edgecolors='darkred', linewidth=2)
        
        # Add grid, legend, and show the plot
        plt.grid(True, alpha=0.3)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.title("RRT* Path Planning with Perception Data")
        plt.xlabel('X Position (m)')
        plt.ylabel('Y Position (m)')
        plt.axis('equal')
        plt.tight_layout()
        plt.show()
    except Exception as e:
        logging.error(f"Error plotting results: {str(e)}")
        raise
