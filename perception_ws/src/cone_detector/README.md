# Cone Detector Package

YOLOv8-based cone detection for autonomous racing perception.

## Overview

This package implements real-time cone detection using YOLOv8, publishing detected cone positions as ROS2 messages. It's designed to work with camera feeds from the EUFS simulation or real hardware.

## Usage

### Quick Start

1. Launch the cone detector:
   ```bash
   ros2 launch cone_detector cone_detector.launch.py
   ```

2. View debug images (if enabled):
   ```bash
   ros2 run rqt_image_view rqt_image_view /cone_detector/debug_image
   ```

3. Monitor cone detections:
   ```bash
   ros2 topic echo /cone_detections
   ```

### Configuration

The node accepts several parameters that can be set via launch file or command line:

```bash
ros2 launch cone_detector cone_detector.launch.py \
    model_path:=yolov8s.pt \
    confidence_threshold:=0.7 \
    camera_topic:=/camera/image_raw \
    publish_debug_image:=true
```

#### Parameters

- `model_path` (string, default: `yolov8n.pt`): Path to YOLO model file
- `confidence_threshold` (double, default: `0.5`): Minimum confidence for detections
- `camera_topic` (string, default: `/camera/image_raw`): Input camera topic
- `output_topic` (string, default: `/cone_detections`): Output topic for detections
- `publish_debug_image` (bool, default: `true`): Whether to publish debug images
- `debug_image_topic` (string, default: `/cone_detector/debug_image`): Debug image topic

## Topics

### Subscribed Topics

- `/camera/image_raw` (sensor_msgs/Image): Input camera images

### Published Topics

- `/cone_detections` (geometry_msgs/PointStamped): Detected cone positions
  - `point.x`: Pixel x-coordinate of cone center
  - `point.y`: Pixel y-coordinate of cone center
  - `point.z`: Detection confidence score
- `/cone_detector/debug_image` (sensor_msgs/Image): Debug visualization with bounding boxes

## Model Requirements

The cone detector uses YOLO models which are automatically downloaded by the ultralytics library. Supported models:

- `yolov8n.pt`: Nano model (fastest, least accurate)
- `yolov8s.pt`: Small model (balanced)
- `yolov8m.pt`: Medium model (more accurate)
- `yolov8l.pt`: Large model (high accuracy)
- `yolov8x.pt`: Extra large model (highest accuracy, slowest)

### Custom Models

To use a custom trained model:

1. Train your model using the ultralytics framework
2. Place the `.pt` file in your workspace
3. Set the `model_path` parameter to the full path

## Development

### File Structure

```
cone_detector/
├── cone_detector/
│   ├── __init__.py
│   └── cone_detector_node.py    # Main detection node
├── launch/
│   └── cone_detector.launch.py  # Launch configuration
├── test/                        # Unit tests
├── package.xml                  # Package metadata
└── setup.py                     # Python setup
```

### Extending the Detector

To add custom cone filtering or processing:

1. Modify `cone_detector_node.py`
2. Add custom logic in the `image_callback` method
3. Update the `publish_cone_detection` method for custom message formats

### Testing

```bash
# Run package tests
colcon test --packages-select cone_detector

# Run specific test
python3 -m pytest src/cone_detector/test/
```

## Troubleshooting

### Common Issues

1. **No detections appearing**:
   - Check camera topic is publishing: `ros2 topic list | grep camera`
   - Verify image format: `ros2 topic info /camera/image_raw`
   - Lower confidence threshold: `confidence_threshold:=0.3`

2. **Poor performance**:
   - Use a smaller model: `model_path:=yolov8n.pt`
   - Reduce image resolution in camera driver
   - Check CPU/GPU utilization

3. **Model download fails**:
   - Ensure internet connection
   - Check ultralytics installation: `pip show ultralytics`
   - Manually download model and specify full path

4. **Dependency errors**:
   - Ensure all ROS2 dependencies are installed
   - Source the workspace: `source install/setup.bash`
   - Rebuild: `colcon build --packages-select cone_detector`

### Debug Mode

Enable verbose logging:

```bash
ros2 launch cone_detector cone_detector.launch.py --ros-args --log-level DEBUG
```

## Integration with EUFS

```bash
# Terminal 1: Start EUFS simulation
ros2 launch eufs_launcher eufs_launcher.launch.py

# Terminal 2: Start cone detector
ros2 launch cone_detector cone_detector.launch.py camera_topic:=/camera/image_raw
```

## Future Improvements

- [ ] Convert pixel coordinates to world coordinates using camera calibration
- [ ] Add cone color classification (blue, yellow, orange)
- [ ] Implement cone tracking across frames
- [ ] Add distance estimation
- [ ] Support for stereo camera input
- [ ] Real-time model switching based on conditions