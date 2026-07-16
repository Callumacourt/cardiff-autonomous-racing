"""
TUM Global Race Trajectory Optimization Wrapper
"""

import numpy as np
from typing import List, Tuple, Optional
import sys
import os

# Add TUM optimizer to path
tum_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'tum_optimizer')
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
        self.vehicle_width  = vehicle_width
        self.vehicle_length = vehicle_length
        self.tum_available  = TUM_AVAILABLE

    # ------------------------------------------------------------------
    # Cone ordering
    # ------------------------------------------------------------------

    def _chain_cones(self,
                     cones: List[Tuple[float, float]],
                     start_pos: Optional[Tuple[float, float]] = None
                     ) -> List[Tuple[float, float]]:
        """Order cones via nearest-neighbour chaining from start_pos.

        This correctly handles any track shape (straight, hairpin, figure-8)
        provided cone spacing > track width, which guarantees the chain always
        steps to the next same-side cone rather than jumping across the track.
        """
        if not cones:
            return []

        remaining = list(cones)

        if start_pos is not None:
            dists     = [np.hypot(c[0] - start_pos[0], c[1] - start_pos[1])
                         for c in remaining]
            first_idx = int(np.argmin(dists))
        else:
            first_idx = 0

        ordered = [remaining.pop(first_idx)]
        while remaining:
            last  = ordered[-1]
            dists = [np.hypot(c[0] - last[0], c[1] - last[1]) for c in remaining]
            ordered.append(remaining.pop(int(np.argmin(dists))))

        return ordered

    # ------------------------------------------------------------------
    # Reference track
    # ------------------------------------------------------------------

    def cones_to_reftrack(self,
                          left_cones:  List[Tuple[float, float]],
                          right_cones: List[Tuple[float, float]],
                          min_points:  int = 5,
                          start_pos:   Optional[Tuple[float, float]] = None
                          ) -> Optional[np.ndarray]:
        """Convert cone detections to reference track [x, y, w_tr_right, w_tr_left].

        Both cone sets are chained from start_pos so they progress in the same
        direction along the track, then paired by equal index.  A maximum width
        guard discards clearly mis-paired cones.
        """
        if len(left_cones) < min_points or len(right_cones) < min_points:
            return None

        left_sorted  = self._chain_cones(left_cones,  start_pos)
        right_sorted = self._chain_cones(right_cones, start_pos)

        n = min(len(left_sorted), len(right_sorted))
        max_half_width = 12.0

        reftrack = []
        for i in range(n):
            li = int(i * len(left_sorted)  / n)
            ri = int(i * len(right_sorted) / n)

            lx, ly = left_sorted[li]
            rx, ry = right_sorted[ri]

            cx = (lx + rx) / 2.0
            cy = (ly + ry) / 2.0

            w_left  = np.hypot(cx - lx, cy - ly)
            w_right = np.hypot(cx - rx, cy - ry)

            if w_left > max_half_width or w_right > max_half_width:
                continue

            reftrack.append([cx, cy, w_right, w_left])

        if len(reftrack) < 3:
            return None

        return np.array(reftrack)

    # ------------------------------------------------------------------
    # Trajectory optimisation
    # ------------------------------------------------------------------

    def optimize_trajectory(self,
                            reftrack:  np.ndarray,
                            opt_type:  str = 'mincurv',
                            start_pos: Optional[Tuple[float, float]] = None
                            ) -> Optional[np.ndarray]:
        """Optimize trajectory: returns [x, y, heading, curvature, velocity].

        Uses TUM trajectory_planning_helpers when available, otherwise falls
        back to a scipy B-spline smoother with boundary clamping.
        """
        if reftrack is None or len(reftrack) < 3:
            return None

        if not self.tum_available:
            return self._optimize_scipy(reftrack, start_pos=start_pos)

        try:
            reftrack_interp, normvec_normalized, a_interp, _, _ = \
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

            raceline = (reftrack_interp[:, :2]
                        + np.expand_dims(alpha_opt, axis=1) * normvec_normalized)

            coeffs_x_rl, coeffs_y_rl, _, _ = tph.calc_splines.calc_splines(
                path=np.column_stack((raceline, reftrack_interp[:, 2:]))
            )

            psi_rl, kappa_rl = tph.calc_head_curv_an.calc_head_curv_an(
                coeffs_x=coeffs_x_rl,
                coeffs_y=coeffs_y_rl,
                ind_spls=np.arange(len(coeffs_x_rl)),
                t_spls=np.zeros(len(coeffs_x_rl))
            )

            velocity = np.ones(len(raceline)) * 10.0
            result   = np.column_stack((raceline, psi_rl, kappa_rl, velocity))
            return self._align_to_start(result, start_pos)

        except Exception as e:
            print(f"TUM optimization failed: {e}")
            return None

    # ------------------------------------------------------------------
    # Scipy fallback
    # ------------------------------------------------------------------

    def _optimize_scipy(self,
                        reftrack:  np.ndarray,
                        start_pos: Optional[Tuple[float, float]] = None
                        ) -> Optional[np.ndarray]:
        """Scipy B-spline fallback optimizer.

        Pipeline:
          1. Fit a tightly smoothed spline through the reftrack centreline.
          2. Clamp every waypoint to within the track boundaries (vehicle
             clearance respected).
          3. Recompute heading and curvature from the clamped positions so
             the speed profile reflects the actual driven geometry.
        """
        from scipy.interpolate import splprep, splev

        cx = reftrack[:, 0].copy()
        cy = reftrack[:, 1].copy()

        if len(cx) < 4:
            return None

        arc_length = float(np.sum(np.hypot(np.diff(cx), np.diff(cy))))
        gap        = float(np.hypot(cx[-1] - cx[0], cy[-1] - cy[0]))
        is_closed  = arc_length > 0 and (gap / arc_length) < 0.10

        if is_closed and gap > 1e-6:
            cx = np.append(cx, cx[0])
            cy = np.append(cy, cy[0])

        # Small smoothing factor so the spline follows the centreline closely
        # without cutting corners.  Using s ≈ n keeps residuals tight while
        # still filtering measurement noise.
        s = max(float(len(cx)) * 0.8, 3.0)

        try:
            tck, _ = splprep([cx, cy], s=s, per=is_closed, k=3)
        except Exception as e:
            print(f"Scipy spline fitting failed: {e}")
            return None

        n_points = max(len(reftrack) * 4, 150)
        u = np.linspace(0, 1, n_points, endpoint=not is_closed)

        x_s, y_s = splev(u, tck)

        # --- Boundary clamping ------------------------------------------------
        xy_c = self._clamp_to_track(np.column_stack((x_s, y_s)), reftrack)
        x_c, y_c = xy_c[:, 0], xy_c[:, 1]

        # --- Recompute derivatives from clamped path --------------------------
        dx_c  = np.gradient(x_c)
        dy_c  = np.gradient(y_c)
        ddx_c = np.gradient(dx_c)
        ddy_c = np.gradient(dy_c)

        psi_c  = np.arctan2(dy_c, dx_c)
        denom  = np.maximum((dx_c ** 2 + dy_c ** 2) ** 1.5, 1e-8)
        kappa_c = (dx_c * ddy_c - dy_c * ddx_c) / denom

        v_max, v_min = 15.0, 3.0
        k_max    = max(float(np.max(np.abs(kappa_c))), 1e-6)
        velocity = v_max - (v_max - v_min) * (np.abs(kappa_c) / k_max)

        result = np.column_stack((x_c, y_c, psi_c, kappa_c, velocity))
        return self._align_to_start(result, start_pos)

    # ------------------------------------------------------------------
    # Boundary clamping
    # ------------------------------------------------------------------

    def _clamp_to_track(self,
                        pts_2d:   np.ndarray,
                        reftrack: np.ndarray) -> np.ndarray:
        """Project any out-of-bounds path points back inside the track.

        For each waypoint the nearest reftrack segment is found via a sequential
        window search (rather than a global argmin) so that the mapping stays
        coherent on non-convex and self-intersecting tracks such as figure-8.
        The signed cross-track offset is clamped to
        [-(w_right - clearance), (w_left - clearance)], then the point is
        translated purely in the normal direction so along-track position is
        preserved.
        """
        cx      = reftrack[:, 0]
        cy      = reftrack[:, 1]
        w_right = reftrack[:, 2]
        w_left  = reftrack[:, 3]
        n_rt    = len(cx)

        # Unit left-normals along the reftrack
        dx   = np.gradient(cx)
        dy   = np.gradient(cy)
        norm = np.maximum(np.sqrt(dx ** 2 + dy ** 2), 1e-8)
        nx   = -dy / norm
        ny   =  dx / norm

        clearance = self.vehicle_width / 2.0
        clamped   = pts_2d.copy()

        # Window size: each trajectory point maps to ~pts/reftrack ratio of the
        # reftrack.  Allow ±window indices so we don't jump to a distant segment.
        ratio  = max(len(pts_2d) / max(n_rt, 1), 1.0)
        window = max(6, int(round(ratio * 2)))

        prev_j = 0
        for i in range(len(pts_2d)):
            tx, ty = pts_2d[i]

            # Search a local window around the previous index (wraps for closed tracks)
            idxs  = [(prev_j + k) % n_rt for k in range(-window, window + 1)]
            dists = [np.hypot(cx[c] - tx, cy[c] - ty) for c in idxs]
            j     = idxs[int(np.argmin(dists))]
            prev_j = j

            # Signed cross-track offset (positive = left of centreline)
            cross = (tx - cx[j]) * nx[j] + (ty - cy[j]) * ny[j]

            safe_left  = max(0.0, w_left[j]  - clearance)
            safe_right = max(0.0, w_right[j] - clearance)

            clamped_cross = float(np.clip(cross, -safe_right, safe_left))

            if abs(clamped_cross - cross) > 1e-6:
                shift = clamped_cross - cross
                clamped[i, 0] = tx + shift * nx[j]
                clamped[i, 1] = ty + shift * ny[j]

        return clamped

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _align_to_start(trajectory: np.ndarray,
                        start_pos:  Optional[Tuple[float, float]]) -> np.ndarray:
        """Roll the trajectory so it begins at the point closest to start_pos."""
        if start_pos is None or len(trajectory) == 0:
            return trajectory

        dists     = np.hypot(trajectory[:, 0] - start_pos[0],
                             trajectory[:, 1] - start_pos[1])
        start_idx = int(np.argmin(dists))
        return np.roll(trajectory, -start_idx, axis=0)
