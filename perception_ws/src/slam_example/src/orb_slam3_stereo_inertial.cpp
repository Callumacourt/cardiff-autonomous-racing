#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/image.hpp>
#include <sensor_msgs/msg/imu.hpp>
#include <nav_msgs/msg/odometry.hpp>
#include <geometry_msgs/msg/pose_stamped.hpp>
#include <string>

#include "slam_example/image_grabber_stereo_inertial.hpp"
#include "System.h"

int main(int argc, char **argv)
{
    rclcpp::init(argc, argv);
    auto node = rclcpp::Node::make_shared("orb_slam3_stereo_inertial");

    // --- Parameters ---
    const auto vocab_file        = node->declare_parameter<std::string>("vocab_path",         "");
    const auto settings_file     = node->declare_parameter<std::string>("config_path",        "");
    const auto left_topic        = node->declare_parameter<std::string>("left_image_topic",   "/zed/left/image_rect_color");
    const auto right_topic       = node->declare_parameter<std::string>("right_image_topic",  "/zed/right/image_rect_color");
    const auto imu_topic         = node->declare_parameter<std::string>("imu_topic",          "/zed/imu/data");
    const auto viewer_enabled    = node->declare_parameter<bool>       ("viewer",             true);
    const auto sync_timer_ms     = node->declare_parameter<int>        ("sync_timer_ms",      33);
    const auto odom_topic        = node->declare_parameter<std::string>("odom_topic",         "/odometry/slam");
    const auto child_frame_id    = node->declare_parameter<std::string>("child_frame_id",     "base_link");
    const auto parent_frame_id   = node->declare_parameter<std::string>("odom_frame_id",      "odom");
    const auto max_sync_delta    = node->declare_parameter<double>     ("max_sync_delta",     0.02);

    if (vocab_file.empty() || settings_file.empty()) {
        RCLCPP_FATAL(node->get_logger(), "vocab_path or config_path is empty — aborting");
        return 1;
    }

    RCLCPP_INFO(node->get_logger(), "vocab:    %s", vocab_file.c_str());
    RCLCPP_INFO(node->get_logger(), "config:   %s", settings_file.c_str());
    RCLCPP_INFO(node->get_logger(), "left:     %s", left_topic.c_str());
    RCLCPP_INFO(node->get_logger(), "right:    %s", right_topic.c_str());
    RCLCPP_INFO(node->get_logger(), "IMU:      %s", imu_topic.c_str());
    RCLCPP_INFO(node->get_logger(), "TF:       %s → %s", parent_frame_id.c_str(), child_frame_id.c_str());
    RCLCPP_INFO(node->get_logger(), "odom out: %s", odom_topic.c_str());
    RCLCPP_INFO(node->get_logger(), "viewer:   %s", viewer_enabled ? "on" : "off");

    // --- SLAM system ---
    ORB_SLAM3::System SLAM(vocab_file, settings_file, ORB_SLAM3::System::IMU_STEREO, viewer_enabled);

    // --- Publishers ---
    auto odom_pub = node->create_publisher<nav_msgs::msg::Odometry>(odom_topic, 10);
    auto pose_pub = node->create_publisher<geometry_msgs::msg::PoseStamped>("/car_pose", 10);

    // --- Image grabber ---
    auto grabber = std::make_shared<ImageGrabberInertial>(
        &SLAM,
        odom_pub,
        pose_pub,
        node,
        child_frame_id,
        parent_frame_id,
        max_sync_delta);

    grabber->SetupSubscriptions(
        left_topic, right_topic, imu_topic,
        static_cast<double>(sync_timer_ms));

    RCLCPP_INFO(node->get_logger(), "ORB-SLAM3 stereo-inertial node running.");
    rclcpp::spin(node);

    RCLCPP_INFO(node->get_logger(), "Shutting down SLAM...");
    SLAM.Shutdown();
    return 0;
}
