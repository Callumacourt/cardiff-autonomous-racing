# Perception on-car setup — FS-AI 2026 (native, no Docker)

Everything below runs ON the car machine, booted from this SSD.
All installers are pre-staged in `~/installers/` — no internet required
unless a step explicitly says so.

Already on this drive: ROS2 Humble, colcon, NVIDIA driver 580,
torch 2.13 (CUDA), ultralytics, OpenCV, ros_can (built, in
`~/cardiff-autonomous-racing/Control/`), perception source (current),
YOLO weights, zed-ros2-wrapper source (`~/zed_ws/src`).

---

## 1. YOLO weights path (one-time, needs sudo)

The detector loads weights from a fixed path:

```bash
sudo mkdir -p /workspace/perception_ws/models
sudo cp ~/cardiff-autonomous-racing/perception_ws/models/best.pt /workspace/perception_ws/models/best.pt
```

## 2. ZED wrapper dependencies (one-time, offline)

```bash
sudo dpkg -i ~/installers/wrapper_debs/*.deb
```

If dpkg reports missing dependencies, run `sudo apt -f install` (needs
internet) — but the common ones are pre-checked as already installed.

## 3. CUDA toolkit (only if the ZED SDK install asks for it)

Driver 580 is already installed — do NOT install the driver again.
If the SDK installer asks for CUDA, let it download over the car's WiFi
(toolkit only, no driver).

## 4. ZED SDK (one-time)

```bash
cd ~/installers
./ZED_SDK_Ubuntu22_cuda12.8_tensorrt10.9_v5.1.2.zstd.run
```

Accept defaults. Skip the AI-module downloads if offline — not needed
for our pipeline (we run our own YOLO).
(Fallback installer for SDK 4.2.5 is alongside it if 5.1.2 misbehaves;
if used, `git -C ~/zed_ws/src/zed-ros2-wrapper checkout humble-v4.2.5`.)

## 5. Build the ZED wrapper (one-time)

```bash
cd ~/zed_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install --cmake-args=-DCMAKE_BUILD_TYPE=Release
```

## 6. Build perception (one-time, and after any code change)

```bash
cd ~/cardiff-autonomous-racing/perception_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-select cone_detector cone_mapper landmark_slam
```

---

## 7. Launch (every boot)

Terminal A — camera:
```bash
source /opt/ros/humble/setup.bash && source ~/zed_ws/install/setup.bash
ros2 launch zed_wrapper zed_camera.launch.py camera_model:=zed2
```

Terminal B — vehicle interface (Control's node, publishes /ros_can/imu + /ros_can/twist):
```bash
source /opt/ros/humble/setup.bash && source ~/cardiff-autonomous-racing/Control/install/setup.bash
ros2 launch ros_can ros_can.launch.py
```

Confirm the real camera topic names first — they depend on wrapper config:
```bash
ros2 topic list | grep zed
```

Terminal C — perception (adjust topic names to what step above printed):
```bash
source /opt/ros/humble/setup.bash && source ~/cardiff-autonomous-racing/perception_ws/install/setup.bash
ros2 run cone_detector YOLO_cone_detector --ros-args \
  -p rgb_topic:=/zed/zed_node/rgb/image_rect_color \
  -p depth_topic:=/zed/zed_node/depth/depth_registered \
  -p camera_info_topic:=/zed/zed_node/left/camera_info &
ros2 run landmark_slam landmark_slam --ros-args -p imu_topic:=/ros_can/imu &
ros2 run cone_mapper cone_mapper &
```

Do NOT pass `use_sim_time` on the real car.

## 8. Health check

```bash
ros2 topic hz /zed/zed_node/rgb/image_rect_color   # camera alive
ros2 topic hz /cone_cloud/local                     # detector output
ros2 topic hz /odometry/slam                        # SLAM pose
ros2 topic echo /cone_map/local --once              # planner feed
```

If `/odometry/slam` position stays near zero while moving: no velocity
source — check `/ros_can/twist` is publishing (ros_can + CAN bus up).

## 9. Once the camera mount is measured

```bash
ros2 run landmark_slam landmark_slam --ros-args \
  -p imu_topic:=/ros_can/imu \
  -p camera_x_offset:=<metres forward of reference> \
  -p camera_y_offset:=<metres left of reference>
```

Full topic/format contract: `PERCEPTION_FORMAT.md` in this directory.

## 10. SKIDPAD mission (added 2026-07-16)

One command starts the whole mission stack (ros_can, ZED, perception,
skidpad driver):

```bash
bash ~/launch_skidpad_car.sh
```

Do NOT also run Control's cmd_node (`start_control.sh`) — it has no skidpad
branch, publishes competing /cmd messages, and spams mission_completed=False.

The skidpad driver (`scripts/skidpad_driver.py`) only sends commands when the
ADS-DV mission selector is on SKIDPAD (ami_state=12) and the car is in
AS_DRIVING. It anchors a regulation figure-8 (right circle 2 laps, then left
circle 2 laps, then exit) to the SLAM pose at the moment driving starts, so
**the car must be staged on the entry lane centreline, pointing straight at
the circle crossing point**, and perception must already be running (SLAM
pose valid) before the go signal.

Before running, confirm on the day and edit `~/launch_skidpad_car.sh`:
- `entry_length` — metres from the car's **SLAM reference point** (camera/base,
  not the nose) to the circle crossing / timekeeping line. Rules stage the
  foremost part of the vehicle 15 m before the line (D4.3.3), so this is
  15 m + nose-to-reference distance. Measure it; default 15.0.
- `exit_length`  — where the car aims to stop after the crossing. Rules
  (D4.3.6) require a full stop within 25 m or it's an Unsafe Stop = DNF;
  selftest shows ~0.9 m overshoot, so the default is 20.0 for margin. Do
  not raise it to 25.
- `target_speed` — start at 2.5 m/s; only raise after a clean run

The launch script now runs `sudo -v` first (CAN bring-up needs sudo and
runs in the background) — type the password when prompted at launch.

Offline sanity check (no ROS needed, prints PASS/FAIL):

```bash
python3 ~/cardiff-autonomous-racing/scripts/skidpad_driver.py --selftest
```

## 11. FULL AUTONOMOUS LAP — perception + planning + follower (added 2026-07-18)

The pipeline that lapped the EUFS sim, adapted for the car. It uses the ZED
camera end-to-end: ZED → GPU YOLO → cone_mapper + landmark_slam → path
planner (`/planned_path`) → pure-pursuit follower (`/cmd` to ros_can).

Before the day (offline, ~1 min):

```bash
~/cardiff-autonomous-racing/scripts/check_car_deps.sh
```

Every check must PASS. It verifies ROS, the NVIDIA driver, a real GPU
kernel run through torch (catches the wrong-CUDA-wheel problem), ultralytics,
numpy 1.x (2.x breaks cv_bridge), YOLO weights, ZED SDK + wrapper, the
perception/Control workspaces, and that the planner + follower import cleanly.

On the day:

```bash
~/cardiff-autonomous-racing/scripts/run_full_autonomous_lap_car.sh [laps] [speed_mps]
```

It re-runs the dependency check, stops any running `command_node`
(it publishes zero-commands on `/cmd` and would fight the follower),
starts ros_can if needed, brings up camera + perception via
`setup_real_car.sh`, starts the planner, waits for `/planned_path`, then
arms the follower in `--real-car` mode: **it never calls set_mission — select
the mission on the AMI panel**; the car drives when ros_can reports
AS:DRIVING. EBS/RES stops the car as normal; the follower also brakes itself
if SLAM goes quiet >0.5 s or the planner >2 s, and stops after [laps].

`scripts/run_full_autonomous_lap_car.sh stop` tears down follower, planner
and perception (leaves ros_can running).

First run: 2.0 m/s, one lap, walk the fallbacks like the skidpad procedure.
