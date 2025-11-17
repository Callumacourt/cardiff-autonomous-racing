#ifndef IMAGE_GRABBER_STEREO_INERTIAL_H
#define IMAGE_GRABBER_STEREO_INERTIAL_H

#include <deque>
#include <mutex>
#include <string>
#include <vector>

#include <cv_bridge/cv_bridge.h>
#include <nav_msgs/msg/odometry.hpp>
#include <rclcpp/rclcpp.hpp>
#include <rclcpp/time.hpp>
#include <sensor_msgs/msg/image.hpp>
#include <sensor_msgs/msg/imu.hpp>
#include <sensor_msgs/image_encodings.hpp>

#include "System.h"

/// \brief Handles stereo image and IMU synchronization and feeds them to ORB-SLAM3
class ImageGrabberInertial {
public:
    /// Constructor: stores pointer to the SLAM system and publishing context
    ImageGrabberInertial(ORB_SLAM3::System* pSLAM,
                         rclcpp::Publisher<nav_msgs::msg::Odometry>::SharedPtr odom_pub,
                         rclcpp::Node::SharedPtr node,
                         const std::string& child_frame,
                         double max_sync_delta = 0.02);

    /// \brief Sets up the ROS subscriptions/timers and keeps the handles alive
    void SetupSubscriptions(const std::string& left_topic,
                            const std::string& right_topic,
                            const std::string& imu_topic,
                            double manual_sync_period_ms);

    /// \brief Callback for synchronized stereo images
    void GrabStereo(const sensor_msgs::msg::Image::ConstSharedPtr& left,
                    const sensor_msgs::msg::Image::ConstSharedPtr& right);

    /// \brief Callback for IMU messages
    void GrabImu(const sensor_msgs::msg::Imu::SharedPtr msg);
    void GrabLeft(const sensor_msgs::msg::Image::ConstSharedPtr& msg);
    void GrabRight(const sensor_msgs::msg::Image::ConstSharedPtr& msg);
    void AttemptManualSync();  // called from a timer

private:
    /// \brief Triggers ORB-SLAM3 tracking if stereo and IMU data are ready
    void TryTrackStereoIfReady();

    cv::Mat ConvertToGray(const sensor_msgs::msg::Image::ConstSharedPtr& img) const;
    std::vector<ORB_SLAM3::IMU::Point> ExtractImuMeasurementsLocked(double frame_time);
    void PublishPose(const Sophus::SE3f& pose, const rclcpp::Time& stamp);

    ORB_SLAM3::System* m_SLAM;  ///< Pointer to SLAM system
    rclcpp::Publisher<nav_msgs::msg::Odometry>::SharedPtr odom_pub_;
    rclcpp::Node::SharedPtr node_;
    rclcpp::Logger logger_;
    std::string tf_frame_;
    double max_sync_delta_;
    sensor_msgs::msg::Image::ConstSharedPtr m_leftImage;  ///< Latest left image
    sensor_msgs::msg::Image::ConstSharedPtr m_rightImage; ///< Latest right image
    std::deque<sensor_msgs::msg::Imu::SharedPtr> m_imuQueue; ///< Buffered IMU messages
    std::mutex m_mutex; ///< Mutex for thread-safe access to shared data
    std::deque<sensor_msgs::msg::Image::ConstSharedPtr> m_leftBuffer;
    std::deque<sensor_msgs::msg::Image::ConstSharedPtr> m_rightBuffer;
    rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr left_subscription_;
    rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr right_subscription_;
    rclcpp::Subscription<sensor_msgs::msg::Imu>::SharedPtr imu_subscription_;
    rclcpp::TimerBase::SharedPtr manual_sync_timer_;
};

#endif // IMAGE_GRABBER_STEREO_INERTIAL_H

