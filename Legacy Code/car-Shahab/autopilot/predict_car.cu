#define DIM_X 9
#define DIM_CTR 2
#define MASS 2500.0f
#define GRAVITY 9.81f

__device__ float sign(float x)
{
    if (x >= 0.0)
{
    return 1.0;
}
    if (x < 0.0)
{
    return -1.0;
}
    return 0.0;
};

__device__ float clamp(float x, float a, float b)
{
    return max(a, min(b, x));
};


__device__ void advance_car(float const *Xin, float *Xout,
        float steering, float throttle_,
                float weight_transfer, float cg_height, float cg_to_front_axle, float cg_to_rear_axle,
                        float max_steering, float tire_grip, float corner_stiffness_front, float corner_stiffness_rear, float engine_force,
                                float roll_resistance, float air_resistance, float inertia, float ahdg_damping,
                                        float dt)
{
    // State X: [x, y, vx, vy, ax, ay, hdg, vhdg, ahdg]
            //           0  1   2   3   4   5    6     7     8
                    // Control
                            float speed = sqrt(Xin[2] * Xin[2] + Xin[3] * Xin[3]);
float speed_c = 0.0017268 * speed * speed - 0.0800304 * speed + 0.9791562;
float steering_angle = min(1.0, max(-1.0, steering)) * max_steering * speed_c;

float throttle = min(1.0, max(0.0, throttle_)) * engine_force;

float wheel_base = cg_to_front_axle + cg_to_rear_axle;
float weight_ratio_front = cg_to_rear_axle / wheel_base;
float weight_ratio_rear = cg_to_front_axle / wheel_base;

float sn = sin(Xin[6]); float cs = cos(Xin[6]);

// Get velocity and acceleration in local car coordinates
        float vxc = cs * Xin[2] + sn * Xin[3];
float vyc = cs * Xin[3] - sn * Xin[2];
float axc = cs * Xin[4] + sn * Xin[5];

// Weight on axles based on centre of gravity and weight shift due to forward/reverse acceleration
        float axle_weight_front = MASS * (weight_ratio_front * GRAVITY - weight_transfer * axc * cg_height / wheel_base);
float axle_weight_rear = MASS * (weight_ratio_rear * GRAVITY + weight_transfer * axc * cg_height / wheel_base);

/*  Resulting velocity of the wheels as result of the yaw rate of the car body.
v = yawrate * r where r is distance from axle to CG and heading_rate (angular velocity) in rad/s.
*/

        float yaw_speed_front = cg_to_front_axle * Xin[7];
float yaw_speed_rear = -cg_to_rear_axle * Xin[7];

// Calculate slip angles for front and rear wheels (a.k.a. alpha)
        float slip_angle_front = atan2(vyc + yaw_speed_front, fabs(vxc)) - sign(vxc) * steering_angle;
float slip_angle_rear = atan2(vyc + yaw_speed_rear, fabs(vxc));

float tire_grip_front = tire_grip;
// reduce rear grip when ebrake is on. (Disabled for now.)
        float tire_grip_rear = tire_grip; // *  (1.0 - self.ebrake * (1.0 - self.lockGrip));

float motion = min(1.0f, max(0.0f, (speed - 0.01) / (20.0 - 0.01)));
float friction_force_front_cy = clamp(-corner_stiffness_front * slip_angle_front * motion, -tire_grip_front, tire_grip_front) * axle_weight_front;
float friction_force_rear_cy = clamp(-corner_stiffness_rear * slip_angle_rear * motion, -tire_grip_rear, tire_grip_rear) * axle_weight_rear;

// Resulting force in local car coordinates. This is implemented as a RWD car only.
float traction_force_cx = throttle; // - brake * sign(vxc);
float traction_force_cy = 0;

// Resistance forces.
float drag_force_cx = -roll_resistance * vxc - air_resistance * vxc * abs(vxc);
float drag_force_cy = -roll_resistance * vyc - air_resistance * vyc * abs(vyc);

// Total force in car coordinates.
float total_force_cx = drag_force_cx + traction_force_cx;
float total_force_cy = drag_force_cy + traction_force_cy + cos(steering_angle) * friction_force_front_cy + friction_force_rear_cy;

// Acceleration in car coordinates.
axc = total_force_cx / MASS;
float ayc = total_force_cy / MASS;

// Acceleration in world coordinates.
Xout[4] = cs * axc - sn * ayc;
Xout[5] = sn * axc + cs * ayc;

// Integrate velocity.
Xout[2] = Xin[2] + Xout[4] * dt;
Xout[3] = Xin[3] + Xout[5] * dt;

// Integrate position.
Xout[0] = Xin[0] + Xout[2] * dt;
Xout[1] = Xin[1] + Xout[3] * dt;

// Calculate rotational forces.
float angular_torque = (friction_force_front_cy + traction_force_cy) * cg_to_front_axle - friction_force_rear_cy * cg_to_rear_axle;

Xout[8] = ahdg_damping * (angular_torque / (MASS * inertia)) + (1 - ahdg_damping) * Xin[8];
Xout[7] = Xin[7] + Xout[8] * dt;
Xout[6] = Xin[6] + Xout[7] * dt;
}

__global__ void predict_car(int K, int T, float const *X0, float const *ctr, float const *cfg, float dt, float *X_out)
{
    unsigned int k = blockIdx.x * blockDim.x + threadIdx.x;
    if (k >= K)
        return;

float weight_transfer = cfg[0];
float cg_height = cfg[1];
float cg_to_front_axle = cfg[2];
float cg_to_rear_axle = cfg[3];
float max_steering = cfg[4];
float tire_grip = cfg[5];
float corner_stiffness_front = cfg[6];
float corner_stiffness_rear = cfg[7];
float engine_force = cfg[8];
float roll_resistance = cfg[9];
float air_resistance = cfg[10];
float inertia = cfg[11];
float ahdg_damping = cfg[12];


    float *x_out = X_out + DIM_X * T * k;
    ctr += DIM_CTR * T * k;
    float const *x_in = X0;


    for (int t = 0; t < T; ++t)
    {
        float steering = ctr[0];
        float throttle = ctr[1];
        advance_car(x_in, x_out,
        steering, throttle,
                weight_transfer, cg_height, cg_to_front_axle, cg_to_rear_axle,
                        max_steering, tire_grip, corner_stiffness_front, corner_stiffness_rear, engine_force,
                                roll_resistance, air_resistance, inertia, ahdg_damping,
                                        dt);
        x_in = x_out;
        x_out += DIM_X;
        ctr += DIM_CTR;
    }
}
