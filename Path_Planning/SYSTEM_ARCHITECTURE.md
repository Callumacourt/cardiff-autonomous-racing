# Path Planning System Architecture

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    Cardiff Autonomous Racing - Path Planning                  ║
╚══════════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────────┐
│                              PRODUCTION SYSTEM                               │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────┐         ┌──────────────┐         ┌──────────────┐
    │  Perception  │────────▶│Path Planning │────────▶│   Control    │
    │   (YOLO)     │         │   (TUM Opt)  │         │              │
    └──────────────┘         └──────────────┘         └──────────────┘
           │                        │                        │
    /detected_cones           /planned_path            /control_cmd
           │                        │                        │
    x,y,z,label              nav_msgs/Path             velocity, steering
    per line                 waypoints                 commands


┌─────────────────────────────────────────────────────────────────────────────┐
│                           TESTING & DEVELOPMENT                              │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌────────────────────────────────────────────────────────────────┐
    │                    PATH PLANNING GUI                           │
    │                  (path_planning_gui.py)                        │
    │                                                                │
    │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
    │  │   Scenario   │  │Interactive   │  │     TUM      │       │
    │  │  Selection   │  │Cone Placement│  │ Optimization │       │
    │  └──────────────┘  └──────────────┘  └──────────────┘       │
    │                                                                │
    │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
    │  │Visualization │  │ Statistics & │  │     Save/    │       │
    │  │   Display    │  │   Metrics    │  │     Load     │       │
    │  └──────────────┘  └──────────────┘  └──────────────┘       │
    │                                                                │
    │  ┌──────────────────────────────────────────────────────┐    │
    │  │          Optional ROS 2 Integration                   │    │
    │  │  • Publish test cones to /detected_cones              │    │
    │  │  • Publish test paths to /planned_path                │    │
    │  │  • Validate integration with real system              │    │
    │  └──────────────────────────────────────────────────────┘    │
    └────────────────────────────────────────────────────────────────┘
                                  │
                     ┌────────────┼────────────┐
                     ▼            ▼            ▼
              ┌──────────┐ ┌──────────┐ ┌──────────┐
              │ Test     │ │  GUI     │ │  Plot    │
              │Scenarios │ │  Guide   │ │ Exports  │
              │  (JSON)  │ │   (MD)   │ │(PNG/PDF) │
              └──────────┘ └──────────┘ └──────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                            CORE COMPONENTS                                   │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌────────────────────────────────────────────────────────┐
    │            TUM Trajectory Optimizer                     │
    │         (path_planning/tum_wrapper.py)                 │
    │                                                         │
    │  Input:  Left/Right cone positions                     │
    │          ↓                                              │
    │  Process: Generate reference track                     │
    │          [x, y, w_tr_right, w_tr_left]                │
    │          ↓                                              │
    │  Optimize: Min curvature / Shortest path              │
    │          ↓                                              │
    │  Output: [x, y, heading, curvature, velocity]         │
    └────────────────────────────────────────────────────────┘
                              │
                              ▼
    ┌────────────────────────────────────────────────────────┐
    │   TUM Global Race Trajectory Optimization              │
    │        (tum_optimizer/ submodule)                      │
    │                                                         │
    │  • trajectory_planning_helpers                         │
    │  • CasADi optimization                                 │
    │  • Spline interpolation                                │
    │  • Vehicle dynamics model                              │
    └────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA FLOW - GUI MODE                               │
└─────────────────────────────────────────────────────────────────────────────┘

    User Interaction
         │
         ▼
    ┌─────────────────┐
    │  Click to Place │
    │      Cones      │
    └─────────────────┘
         │
         ▼
    ┌─────────────────┐      ┌──────────────────┐
    │  Store in Lists │─────▶│  Update Plot     │
    │  - left_cones   │      │  - Blue squares  │
    │  - right_cones  │      │  - Yellow squares│
    │  - orange_cones │      └──────────────────┘
    └─────────────────┘
         │
         ▼
    ┌─────────────────┐
    │ Run Optimization│
    │     Button      │
    └─────────────────┘
         │
         ▼
    ┌─────────────────────────────────┐
    │  TUMTrajectoryOptimizer         │
    │  1. cones_to_reftrack()         │
    │  2. optimize_trajectory()       │
    └─────────────────────────────────┘
         │
         ▼
    ┌─────────────────────────────────┐      ┌────────────────┐
    │  Optimized Trajectory Array     │─────▶│  Visualize:    │
    │  [x, y, heading, κ, velocity]   │      │  - Green line  │
    └─────────────────────────────────┘      │  - Vel heatmap │
         │                                    └────────────────┘
         ▼
    ┌─────────────────────────────────┐      ┌────────────────┐
    │  Calculate Statistics           │─────▶│  Display:      │
    │  - Path length                  │      │  - Text panel  │
    │  - Max curvature                │      │  - Metrics     │
    │  - Avg velocity                 │      └────────────────┘
    └─────────────────────────────────┘
         │
         ▼
    ┌─────────────────────────────────┐
    │  Optional: Publish to ROS 2     │
    │  - /detected_cones              │
    │  - /planned_path                │
    └─────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                       FILE STRUCTURE                                         │
└─────────────────────────────────────────────────────────────────────────────┘

Path_Planning/
│
├── path_planning_gui.py          ← 🆕 MAIN GUI APPLICATION
├── run_gui.sh                    ← 🆕 Linux/WSL launcher
├── run_gui.bat                   ← 🆕 Windows launcher
│
├── GUI_GUIDE.md                  ← 🆕 Complete user guide
├── GUI_IMPLEMENTATION.md         ← 🆕 Implementation summary
├── pathPlanningREADME.md         ← ✏️  Updated with GUI docs
│
├── test_scenarios/               ← 🆕 Test scenario library
│   ├── README.md                 ← 🆕 Scenarios documentation
│   ├── straight_track.json       ← 🆕 Basic track
│   ├── chicane.json              ← 🆕 S-curve
│   ├── hairpin.json              ← 🆕 180° corner
│   └── complex_circuit.json      ← 🆕 Full circuit
│
├── path_planning/                ← Existing module
│   ├── __init__.py
│   ├── integration.py            ← ROS 2 node
│   └── tum_wrapper.py            ← TUM optimizer wrapper
│
├── tum_optimizer/                ← Git submodule
├── launch/
│   └── launch.py
├── package.xml
├── setup.py
└── requirements.txt


┌─────────────────────────────────────────────────────────────────────────────┐
│                         TESTING WORKFLOWS                                    │
└─────────────────────────────────────────────────────────────────────────────┘

WORKFLOW 1: Quick Visual Test
─────────────────────────────
./run_gui.sh → Select Scenario → Run Optimization → View Results


WORKFLOW 2: Custom Scenario Design
───────────────────────────────────
Open GUI → Place Cones Manually → Optimize → Save JSON → Export Plot


WORKFLOW 3: ROS Integration Test
─────────────────────────────────
GUI: Load Scenario + Enable ROS + Publish Cones
  ↓
Path Planner Node: Subscribe + Optimize + Publish Path
  ↓
GUI or RViz: Visualize Result


WORKFLOW 4: Parameter Tuning
─────────────────────────────
Load Scenario → Adjust Vehicle Width → Optimize → Compare Results
                  (Repeat with different widths)


WORKFLOW 5: Batch Testing
──────────────────────────
For each scenario in test_scenarios/:
    Load → Optimize → Export Plot → Save Metrics
Generate comparison report


┌─────────────────────────────────────────────────────────────────────────────┐
│                      QUICK REFERENCE                                         │
└─────────────────────────────────────────────────────────────────────────────┝

Launch:          ./run_gui.sh  or  python3 path_planning_gui.py
Documentation:   GUI_GUIDE.md
Scenarios:       test_scenarios/*.json
Dependencies:    numpy, matplotlib, tkinter
Optional:        trajectory-planning-helpers, rclpy

Cone Colors:     🔵 Blue = Left    🟡 Yellow = Right    🔴 Orange = Markers
Path:            🟢 Green line with velocity heatmap
Car:             🟣 Purple arrow

Min Requirements: 5 left cones + 5 right cones
Track Width:     4-8 meters typical
Cone Spacing:    2-5 meters typical
```
