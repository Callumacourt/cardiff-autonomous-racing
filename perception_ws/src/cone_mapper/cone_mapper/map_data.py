"""Data structures for cone map management."""
import numpy as np
from typing import List, Dict, Optional
import time
import math
import json

from .constants import ConeColor

class PersistentGlobalMap:
    """Persistent global cone map with confidence filtering."""
    
    def __init__(self, confidence_threshold: float = 0.7, min_detections: int = 3):
        """
        Initialize global map.
        
        Args:
            confidence_threshold: Minimum confidence to add cone to global map
            min_detections: Minimum detection count required
        """
        self.global_cones: List[Dict] = []
        self.confidence_threshold = confidence_threshold
        self.min_detections = min_detections
        self.cone_id_counter = 0
        
    def try_add_cone(self, cone_data: Dict) -> bool:
        """
        Try to add a cone to global map if it meets criteria.
        
        Args:
            cone_data: Dictionary with keys: x, y, z, color, confidence, detections
            
        Returns:
            True if cone was added, False if rejected or duplicate
        """
        if (cone_data['confidence'] > self.confidence_threshold and 
            cone_data['detections'] >= self.min_detections):
            
            # Check if already in global map (avoid duplicates)
            for existing in self.global_cones:
                if (existing['color'] == cone_data['color'] and
                    np.linalg.norm([existing['x'] - cone_data['x'], 
                                   existing['y'] - cone_data['y']]) < 1.5):
                    return False  # Already exists
            
            # Add to global map
            self.cone_id_counter += 1
            global_cone = {
                'id': self.cone_id_counter,
                'x': cone_data['x'],
                'y': cone_data['y'], 
                'z': cone_data['z'],
                'color': cone_data['color'],
                'confidence': cone_data['confidence'],
                'detections': cone_data['detections'],
                'added_timestamp': time.time()
            }
            self.global_cones.append(global_cone)
            return True
        return False
    
    def get_global_map(self) -> List[Dict]:
        """Get copy of all cones in global map."""
        return self.global_cones.copy()
    
    def get_local_view(self, vehicle_pos: tuple, radius: float = 20.0) -> List[Dict]:
        """
        Get cones within radius of vehicle position.
        
        Args:
            vehicle_pos: Tuple of (x, y) vehicle position
            radius: Search radius in meters
            
        Returns:
            List of cones within radius
        """
        veh_x, veh_y = vehicle_pos
        local_cones = []
        
        for cone in self.global_cones:
            distance = math.sqrt((cone['x'] - veh_x)**2 + (cone['y'] - veh_y)**2)
            if distance <= radius:
                local_cones.append(cone)
        
        return local_cones
    
    def save_to_file(self, filename: str):
        """Save global map to JSON file."""
        with open(filename, 'w') as f:
            json.dump(self.global_cones, f, indent=2)
    
    def get_stats(self) -> Dict:
        """Get statistics about global map."""
        color_counts = {
            ConeColor.BLUE: 0, 
            ConeColor.YELLOW: 0, 
            ConeColor.ORANGE: 0
        }
        for cone in self.global_cones:
            color = cone['color']
            if color in color_counts:
                color_counts[color] += 1
        
        return {
            'total_cones': len(self.global_cones),
            'blue_cones': color_counts[ConeColor.BLUE],
            'yellow_cones': color_counts[ConeColor.YELLOW],
            'orange_cones': color_counts[ConeColor.ORANGE]
        }


class LocalConeBuffer:
    """Sliding window buffer for recent cone detections with temporal filtering."""
    
    def __init__(self, max_size: int = 200, max_age: float = 6.0):
        """
        Initialize local buffer.
        
        Args:
            max_size: Maximum number of cones to track
            max_age: Maximum age in seconds before cone is dropped
        """
        self.cones: List[Dict] = []
        self.max_size = max_size
        self.max_age = max_age
        self.cone_id_counter = 0
        
    def add_cone_detection(self, x: float, y: float, z: float, 
                          color: int, confidence: float = 1.0):
        """
        Add or update cone detection with distance-based confidence.
        
        Args:
            x, y, z: Cone position in world frame
            color: Cone color label (ConeColor enum value)
            confidence: Initial confidence value
        """
        current_time = time.time()
        
        # Calculate distance for confidence adjustment
        distance = np.sqrt(x*x + y*y + z*z)
        
        # Find matching cone
        matching_idx = self._find_matching_cone(x, y, color)
        
        if matching_idx is not None:
            # Update existing cone using exponential moving average
            cone = self.cones[matching_idx]
            cone['x'] = 0.3 * x + 0.7 * cone['x']  # EMA
            cone['y'] = 0.3 * y + 0.7 * cone['y']
            cone['z'] = 0.3 * z + 0.7 * cone['z']
            
            # Distance-based confidence gain
            confidence_gain = 0.2 if distance < 5.0 else 0.15 if distance < 10.0 else 0.1
            cone['confidence'] = min(1.0, cone['confidence'] + confidence_gain)
            cone['detections'] += 1
            cone['last_seen'] = current_time
        else:
            # Add new cone with distance-based initial confidence
            if distance < 3.0:
                initial_conf = 0.6
            elif distance < 8.0:
                initial_conf = 0.4
            else:
                initial_conf = 0.3
                
            self.cone_id_counter += 1
            self.cones.append({
                'id': self.cone_id_counter,
                'x': x, 'y': y, 'z': z, 'color': color,
                'confidence': initial_conf,
                'detections': 1,
                'first_seen': current_time,
                'last_seen': current_time
            })
    
    def update_frame(self):
        """Update confidence decay and prune old/low-confidence cones."""
        current_time = time.time()
        
        # Decay confidence for unseen cones
        for cone in self.cones:
            age = current_time - cone['last_seen']
            if age > 0.1:  # Not seen this frame
                cone['confidence'] = max(0.0, cone['confidence'] - 0.04)
        
        # Remove old or low-confidence cones
        self.cones = [cone for cone in self.cones 
                     if (current_time - cone['first_seen'] < self.max_age and
                         cone['confidence'] > 0.15)]
        
        # Limit size (keep highest confidence)
        if len(self.cones) > self.max_size:
            self.cones.sort(key=lambda x: x['confidence'], reverse=True)
            self.cones = self.cones[:self.max_size]
    
    def get_all_cones(self) -> List[Dict]:
        """Get all cones in buffer."""
        return self.cones.copy()
    
    def get_high_confidence_cones(self, threshold: float = 0.6) -> List[Dict]:
        """Get cones above confidence threshold."""
        return [cone for cone in self.cones if cone['confidence'] > threshold]
    
    def _find_matching_cone(self, x: float, y: float, color: int,
                           radius: float = 2.0) -> Optional[int]:
        """
        Find the nearest same-colour cone within *radius* metres.

        Returns the index into self.cones, or None.  A plain linear scan:
        the buffer holds at most max_size (200) cones.
        """
        best_idx = None
        best_dist_sq = radius * radius

        for i, cone in enumerate(self.cones):
            if cone['color'] != color:
                continue
            d_sq = (cone['x'] - x) ** 2 + (cone['y'] - y) ** 2
            if d_sq < best_dist_sq:
                best_dist_sq = d_sq
                best_idx = i

        return best_idx