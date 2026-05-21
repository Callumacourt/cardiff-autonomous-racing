#ifndef IMAGE_GRABBER_STEREO_INERTIAL_H
#define IMAGE_GRABBER_STEREO_INERTIAL_H

#include <deque>
#include <mutex>
#include <string>
#include <vector>

#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/image.hpp>
#include <sensor_msgs/msg/imu.hpp>
#include <nav_msgs/msg/odometry.hpp>
#include <geometry_msgs/msg/pose_stamped.hpp>
#include <geometry_msgs/msg/transform_stamped.hpp>
#include <tf2_ros/transform_broadcaster.h>
#include <cv_bridge/cv_bridge.h>
#include <opencv2/core/core.hpp>
#include <GL/glew.h>

#include "System.h"

/// Handles stereo image and IMU synchronisation and feeds ORB-SLAM3.
/// Publishes:
///   - nav_msgs/Odometry on the configured odom_topic
///   - geometry_msgs/PoseStamped on /car_pose  (for path planner)
///   - TF transform  parent_frame → child_frame  (for RViz / tf2 tooling)
class ImageGrabberInertial {
public:
    ImageGrabberInertial(
        ORB_SLAM3::System* pSLAM,
        rclcpp::Publisher<nav_msgs::msg::Odometry>::SharedPtr odom_pub,
        rclcpp::Publisher<geometry_msgs::msg::PoseStamped>::SharedPtr pose_pub,
        rclcpp::Node::SharedPtr node,
        const std::string& child_frame,
        const std::string& parent_frame,
        double max_sync_delta);

    void SetupSubscriptions(const std::string& left_topic,
                            const std::string& right_topic,
                            const std::string& imu_topic,
                            double manual_sync_period_ms);

    void GrabStereo(const sensor_msgs::msg::Image::ConstSharedPtr& left,
                    const sensor_msgs::msg::Image::ConstSharedPtr& right);
    void GrabImu(const sensor_msgs::msg::Imu::SharedPtr msg);
    void GrabLeft(const sensor_msgs::msg::Image::ConstSharedPtr& msg);
    void GrabRight(const sensor_msgs::msg::Image::ConstSharedPtr& msg);
    void AttemptManualSync();

private:
    void TryTrackStereoIfReady();
    cv::Mat ConvertToGray(const sensor_msgs::msg::Image::ConstSharedPtr& img) const;
    std::vector<ORB_SLAM3::IMU::Point> ExtractImuMeasurementsLocked(double frame_time);
    void PublishPose(const Sophus::SE3f& se3, const rclcpp::Time& stamp);

    ORB_SLAM3::System* m_SLAM;
    rclcpp::Publisher<nav_msgs::msg::Odometry>::SharedPtr odom_pub_;
    rclcpp::Publisher<geometry_msgs::msg::PoseStamped>::SharedPtr pose_pub_;
    std::shared_ptr<tf2_ros::TransformBroadcaster> tf_broadcaster_;
    rclcpp::Node::SharedPtr node_;
    rclcpp::Logger logger_;
    std::string tf_frame_;    ///< child frame  (e.g. "base_link")
    std::string parent_frame_;///< parent frame (e.g. "odom")
    double max_sync_delta_ = 0.0;

    rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr left_subscription_;
    rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr right_subscription_;
    rclcpp::Subscription<sensor_msgs::msg::Imu>::SharedPtr imu_subscription_;
    rclcpp::TimerBase::SharedPtr manual_sync_timer_;

    sensor_msgs::msg::Image::ConstSharedPtr m_leftImage;
    sensor_msgs::msg::Image::ConstSharedPtr m_rightImage;
    std::deque<sensor_msgs::msg::Imu::SharedPtr> m_imuQueue;
    std::mutex m_mutex;
    std::deque<sensor_msgs::msg::Image::ConstSharedPtr> m_leftBuffer;
    std::deque<sensor_msgs::msg::Image::ConstSharedPtr> m_rightBuffer;
};

#endif // IMAGE_GRABBER_STEREO_INERTIAL_H
