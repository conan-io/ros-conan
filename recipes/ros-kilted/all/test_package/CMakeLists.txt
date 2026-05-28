cmake_minimum_required(VERSION 3.22)
project(conan_ros2_kilted_test CXX)

find_package(rclcpp REQUIRED)

add_executable(test_package_node src/main.cpp)
target_link_libraries(test_package_node PRIVATE rclcpp::rclcpp)
