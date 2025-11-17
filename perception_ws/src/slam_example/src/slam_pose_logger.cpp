#include <filesystem>
#include <fstream>
#include <iomanip>
#include <memory>
#include <string>

#include <nav_msgs/msg/odometry.hpp>
#include <rclcpp/rclcpp.hpp>

namespace slam_example
{

class SlamPoseLogger : public rclcpp::Node
{
public:
  SlamPoseLogger()
  : rclcpp::Node("slam_pose_logger"),
    header_written_(false),
    message_count_(0)
  {
    log_path_ = declare_parameter<std::string>(
      "log_path", "/workspace/perception_ws/logs/slam_pose.csv");
    const bool append = declare_parameter<bool>("append", false);
    odom_topic_ = declare_parameter<std::string>("odom_topic", "/odometry/slam");
    flush_every_ = declare_parameter<int>("flush_every", 10);

    if (!open_log_file(append)) {
      RCLCPP_FATAL(get_logger(), "Failed to open log file at %s", log_path_.c_str());
      rclcpp::shutdown();
      return;
    }

    subscription_ = create_subscription<nav_msgs::msg::Odometry>(
      odom_topic_,
      rclcpp::SensorDataQoS(),
      std::bind(&SlamPoseLogger::handle_odometry, this, std::placeholders::_1));

    RCLCPP_INFO(get_logger(), "Logging poses from %s to %s", odom_topic_.c_str(), log_path_.c_str());
  }

private:
  bool open_log_file(bool append)
  {
    try {
      std::filesystem::path log_dir = std::filesystem::path(log_path_).parent_path();
      if (!log_dir.empty()) {
        std::filesystem::create_directories(log_dir);
      }
    } catch (const std::exception & e) {
      RCLCPP_ERROR(get_logger(), "Failed creating directories for log file: %s", e.what());
      return false;
    }

    log_stream_.open(log_path_, append ? std::ios::app : std::ios::trunc);
    if (!log_stream_.is_open()) {
      return false;
    }

    if (!append) {
      write_header();
    } else {
      header_written_ = true;
    }

    return true;
  }

  void write_header()
  {
    if (header_written_) {
      return;
    }
    log_stream_ << "stamp,x,y,z,qx,qy,qz,qw,vx,vy,vz" << std::endl;
    header_written_ = true;
  }

  void handle_odometry(const nav_msgs::msg::Odometry::SharedPtr msg)
  {
    if (!log_stream_.is_open()) {
      RCLCPP_WARN_THROTTLE(get_logger(), *get_clock(), 5000, "Log stream closed; skipping odometry.");
      return;
    }

    const double stamp = rclcpp::Time(msg->header.stamp).seconds();
    const auto & p = msg->pose.pose.position;
    const auto & q = msg->pose.pose.orientation;
    const auto & v = msg->twist.twist.linear;

    log_stream_
      << std::fixed << std::setprecision(6)
      << stamp << ','
      << p.x << ',' << p.y << ',' << p.z << ','
      << q.x << ',' << q.y << ',' << q.z << ',' << q.w << ','
      << v.x << ',' << v.y << ',' << v.z
      << '\n';

    if (++message_count_ % static_cast<size_t>(std::max(1, flush_every_)) == 0) {
      log_stream_.flush();
    }
  }

  rclcpp::Subscription<nav_msgs::msg::Odometry>::SharedPtr subscription_;
  std::ofstream log_stream_;
  std::string log_path_;
  std::string odom_topic_;
  int flush_every_;
  bool header_written_;
  size_t message_count_;
};

}  // namespace slam_example

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<slam_example::SlamPoseLogger>());
  rclcpp::shutdown();
  return 0;
}
