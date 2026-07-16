"""Data structures for cone map management.

Both classes take a ``now_fn`` returning seconds. The node passes its ROS
clock so aging follows sim time in the simulator and wall time on the car;
the default (time.time) keeps the classes usable without ROS in tests.
"""
import json
import math
import time
from typing import Callable, Dict, List, Optional

from .constants import ConeColor


class PersistentGlobalMap:
    """Persistent global cone map with confidence filtering.

    Cones are promoted from the local buffer once seen often enough with
    high enough confidence, and are never removed. Re-detections of an
    already-promoted cone REFINE its stored position (exponential moving
    average) instead of being discarded — otherwise a cone promoted while
    the SLAM pose was drifting keeps that bias forever, even after loop
    closure has corrected the pose.
    """

    # Orange classes are the rarest in YOLO training data and the least
    # reliable, so they must clear a higher bar to enter the map.
    ORANGE_MIN_DETECTIONS = 6
    ORANGE_CONFIDENCE_THRESHOLD = 0.85

    # Weight of a new observation when refining a stored position
    REFINE_ALPHA = 0.25

    def __init__(self, confidence_threshold: float = 0.7, min_detections: int = 3,
                 duplicate_radius: float = 1.5,
                 now_fn: Callable[[], float] = time.time):
        self.global_cones: List[Dict] = []
        self.confidence_threshold = confidence_threshold
        self.min_detections = min_detections
        self.duplicate_radius = duplicate_radius
        self.cone_id_counter = 0
        self._now = now_fn

    def _passes_promotion_bar(self, cone_data: Dict) -> bool:
        if cone_data['color'] == ConeColor.ORANGE:
            return (cone_data['confidence'] > self.ORANGE_CONFIDENCE_THRESHOLD and
                    cone_data['detections'] >= self.ORANGE_MIN_DETECTIONS)
        return (cone_data['confidence'] > self.confidence_threshold and
                cone_data['detections'] >= self.min_detections)

    def try_add_cone(self, cone_data: Dict) -> bool:
        """
        Promote a local-buffer cone to the global map, or refine the
        position of the matching cone already in the map.

        Args:
            cone_data: Dictionary with keys: x, y, z, color, confidence, detections

        Returns:
            True if a NEW cone was added; False if rejected or merged
            into an existing cone.
        """
        if not self._passes_promotion_bar(cone_data):
            return False

        # Already in the map? Refine its position instead of discarding.
        for existing in self.global_cones:
            if (existing['color'] == cone_data['color'] and
                math.hypot(existing['x'] - cone_data['x'],
                           existing['y'] - cone_data['y']) < self.duplicate_radius):
                a = self.REFINE_ALPHA
                existing['x'] = a * cone_data['x'] + (1 - a) * existing['x']
                existing['y'] = a * cone_data['y'] + (1 - a) * existing['y']
                existing['z'] = a * cone_data['z'] + (1 - a) * existing['z']
                existing['detections'] += cone_data['detections']
                existing['confidence'] = max(existing['confidence'],
                                             cone_data['confidence'])
                return False

        self.cone_id_counter += 1
        self.global_cones.append({
            'id': self.cone_id_counter,
            'x': cone_data['x'],
            'y': cone_data['y'],
            'z': cone_data['z'],
            'color': cone_data['color'],
            'confidence': cone_data['confidence'],
            'detections': cone_data['detections'],
            'added_timestamp': self._now(),
        })
        return True

    def get_global_map(self) -> List[Dict]:
        """Get copy of all cones in global map."""
        return self.global_cones.copy()

    def get_local_view(self, vehicle_pos: tuple, radius: float = 20.0) -> List[Dict]:
        """Get cones within radius of vehicle position."""
        veh_x, veh_y = vehicle_pos
        return [cone for cone in self.global_cones
                if math.hypot(cone['x'] - veh_x, cone['y'] - veh_y) <= radius]

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

    def __init__(self, max_size: int = 200, max_age: float = 6.0,
                 now_fn: Callable[[], float] = time.time):
        """
        Args:
            max_size: Maximum number of cones to track
            max_age: Drop a cone this many seconds after it was LAST seen
            now_fn: Clock returning seconds (inject the ROS clock from the node)
        """
        self.cones: List[Dict] = []
        self.max_size = max_size
        self.max_age = max_age
        self.cone_id_counter = 0
        self._now = now_fn

    def add_cone_detection(self, x: float, y: float, z: float,
                          color: int, confidence: float = 1.0):
        """
        Add or update a cone detection.

        Args:
            x, y, z: Cone position in world frame
            color: Cone color label (ConeColor enum value)
            confidence: Detector (YOLO) confidence for this detection, 0-1.
                Scales how much trust the detection earns: a 0.95 blue cone
                builds confidence twice as fast as a 0.5 maybe-cone.
        """
        current_time = self._now()

        # Distance from the car is unknown here (positions are world-frame),
        # so use distance from origin as a proxy only for the near-field
        # bonus; detector confidence carries the real signal.
        distance = math.sqrt(x * x + y * y + z * z)
        det_trust = 0.5 + 0.5 * max(0.0, min(1.0, confidence))

        matching_idx = self._find_matching_cone(x, y, color)

        if matching_idx is not None:
            # Update existing cone using exponential moving average
            cone = self.cones[matching_idx]
            cone['x'] = 0.3 * x + 0.7 * cone['x']
            cone['y'] = 0.3 * y + 0.7 * cone['y']
            cone['z'] = 0.3 * z + 0.7 * cone['z']

            confidence_gain = (0.2 if distance < 5.0 else
                               0.15 if distance < 10.0 else 0.1) * det_trust
            cone['confidence'] = min(1.0, cone['confidence'] + confidence_gain)
            cone['detections'] += 1
            cone['last_seen'] = current_time
        else:
            if distance < 3.0:
                initial_conf = 0.6
            elif distance < 8.0:
                initial_conf = 0.4
            else:
                initial_conf = 0.3
            initial_conf *= det_trust

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
        """Update confidence decay and prune stale/low-confidence cones."""
        current_time = self._now()

        # Decay confidence for unseen cones
        for cone in self.cones:
            if current_time - cone['last_seen'] > 0.1:
                cone['confidence'] = max(0.0, cone['confidence'] - 0.04)

        # Drop cones not re-seen recently (last_seen, NOT first_seen — a
        # cone that stays in view must not be evicted while still visible)
        self.cones = [cone for cone in self.cones
                     if (current_time - cone['last_seen'] < self.max_age and
                         cone['confidence'] > 0.15)]

        # Limit size (keep highest confidence)
        if len(self.cones) > self.max_size:
            self.cones.sort(key=lambda c: c['confidence'], reverse=True)
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
