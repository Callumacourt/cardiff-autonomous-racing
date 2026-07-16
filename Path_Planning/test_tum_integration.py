#!/usr/bin/env python3
"""
Test script to verify TUM optimizer integration
Run inside Docker container or locally with dependencies installed
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from path_planning.tum_wrapper import TUMTrajectoryOptimizer
import numpy as np

def test_tum_optimizer():
    """Test TUM optimizer with sample cone data"""
    
    print("=" * 60)
    print("Testing TUM Trajectory Optimizer Integration")
    print("=" * 60)
    
    # Create optimizer
    optimizer = TUMTrajectoryOptimizer(vehicle_width=1.5, vehicle_length=2.5)
    
    if not optimizer.tum_available:
        print("❌ FAIL: TUM optimizer not available")
        print("   Check if trajectory_planning_helpers is installed")
        return False
    
    print("✅ TUM optimizer initialized")
    
    # Create sample cone data (straight track)
    print("\n📊 Creating sample cone data...")
    left_cones = [(i * 2.0, 2.5) for i in range(10)]
    right_cones = [(i * 2.0, -2.5) for i in range(10)]
    
    print(f"   Left cones (blue): {len(left_cones)}")
    print(f"   Right cones (yellow): {len(right_cones)}")
    
    # Test 1: Convert cones to reftrack
    print("\n🔄 Test 1: Converting cones to reftrack...")
    reftrack = optimizer.cones_to_reftrack(left_cones, right_cones, min_points=5)
    
    if reftrack is None:
        print("❌ FAIL: Could not create reftrack")
        return False
    
    print(f"✅ Reftrack created: {len(reftrack)} points")
    print(f"   Format: [x, y, w_tr_right, w_tr_left]")
    print(f"   Sample point: {reftrack[0]}")
    
    # Test 2: Optimize trajectory
    print("\n🚀 Test 2: Running trajectory optimization...")
    try:
        trajectory = optimizer.optimize_trajectory(reftrack, opt_type='mincurv')
        
        if trajectory is None:
            print("❌ FAIL: Optimization returned None")
            return False
        
        print(f"✅ Optimization successful!")
        print(f"   Trajectory points: {len(trajectory)}")
        print(f"   Format: [x, y, heading, curvature, velocity]")
        print(f"   Sample point: {trajectory[0]}")
        
        # Calculate statistics
        path_length = sum(
            np.hypot(trajectory[i+1, 0] - trajectory[i, 0],
                    trajectory[i+1, 1] - trajectory[i, 1])
            for i in range(len(trajectory) - 1)
        )
        max_curvature = np.max(np.abs(trajectory[:, 3]))
        
        print(f"\n📈 Trajectory Statistics:")
        print(f"   Path length: {path_length:.2f} m")
        print(f"   Max curvature: {max_curvature:.4f} rad/m")
        print(f"   Avg velocity: {np.mean(trajectory[:, 4]):.2f} m/s")
        
    except Exception as e:
        print(f"❌ FAIL: Optimization error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Simple centerline (fallback)
    print("\n🔄 Test 3: Testing fallback centerline...")
    centerline = optimizer.generate_centerline_simple(left_cones, right_cones)
    
    if not centerline:
        print("❌ FAIL: Could not generate simple centerline")
        return False
    
    print(f"✅ Simple centerline created: {len(centerline)} points")
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    print("\nThe TUM optimizer is working correctly.")
    print("You can now run the full ROS 2 system.")
    return True

if __name__ == '__main__':
    success = test_tum_optimizer()
    sys.exit(0 if success else 1)
