cmake_minimum_required(VERSION 3.8)
project(slam_example)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(cv_bridge REQUIRED)
find_package(OpenCV REQUIRED)
find_package(message_filters REQUIRED)

# Pangolin (visualization backend used via ORB_SLAM3)
find_package(OpenGL REQUIRED)

set(PANGOLIN_LIBS "")
find_library(PANGOLIN_LIB pangolin
  PATHS /usr/local/lib /usr/lib /usr/lib/x86_64-linux-gnu)

if(PANGOLIN_LIB)
  list(APPEND PANGOLIN_LIBS ${PANGOLIN_LIB})
else()
  # Newer Pangolin builds ship split component libraries (libpango_*).
  set(PANGOLIN_COMPONENTS
    pango_display
    pango_windowing
    pango_opengl
    pango_geometry
    pango_image
    pango_packetstream
    pango_core
  )
  foreach(component ${PANGOLIN_COMPONENTS})
    string(TOUPPER ${component} component_upper)
    find_library(PANGOLIN_${component_upper}_LIB ${component}
      PATHS /usr/local/lib /usr/lib /usr/lib/x86_64-linux-gnu)
    if(NOT PANGOLIN_${component_upper}_LIB)
      message(FATAL_ERROR "Required Pangolin component library '${component}' not found. Ensure Pangolin is installed via Dockerfile.perception.")
    endif()
    list(APPEND PANGOLIN_LIBS ${PANGOLIN_${component_upper}_LIB})
  endforeach()
endif()

# Add include directories
include_directories(
  include
  ${OpenCV_INCLUDE_DIRS}
  ${cv_bridge_INCLUDE_DIRS}
  /usr/include/eigen3
  /usr/local/include/eigen3
  /usr/local/include
  ${PROJECT_SOURCE_DIR}/../../ORB_SLAM3/include
  ${PROJECT_SOURCE_DIR}/../../ORB_SLAM3/include/CameraModels
  ${PROJECT_SOURCE_DIR}/../../ORB_SLAM3/Thirdparty/Sophus
  ${PROJECT_SOURCE_DIR}/../../ORB_SLAM3/Thirdparty/DBoW2/DBoW2
  ${PROJECT_SOURCE_DIR}/../../ORB_SLAM3/Thirdparty/g2o
  ${PROJECT_SOURCE_DIR}/../../ORB_SLAM3
)

# Link libraries
link_directories(${PROJECT_SOURCE_DIR}/../../ORB_SLAM3/lib)

add_executable(orb_slam3_stereo
  src/orb_slam3_stereo.cpp
  src/image_grabber_stereo.cpp
)

target_link_libraries(orb_slam3_stereo
  ${OpenCV_LIBS}
  ${cv_bridge_LIBRARIES}
  ${PROJECT_SOURCE_DIR}/../../ORB_SLAM3/lib/libORB_SLAM3.so
  ${PROJECT_SOURCE_DIR}/../../ORB_SLAM3/Thirdparty/DBoW2/lib/libDBoW2.so
  ${PANGOLIN_LIBS}
  -lGL
  -lGLU
  -lGLEW
)

ament_target_dependencies(orb_slam3_stereo
  rclcpp
  sensor_msgs
  nav_msgs
  cv_bridge
  message_filters
)

#Install the node
install(TARGETS orb_slam3_stereo
  DESTINATION lib/${PROJECT_NAME}
)

add_executable(orb_slam3_stereo_inertial
  src/orb_slam3_stereo_inertial.cpp
  src/image_grabber_stereo_inertial.cpp
)

target_link_libraries(orb_slam3_stereo_inertial
  ${OpenCV_LIBS}
  ${cv_bridge_LIBRARIES}
  ${message_filters_LIBRARIES}
  ${PROJECT_SOURCE_DIR}/../../ORB_SLAM3/lib/libORB_SLAM3.so
  ${PANGOLIN_LIBS}
  -lGL
  -lGLU
  -lGLEW
)

ament_target_dependencies(orb_slam3_stereo_inertial
  rclcpp
  sensor_msgs
  nav_msgs
  cv_bridge
  message_filters
)

install(TARGETS orb_slam3_stereo_inertial
  DESTINATION lib/${PROJECT_NAME}
)

add_executable(slam_pose_logger
  src/slam_pose_logger.cpp
)

target_compile_features(slam_pose_logger PUBLIC cxx_std_17)

ament_target_dependencies(slam_pose_logger
  rclcpp
  nav_msgs
)

install(TARGETS slam_pose_logger
  DESTINATION lib/${PROJECT_NAME}
)


# Install config and launch files
install(DIRECTORY config launch
  DESTINATION share/${PROJECT_NAME}
)

ament_package()

