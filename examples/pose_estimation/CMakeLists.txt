cmake_minimum_required(VERSION 3.15)
project(my_package)

find_package(rclcpp REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(visualization_msgs REQUIRED)
find_package(tensorflowlite REQUIRED)
find_package(OpenCV REQUIRED)


add_executable(pose-estimation src/pose-estimation.cpp)
target_link_libraries(pose-estimation PUBLIC opencv::opencv
                                             tensorflow::tensorflowlite
                                             rclcpp::rclcpp
                                             ${geometry_msgs_TARGETS}
                                             ${visualization_msgs_TARGETS})

