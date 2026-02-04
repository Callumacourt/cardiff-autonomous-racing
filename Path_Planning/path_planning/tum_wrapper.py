"""
TUM Global Race Trajectory Optimization Wrapper
"""

import numpy as np
from typing import List, Tuple, Optional
import sys
import os

# Add TUM optimizer to path
tum_path = os.path.join(os.path.dirname(__file__), 'tum_optimizer')
if os.path.exists(tum_path) and tum_path not in sys.path:
    sys.path.insert(0, tum_path)

try:
    import trajectory_planning_helpers as tph
    TUM_AVAILABLE = True
except ImportError:
    TUM_AVAILABLE = False


class TUMTrajectoryOptimizer:
    """Wrapper for TUM trajectory optimization"""
    
    def __init__(self, vehicle_width: float = 1.5, vehicle_length: float = 2.5):
        self.vehicle_width = vehicle_width
        self.vehicle_length = vehicle_length
        self.tum_available = TUM_AVAILABLE
        
    def cones_to_reftrack(self, 
                          left_cones: List[Tuple[float, float]], 
                          right_cones: List[Tuple[float, float]],
                          min_points: int = 5) -> Optional[np.ndarray]:
        """Convert cone detections to TUM reference track [x, y, w_tr_right, w_tr_left]"""
        if len(left_cones) < min_points or len(right_cones) < min_points:
            return None
            
        left_sorted = sorted(left_cones, key=lambda p: np.hypot(p[0], p[1]))
        right_sorted = sorted(right_cones, key=lambda p: np.hypot(p[0], p[1]))
        
        n_pairs = min(len(left_sorted), len(right_sorted))
        reftrack = []
        
        for i in range(n_pairs):
            left_x, left_y = left_sorted[i]
            right_x, right_y = right_sorted[i]
            
            center_x = (left_x + right_x) / 2.0
            center_y = (left_y + right_y) / 2.0
            
            w_tr_left = np.hypot(center_x - left_x, center_y - left_y)
            w_tr_right = np.hypot(center_x - right_x, center_y - right_y)
            
            reftrack.append([center_x, center_y, w_tr_right, w_tr_left])
        
        return np.array(reftrack)
    
    def optimize_trajectory(self, 
                           reftrack: np.ndarray,
                           opt_type: str = 'mincurv') -> Optional[np.ndarray]:
        """Optimize trajectory: returns [x, y, heading, curvature, velocity]"""
        if not self.tum_available or reftrack is None or len(reftrack) < 3:
            return None
            
        try:
            reftrack_interp, normvec_normalized, a_interp, coeffs_x, coeffs_y = \
                tph.prep_track.prep_track(
                    reftrack_imp=reftrack,
                    reg_smooth_opts={'k_reg': 3, 'eps_kappa': 1e-3},
                    stepsize_opts={'stepsize_prep': 1.0, 'stepsize_reg': 3.0},
                    debug=False,
                    min_width=self.vehicle_width * 1.5
                )
            
            if opt_type == 'shortest_path':
                alpha_opt = tph.opt_shortest_path.opt_shortest_path(
                    reftrack=reftrack_interp,
                    normvectors=normvec_normalized,
                    w_veh=self.vehicle_width,
                    print_debug=False
                )
            else:
                alpha_opt = tph.opt_min_curv.opt_min_curv(
                    reftrack=reftrack_interp,
                    normvectors=normvec_normalized,
                    A=a_interp,
                    kappa_bound=0.4,
                    w_veh=self.vehicle_width,
                    print_debug=False
                )[0]
            
            raceline = reftrack_interp[:, :2] + np.expand_dims(alpha_opt, axis=1) * normvec_normalized
            
            coeffs_x_rl, coeffs_y_rl, a_rl, normvec_rl = tph.calc_splines.calc_splines(
                path=np.column_stack((raceline, reftrack_interp[:, 2:]))
            )
            
            psi_rl, kappa_rl = tph.calc_head_curv_an.calc_head_curv_an(
                coeffs_x=coeffs_x_rl,
                coeffs_y=coeffs_y_rl,
                ind_spls=np.arange(len(coeffs_x_rl)),
                t_spls=np.zeros(len(coeffs_x_rl))
            )
            
            velocity = np.ones(len(raceline)) * 10.0  # 10 m/s default
            
            return np.column_stack((raceline, psi_rl, kappa_rl, velocity))
            
        except Exception:
            return None
