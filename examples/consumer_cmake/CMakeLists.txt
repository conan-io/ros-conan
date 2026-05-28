cmake_minimum_required(VERSION 3.22)
project(conan_ros2_kilted_consumer CXX)

find_package(rclcpp REQUIRED)

add_executable(consumer_node src/main.cpp)
target_link_libraries(consumer_node PRIVATE rclcpp::rclcpp)
