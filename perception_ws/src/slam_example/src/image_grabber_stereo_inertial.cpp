#include "slam_example/image_grabber_stereo_inertial.hpp"

#include <Eigen/Geometry>
#include <chrono>
#include <opencv2/core/core.hpp>
#include <stdexcept>

/// Max size of IMU queue to prevent unbounded growth
constexpr size_t MAX_IMU_QUEUE_SIZE = 200;

ImageGrabberInertial::ImageGrabberInertial(ORB_SLAM3::System* pSLAM,
                                           rclcpp::Publisher<nav_msgs::msg::Odometry>::SharedPtr odom_pub,
                                           rclcpp::Node::SharedPtr node,
                                           const std::string& child_frame,
                                           double max_sync_delta)
    : m_SLAM(pSLAM),
      odom_pub_(std::move(odom_pub)),
      node_(std::move(node)),
      logger_(node_ ? node_->get_logger() : rclcpp::get_logger("ImageGrabberInertial")),
      tf_frame_(child_frame),
      max_sync_delta_(max_sync_delta),
      m_leftImage(nullptr),
      m_rightImage(nullptr)
{}

void ImageGrabberInertial::SetupSubscriptions(const std::string& left_topic,
                                              const std::string& right_topic,
                                              const std::string& imu_topic,
                                              double manual_sync_period_ms)
{
    if (!node_) {
        throw std::runtime_error("ImageGrabberInertial: node pointer is null");
    }

    auto qos = rclcpp::SensorDataQoS();
    RCLCPP_INFO(logger_, "Subscribing to stereo topics: left='%s', right='%s'", left_topic.c_str(), right_topic.c_str());
    left_subscription_ = node_->create_subscription<sensor_msgs::msg::Image>(
        left_topic, qos,
        std::bind(&ImageGrabberInertial::GrabLeft, this, std::placeholders::_1));

    right_subscription_ = node_->create_subscription<sensor_msgs::msg::Image>(
        right_topic, qos,
        std::bind(&ImageGrabberInertial::GrabRight, this, std::placeholders::_1));

    RCLCPP_INFO(logger_, "Subscribing to IMU topic: '%s'", imu_topic.c_str());
    imu_subscription_ = node_->create_subscription<sensor_msgs::msg::Imu>(
        imu_topic, rclcpp::SensorDataQoS(),
        std::bind(&ImageGrabberInertial::GrabImu, this, std::placeholders::_1));

    const auto manual_sync_duration = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::duration<double, std::milli>(manual_sync_period_ms));

    manual_sync_timer_ = node_->create_wall_timer(
        manual_sync_duration,
        std::bind(&ImageGrabberInertial::AttemptManualSync, this));

    RCLCPP_INFO(logger_, "Manual sync timer running every %.2f ms", manual_sync_period_ms);
}

/// Stereo image callback, called when left and right images are approximately synchronized
void ImageGrabberInertial::GrabStereo(
    const sensor_msgs::msg::Image::ConstSharedPtr &left,
    const sensor_msgs::msg::Image::ConstSharedPtr &right)
{
    {
        std::lock_guard<std::mutex> lock(m_mutex);
        m_leftImage = left;
        m_rightImage = right;
    }
    TryTrackStereoIfReady();
}

void ImageGrabberInertial::GrabLeft(const sensor_msgs::msg::Image::ConstSharedPtr& msg) {
    std::lock_guard<std::mutex> lock(m_mutex);
    m_leftBuffer.push_back(msg);
    if (m_leftBuffer.size() > 30) m_leftBuffer.pop_front();
}

void ImageGrabberInertial::GrabRight(const sensor_msgs::msg::Image::ConstSharedPtr& msg) {
    std::lock_guard<std::mutex> lock(m_mutex);
    m_rightBuffer.push_back(msg);
    if (m_rightBuffer.size() > 30) m_rightBuffer.pop_front();
}

void ImageGrabberInertial::AttemptManualSync() {
    sensor_msgs::msg::Image::ConstSharedPtr left;
    sensor_msgs::msg::Image::ConstSharedPtr right;

    {
        std::lock_guard<std::mutex> lock(m_mutex);
        while (!m_leftBuffer.empty() && !m_rightBuffer.empty()) {
            const double t_left = rclcpp::Time(m_leftBuffer.front()->header.stamp).seconds();
            const double t_right = rclcpp::Time(m_rightBuffer.front()->header.stamp).seconds();
            const double dt = t_left - t_right;

            if (std::abs(dt) < max_sync_delta_) {
                left = m_leftBuffer.front();
                right = m_rightBuffer.front();
                m_leftBuffer.pop_front();
                m_rightBuffer.pop_front();
                break;
            }

            if (dt < 0) {
                m_leftBuffer.pop_front();
            } else {
                m_rightBuffer.pop_front();
            }
        }

        if (left && right) {
            m_leftImage = left;
            m_rightImage = right;
        }
    }

    if (left && right) {
        TryTrackStereoIfReady();
    }
}


/// IMU callback: appends the new IMU message to the queue
void ImageGrabberInertial::GrabImu(const sensor_msgs::msg::Imu::SharedPtr imu)
{
    std::lock_guard<std::mutex> lock(m_mutex);

    if (m_imuQueue.size() > MAX_IMU_QUEUE_SIZE) {
        m_imuQueue.pop_front();
    }

    m_imuQueue.push_back(imu);
}


/// Attempts to track a stereo-inertial frame if stereo images and IMU data are ready
void ImageGrabberInertial::TryTrackStereoIfReady()
{
    sensor_msgs::msg::Image::ConstSharedPtr left;
    sensor_msgs::msg::Image::ConstSharedPtr right;

    {
        std::lock_guard<std::mutex> lock(m_mutex);
        if (!m_leftImage || !m_rightImage) {
            return;
        }
        left = m_leftImage;
        right = m_rightImage;
    }

    cv::Mat imLeft = ConvertToGray(left);
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
        RCLCPP_WARN(logger_, "No IMU measurements available for stereo frame t=%.6f", tframe);
        return;
    }

    Sophus::SE3f pose;
    try {
        pose = m_SLAM->TrackStereo(imLeft, imRight, tframe, imu_measurements);
    } catch (const std::exception &e) {
        RCLCPP_ERROR(logger_, "Exception during ORB-SLAM3 tracking: %s", e.what());
        return;
    }

    PublishPose(pose, left->header.stamp);

    {
        std::lock_guard<std::mutex> lock(m_mutex);
        m_leftImage.reset();
        m_rightImage.reset();
    }
}

cv::Mat ImageGrabberInertial::ConvertToGray(const sensor_msgs::msg::Image::ConstSharedPtr& img) const
{
    try {
        return cv_bridge::toCvCopy(img, sensor_msgs::image_encodings::MONO8)->image;
    } catch (const cv_bridge::Exception &e) {
        RCLCPP_ERROR(logger_, "cv_bridge conversion error: %s", e.what());
        return cv::Mat();
    }
}

std::vector<ORB_SLAM3::IMU::Point> ImageGrabberInertial::ExtractImuMeasurementsLocked(double frame_time)
{
    constexpr double MAX_IMU_DELAY = 0.5;
    std::vector<ORB_SLAM3::IMU::Point> measurements;

    while (!m_imuQueue.empty()) {
        const auto imu = m_imuQueue.front();
        const double timu = rclcpp::Time(imu->header.stamp).seconds();

        if (timu > frame_time + MAX_IMU_DELAY) {
            break;
        }

        const cv::Point3f acc(
            imu->linear_acceleration.x,
            imu->linear_acceleration.y,
            imu->linear_acceleration.z);

        const cv::Point3f gyro(
            imu->angular_velocity.x,
            imu->angular_velocity.y,
            imu->angular_velocity.z);

        measurements.emplace_back(acc, gyro, timu);
        m_imuQueue.pop_front();
    }

    return measurements;
}

void ImageGrabberInertial::PublishPose(const Sophus::SE3f& se3, const rclcpp::Time& stamp)
{
    if (!odom_pub_) {
        return;
    }

    const Eigen::Vector3f t = se3.translation();
    const Eigen::Quaternionf q(se3.rotationMatrix());

    nav_msgs::msg::Odometry msg;
    msg.header.stamp = stamp;
    msg.header.frame_id = "odom";
    msg.child_frame_id = tf_frame_;

    msg.pose.pose.position.x = t.x();
    msg.pose.pose.position.y = t.y();
    msg.pose.pose.position.z = t.z();

    msg.pose.pose.orientation.x = q.x();
    msg.pose.pose.orientation.y = q.y();
    msg.pose.pose.orientation.z = q.z();
    msg.pose.pose.orientation.w = q.w();

    odom_pub_->publish(msg);
}




