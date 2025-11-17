#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/image.hpp>
#include <sensor_msgs/msg/imu.hpp>
#include <nav_msgs/msg/odometry.hpp>

#include "slam_example/image_grabber_stereo_inertial.hpp"
#include "System.h"  // ORB-SLAM3 core system

int main(int argc, char **argv)
{
    // Initialise ROS2 node
    rclcpp::init(argc, argv);
    auto node = rclcpp::Node::make_shared("orb_slam3_stereo_inertial");

    // --- Parameter handling ---
    const std::string vocab_file = node->declare_parameter<std::string>("vocab_path", "");
    const std::string settings_file = node->declare_parameter<std::string>("config_path", "");
    const std::string left_topic = node->declare_parameter<std::string>(
        "left_topic", "/zed/left/image_rect_color");
    const std::string right_topic = node->declare_parameter<std::string>(
        "right_topic", "/zed/right/image_rect_color");
    const std::string imu_topic = node->declare_parameter<std::string>(
        "imu_topic", "/camera/imu/data");
    const std::string camera_frame = node->declare_parameter<std::string>(
        "camera_frame", "camera_link");
    const double manual_sync_period_ms = node->declare_parameter<double>(
        "manual_sync_period_ms", 33.0);
    const double stereo_sync_tolerance = node->declare_parameter<double>(
        "stereo_sync_tolerance", 0.02);

    if (vocab_file.empty() || settings_file.empty()) {
        RCLCPP_FATAL(node->get_logger(), "vocab_path or config_path is empty! Exiting...");
        return 1;
    }

    RCLCPP_INFO(node->get_logger(), "Vocab path: %s", vocab_file.c_str());
    RCLCPP_INFO(node->get_logger(), "Config path: %s", settings_file.c_str());

    // --- Create SLAM system ---
    ORB_SLAM3::System SLAM(vocab_file, settings_file, ORB_SLAM3::System::IMU_STEREO, true);

    // --- Create grabber class ---
    auto odom_pub = node->create_publisher<nav_msgs::msg::Odometry>("/odometry/slam", 10);
    auto grabber = std::make_shared<ImageGrabberInertial>(
        &SLAM, odom_pub, node, camera_frame, stereo_sync_tolerance);

    grabber->SetupSubscriptions(left_topic, right_topic, imu_topic, manual_sync_period_ms);

    // --- Start ROS loop ---
    RCLCPP_INFO(node->get_logger(), "ORB-SLAM3 stereo-inertial node started.");
    rclcpp::spin(node);

    // --- Shutdown procedure ---
    RCLCPP_INFO(node->get_logger(), "Shutting down SLAM...");
    SLAM.Shutdown();
    //SLAM.SaveTrajectoryEuRoC("CameraTrajectory.txt");

    return 0;
}


