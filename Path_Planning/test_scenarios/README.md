# Path Planning Test Scenarios

This directory contains predefined test scenarios for the path planning GUI.

## Available Scenarios

### 1. straight_track.json
- Simple straight track with parallel cone boundaries
- Good for testing basic optimization and path smoothing
- 15 cone pairs
- Track width: 6m

### 2. chicane.json
- S-curve chicane with alternating left-right sections
- Tests path planning through complex curves
- 20 cone pairs
- Variable track width
- Includes start/finish orange cones

### 3. hairpin.json
- 180-degree hairpin turn
- Tests tight corner handling and path optimization
- Straight approach and exit sections
- Challenging for minimum time optimization
- Includes corner apex markers

### 4. complex_circuit.json
- Full racing circuit with multiple corner types
- Combination of fast sweepers and tight sections
- 22 cone pairs in closed loop
- Tests complete racing line optimization
- Multiple strategic points marked with orange cones

## Usage

1. Open the Path Planning GUI: `python3 path_planning_gui.py`
2. Click "Load Scenario" button
3. Navigate to `test_scenarios/` directory
4. Select a JSON file
5. Click "Run Optimization" to generate the racing line

## Creating Custom Scenarios

You can create your own scenarios by:

1. Using the GUI to place cones interactively
2. Clicking "Save Scenario" to export as JSON
3. Or manually editing JSON files following this format:

```json
{
  "scenario_name": "My Test Track",
  "left_cones": [[x1, y1], [x2, y2], ...],
  "right_cones": [[x1, y1], [x2, y2], ...],
  "orange_cones": [[x1, y1], [x2, y2], ...],
  "car_position": [x, y],
  "car_heading": 0.0,
  "vehicle_width": 1.5,
  "optimization_type": "mincurv"
}
```

## Coordinate System

- X-axis: Forward direction (m)
- Y-axis: Lateral direction (m)
- Origin: Start position
- Blue cones (label 0): Left track boundary
- Yellow cones (label 1): Right track boundary
- Orange cones (label 2): Special markers (start/finish, apex points)

## Tips for Scenario Design

1. **Minimum Cones**: Need at least 5 left and 5 right cones for optimization
2. **Spacing**: 2-4 meters between cones is typical for racing
3. **Track Width**: 4-8 meters typical for Formula Student tracks
4. **Closed Loops**: First and last cones should connect for circuits
5. **Orange Cones**: Use sparingly for key reference points
