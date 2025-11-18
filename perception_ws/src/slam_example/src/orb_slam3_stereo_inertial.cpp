#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/image.hpp>
#include <sensor_msgs/msg/imu.hpp>
#include <nav_msgs/msg/odometry.hpp>
#include <string>

#include "slam_example/image_grabber_stereo_inertial.hpp"
#include "System.h"  // ORB-SLAM3 core system

int main(int argc, char **argv)
{
    // Initialise ROS2 node
    rclcpp::init(argc, argv);
    auto node = rclcpp::Node::make_shared("orb_slam3_stereo_inertial");

    // --- Parameter handling ---
    const auto vocab_file = node->declare_parameter<std::string>("vocab_path", "");
    const auto settings_file = node->declare_parameter<std::string>("config_path", "");
    const auto left_image_topic = node->declare_parameter<std::string>(
        "left_image_topic", "/zed/left/image_rect_color");
    const auto right_image_topic = node->declare_parameter<std::string>(
        "right_image_topic", "/zed/right/image_rect_color");
    const auto imu_topic = node->declare_parameter<std::string>(
        "imu_topic", "/zed/imu/data");
    const auto viewer_enabled = node->declare_parameter<bool>("viewer", true);
    const auto sync_timer_ms = node->declare_parameter<int>("sync_timer_ms", 33);
    const auto odom_topic = node->declare_parameter<std::string>("odom_topic", "/odometry/slam");
    const auto child_frame_id = node->declare_parameter<std::string>("child_frame_id", "base_link");
    const auto max_sync_delta = node->declare_parameter<double>("max_sync_delta", 0.02);

    if (vocab_file.empty() || settings_file.empty()) {
        RCLCPP_FATAL(node->get_logger(), "vocab_path or config_path is empty! Exiting...");
        return 1;
    }

    RCLCPP_INFO(node->get_logger(), "Vocab path: %s", vocab_file.c_str());
    RCLCPP_INFO(node->get_logger(), "Config path: %s", settings_file.c_str());
    RCLCPP_INFO(node->get_logger(), "Left image topic: %s", left_image_topic.c_str());
    RCLCPP_INFO(node->get_logger(), "Right image topic: %s", right_image_topic.c_str());
    RCLCPP_INFO(node->get_logger(), "IMU topic: %s", imu_topic.c_str());
    RCLCPP_INFO(node->get_logger(), "Viewer enabled: %s", viewer_enabled ? "true" : "false");
    RCLCPP_INFO(node->get_logger(), "Odometry topic: %s", odom_topic.c_str());
    RCLCPP_INFO(node->get_logger(), "Child frame: %s", child_frame_id.c_str());
    RCLCPP_INFO(node->get_logger(), "Max sync delta: %.4f s", max_sync_delta);

    // --- Create SLAM system ---
    ORB_SLAM3::System SLAM(
        vocab_file,
        settings_file,
        ORB_SLAM3::System::IMU_STEREO,
        viewer_enabled);

    // --- Create odometry publisher and grabber class ---
    auto odom_pub = node->create_publisher<nav_msgs::msg::Odometry>(odom_topic, 10);
    auto grabber = std::make_shared<ImageGrabberInertial>(
        &SLAM,
        odom_pub,
        node,
        child_frame_id,
        max_sync_delta);

    // --- Wire up subscriptions/timers via grabber ---
    grabber->SetupSubscriptions(
        left_image_topic,
        right_image_topic,
        imu_topic,
        static_cast<double>(sync_timer_ms));

    // --- Start ROS loop ---
    RCLCPP_INFO(node->get_logger(), "ORB-SLAM3 stereo-inertial node started.");
    rclcpp::spin(node);

    // --- Shutdown procedure ---
    RCLCPP_INFO(node->get_logger(), "Shutting down SLAM...");
    SLAM.Shutdown();
    //SLAM.SaveTrajectoryEuRoC("CameraTrajectory.txt");

    return 0;
}


