#include "slam_example/image_grabber_stereo_inertial.hpp"

#include <Eigen/Geometry>
#include <chrono>
#include <opencv2/core/core.hpp>
#include <stdexcept>

constexpr size_t MAX_IMU_QUEUE_SIZE = 200;

ImageGrabberInertial::ImageGrabberInertial(
    ORB_SLAM3::System* pSLAM,
    rclcpp::Publisher<nav_msgs::msg::Odometry>::SharedPtr odom_pub,
    rclcpp::Publisher<geometry_msgs::msg::PoseStamped>::SharedPtr pose_pub,
    rclcpp::Node::SharedPtr node,
    const std::string& child_frame,
    const std::string& parent_frame,
    double max_sync_delta)
    : m_SLAM(pSLAM),
      odom_pub_(std::move(odom_pub)),
      pose_pub_(std::move(pose_pub)),
      node_(std::move(node)),
      logger_(node_ ? node_->get_logger() : rclcpp::get_logger("ImageGrabberInertial")),
      tf_frame_(child_frame),
      parent_frame_(parent_frame),
      max_sync_delta_(max_sync_delta),
      m_leftImage(nullptr),
      m_rightImage(nullptr)
{
    if (node_) {
        tf_broadcaster_ = std::make_shared<tf2_ros::TransformBroadcaster>(node_);
    }
}

void ImageGrabberInertial::SetupSubscriptions(const std::string& left_topic,
                                              const std::string& right_topic,
                                              const std::string& imu_topic,
                                              double manual_sync_period_ms)
{
    if (!node_) {
        throw std::runtime_error("ImageGrabberInertial: node pointer is null");
    }

    auto qos = rclcpp::SensorDataQoS();
    RCLCPP_INFO(logger_, "Subscribing stereo: left='%s'  right='%s'",
                left_topic.c_str(), right_topic.c_str());

    left_subscription_ = node_->create_subscription<sensor_msgs::msg::Image>(
        left_topic, qos,
        std::bind(&ImageGrabberInertial::GrabLeft, this, std::placeholders::_1));

    right_subscription_ = node_->create_subscription<sensor_msgs::msg::Image>(
        right_topic, qos,
        std::bind(&ImageGrabberInertial::GrabRight, this, std::placeholders::_1));

    RCLCPP_INFO(logger_, "Subscribing IMU: '%s'", imu_topic.c_str());
    imu_subscription_ = node_->create_subscription<sensor_msgs::msg::Imu>(
        imu_topic, rclcpp::SensorDataQoS(),
        std::bind(&ImageGrabberInertial::GrabImu, this, std::placeholders::_1));

    const auto period = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::duration<double, std::milli>(manual_sync_period_ms));

    manual_sync_timer_ = node_->create_wall_timer(
        period, std::bind(&ImageGrabberInertial::AttemptManualSync, this));

    RCLCPP_INFO(logger_, "Manual sync timer: %.1f ms  |  TF: %s → %s",
                manual_sync_period_ms, parent_frame_.c_str(), tf_frame_.c_str());
}

void ImageGrabberInertial::GrabStereo(
    const sensor_msgs::msg::Image::ConstSharedPtr& left,
    const sensor_msgs::msg::Image::ConstSharedPtr& right)
{
    {
        std::lock_guard<std::mutex> lock(m_mutex);
        m_leftImage  = left;
        m_rightImage = right;
    }
    TryTrackStereoIfReady();
}

void ImageGrabberInertial::GrabLeft(const sensor_msgs::msg::Image::ConstSharedPtr& msg)
{
    std::lock_guard<std::mutex> lock(m_mutex);
    m_leftBuffer.push_back(msg);
    if (m_leftBuffer.size() > 30) m_leftBuffer.pop_front();
}

void ImageGrabberInertial::GrabRight(const sensor_msgs::msg::Image::ConstSharedPtr& msg)
{
    std::lock_guard<std::mutex> lock(m_mutex);
    m_rightBuffer.push_back(msg);
    if (m_rightBuffer.size() > 30) m_rightBuffer.pop_front();
}

void ImageGrabberInertial::AttemptManualSync()
{
    sensor_msgs::msg::Image::ConstSharedPtr left, right;
    {
        std::lock_guard<std::mutex> lock(m_mutex);
        while (!m_leftBuffer.empty() && !m_rightBuffer.empty()) {
            const double t_l = rclcpp::Time(m_leftBuffer.front()->header.stamp).seconds();
            const double t_r = rclcpp::Time(m_rightBuffer.front()->header.stamp).seconds();
            const double dt  = t_l - t_r;

            if (std::abs(dt) < max_sync_delta_) {
                left  = m_leftBuffer.front();  m_leftBuffer.pop_front();
                right = m_rightBuffer.front(); m_rightBuffer.pop_front();
                break;
            }
            if (dt < 0) m_leftBuffer.pop_front();
            else        m_rightBuffer.pop_front();
        }
        if (left && right) { m_leftImage = left; m_rightImage = right; }
    }
    if (left && right) TryTrackStereoIfReady();
}

void ImageGrabberInertial::GrabImu(const sensor_msgs::msg::Imu::SharedPtr imu)
{
    std::lock_guard<std::mutex> lock(m_mutex);
    if (m_imuQueue.size() > MAX_IMU_QUEUE_SIZE) m_imuQueue.pop_front();
    m_imuQueue.push_back(imu);
}

void ImageGrabberInertial::TryTrackStereoIfReady()
{
    sensor_msgs::msg::Image::ConstSharedPtr left, right;
    {
        std::lock_guard<std::mutex> lock(m_mutex);
        if (!m_leftImage || !m_rightImage) return;
        left  = m_leftImage;
        right = m_rightImage;
    }

    cv::Mat imLeft  = ConvertToGray(left);
    cv::Mat imRight = ConvertToGray(right);
    if (imLeft.empty() || imRight.empty()) {
        RCLCPP_WARN(logger_, "Converted stereo images are empty");
        return;
    }

    const double tframe = rclcpp::Time(left->header.stamp).seconds();
    std::vector<ORB_SLAM3::IMU::Point> imu_measurements;
    {
        std::lock_guard<std::mutex> lock(m_mutex);
        imu_measurements = ExtractImuMeasurementsLocked(tframe);
    }

    if (imu_measurements.empty()) {
        RCLCPP_WARN(logger_, "No IMU data for stereo frame t=%.6f", tframe);
        return;
    }

    Sophus::SE3f pose;
    try {
        pose = m_SLAM->TrackStereo(imLeft, imRight, tframe, imu_measurements);
    } catch (const std::exception& e) {
        RCLCPP_ERROR(logger_, "SLAM tracking exception: %s", e.what());
        return;
    }

    PublishPose(pose, left->header.stamp);

    {
        std::lock_guard<std::mutex> lock(m_mutex);
        m_leftImage.reset();
        m_rightImage.reset();
    }
}

cv::Mat ImageGrabberInertial::ConvertToGray(
    const sensor_msgs::msg::Image::ConstSharedPtr& img) const
{
    try {
        return cv_bridge::toCvCopy(img, sensor_msgs::image_encodings::MONO8)->image;
    } catch (const cv_bridge::Exception& e) {
        RCLCPP_ERROR(logger_, "cv_bridge error: %s", e.what());
        return cv::Mat();
    }
}

std::vector<ORB_SLAM3::IMU::Point>
ImageGrabberInertial::ExtractImuMeasurementsLocked(double frame_time)
{
    constexpr double MAX_IMU_DELAY = 0.5;
    std::vector<ORB_SLAM3::IMU::Point> out;

    while (!m_imuQueue.empty()) {
        const auto imu  = m_imuQueue.front();
        const double ts = rclcpp::Time(imu->header.stamp).seconds();
        if (ts > frame_time + MAX_IMU_DELAY) break;

        out.emplace_back(
            cv::Point3f(imu->linear_acceleration.x,
                        imu->linear_acceleration.y,
                        imu->linear_acceleration.z),
            cv::Point3f(imu->angular_velocity.x,
                        imu->angular_velocity.y,
                        imu->angular_velocity.z),
            ts);
        m_imuQueue.pop_front();
    }
    return out;
}

void ImageGrabberInertial::PublishPose(const Sophus::SE3f& se3, const rclcpp::Time& stamp)
{
    const Eigen::Vector3f    t = se3.translation();
    const Eigen::Quaternionf q(se3.rotationMatrix());

    // --- Odometry ---
    if (odom_pub_) {
        nav_msgs::msg::Odometry odom;
        odom.header.stamp    = stamp;
        odom.header.frame_id = parent_frame_;
        odom.child_frame_id  = tf_frame_;
        odom.pose.pose.position.x    = t.x();
        odom.pose.pose.position.y    = t.y();
        odom.pose.pose.position.z    = t.z();
        odom.pose.pose.orientation.x = q.x();
        odom.pose.pose.orientation.y = q.y();
        odom.pose.pose.orientation.z = q.z();
        odom.pose.pose.orientation.w = q.w();
        odom_pub_->publish(odom);
    }

    // --- TF broadcast: parent_frame → base_link ---
    if (tf_broadcaster_) {
        geometry_msgs::msg::TransformStamped tf_msg;
        tf_msg.header.stamp    = stamp;
        tf_msg.header.frame_id = parent_frame_;
        tf_msg.child_frame_id  = tf_frame_;
        tf_msg.transform.translation.x = t.x();
        tf_msg.transform.translation.y = t.y();
        tf_msg.transform.translation.z = t.z();
        tf_msg.transform.rotation.x = q.x();
        tf_msg.transform.rotation.y = q.y();
        tf_msg.transform.rotation.z = q.z();
        tf_msg.transform.rotation.w = q.w();
        tf_broadcaster_->sendTransform(tf_msg);
    }

    // --- PoseStamped on /car_pose ---
    if (pose_pub_) {
        geometry_msgs::msg::PoseStamped ps;
        ps.header.stamp    = stamp;
        ps.header.frame_id = parent_frame_;
        ps.pose.position.x    = t.x();
        ps.pose.position.y    = t.y();
        ps.pose.position.z    = t.z();
        ps.pose.orientation.x = q.x();
        ps.pose.orientation.y = q.y();
        ps.pose.orientation.z = q.z();
        ps.pose.orientation.w = q.w();
        pose_pub_->publish(ps);
    }
}
