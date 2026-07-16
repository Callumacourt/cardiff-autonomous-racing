# TUM Global Race Trajectory Optimization Integration Guide

## Installation Steps

### 1. Add TUM repository
```bash
cd /home/dom/cardiff-autonomous-racing/Path_Planning
git submodule add https://github.com/TUMFTM/global_racetrajectory_optimization tum_optimizer
git submodule update --init --recursive
```

### 2. Install TUM dependencies
```bash
cd tum_optimizer
pip3 install -r requirements.txt
```

### 3. Install trajectory planning helpers
```bash
pip3 install trajectory-planning-helpers
```

## Key Dependencies from TUM
- trajectory_planning_helpers (TPH)
- casadi (for optimization)
- cvxpy
- quadprog
- scipy

## How it Works

The TUM optimizer requires:
1. **Reference track**: Centerline with left/right track widths `[x, y, w_tr_right, w_tr_left]`
2. **Vehicle parameters**: From config file (wheelbase, mass, etc.)
3. **GGV diagram**: Acceleration limits
4. **Optimization type**: 'mintime', 'mincurv', or 'shortest_path'

## Outputs
- **Optimal trajectory**: `[s, x, y, psi, kappa, vx, ax]`
- **Spline coefficients**: For smooth trajectory following
- **Lap time**: Total predicted lap time
