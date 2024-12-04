function X = car_sim(X, ctr, cfg, dt)
%    X = [x, y, vx, vy, ax, ay, hdg, vhdg, ahdg]
x = X(1); y = X(2); vx = X(3); vy = X(4); ax = X(5); ay = X(6); hdg = X(7); vhdg = X(8); ahdg = X(9);

% mass = cfg(1);
mass = 2500;
weight_transfer = cfg(1);
cg_height = cfg(2);
cg_to_front_axle = cfg(3);
cg_to_rear_axle = cfg(4);
max_steering = cfg(5);
tire_grip = cfg(6);
corner_stiffness_front = cfg(7);
corner_stiffness_rear = cfg(8);
% brake_force = cfg(11);
engine_force = cfg(9);
roll_resistance = cfg(10);
air_resistance = cfg(11);
inertia = cfg(12);
ahdg_damping = cfg(13);

gravity = 9.81;
% Control
speed = sqrt(vx * vx + vy * vy);
speed_c = 0.0017268 * speed * speed - 0.0800304 * speed + 0.9791562;
steering_angle = min(1.0, max(-1.0, ctr(1))) * max_steering * speed_c;

throttle = min(1.0, max(0.0, ctr(2)));
% brake = ctr(3);

wheel_base = cg_to_front_axle + cg_to_rear_axle;
weight_ratio_front = cg_to_rear_axle / wheel_base;
weight_ratio_rear = cg_to_front_axle / wheel_base;

sn = sin(hdg); cs = cos(hdg);

% Get velocity and acceleration in local car coordinates
vxc = cs * vx + sn * vy;
vyc = cs * vy - sn * vx;
axc = cs * ax + sn * ay;
% ayc = cs * ay - sn * ax;

% Weight on axles based on centre of gravity and weight shift due to forward/reverse acceleration
axle_weight_front = mass * (weight_ratio_front * gravity - weight_transfer * axc * cg_height / wheel_base);
axle_weight_rear = mass * (weight_ratio_rear * gravity + weight_transfer * axc * cg_height / wheel_base);

% Resulting velocity of the wheels as result of the yaw rate of the car body.
% v = yawrate * r where r is distance from axle to CG and heading_rate (angular velocity) in rad/s.
yaw_speed_front = cg_to_front_axle * vhdg;
yaw_speed_rear = -cg_to_rear_axle * vhdg;

% Calculate slip angles for front and rear wheels (a.k.a. alpha)
slip_angle_front = atan2(vyc + yaw_speed_front, abs(vxc)) - sign(vxc) * steering_angle;
slip_angle_rear = atan2(vyc + yaw_speed_rear, abs(vxc));

tire_grip_front = tire_grip;
% reduce rear grip when ebrake is on. (Disabled for now.)
tire_grip_rear = tire_grip; % *  (1.0 - self.ebrake * (1.0 - self.lockGrip));

motion = min(1.0, max(0, (speed - 0.01) / (20.0 - 0.01)));
% motion
friction_force_front_cy = clamp(-corner_stiffness_front * slip_angle_front * motion, ...
    -tire_grip_front, tire_grip_front) * axle_weight_front;
friction_force_rear_cy = clamp(-corner_stiffness_rear * slip_angle_rear * motion, ...
    -tire_grip_rear, tire_grip_rear) * axle_weight_rear;

% Get amount of brake/throttle from our inputs.
% brake = 0; min(brake * brake_force, brake_force);
throttle = throttle * engine_force;

% Resulting force in local car coordinates. This is implemented as a RWD car only.
traction_force_cx = throttle; % - brake * sign(vxc);
traction_force_cy = 0;

% Resistance forces.
drag_force_cx = -roll_resistance * vxc - air_resistance * vxc * abs(vxc);
drag_force_cy = -roll_resistance * vyc - air_resistance * vyc * abs(vyc);

% Total force in car coordinates.
total_force_cx = drag_force_cx + traction_force_cx;
total_force_cy = drag_force_cy + traction_force_cy + ...
    cos(steering_angle) * friction_force_front_cy + friction_force_rear_cy;

% Acceleration in car coordinates.
axc = total_force_cx / mass;
ayc = total_force_cy / mass;

% Acceleration in world coordinates.
ax = cs * axc - sn * ayc;
ay = sn * axc + cs * ayc;

% Integrate velocity.
vx = vx + ax * dt;
vy = vy + ay * dt;

% Calculate rotational forces.
angular_torque = (friction_force_front_cy + traction_force_cy) * cg_to_front_axle - ...
    friction_force_rear_cy * cg_to_rear_axle;

ahdg = ahdg_damping * (angular_torque / (mass * inertia)) + (1 - ahdg_damping) * ahdg;
vhdg = vhdg + ahdg * dt;
hdg = hdg + vhdg * dt;

x = x + vx * dt;
y = y + vy * dt;

X = [x; y; vx; vy; ax; ay; hdg; vhdg; ahdg];

