cmake_minimum_required(VERSION 3.22)
project(consumer_node)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

find_package(ament_cmake REQUIRED)
find_package(dummy_lib REQUIRED)
find_package(rclcpp REQUIRED)

add_executable(consumer_node src/main.cpp)
target_link_libraries(consumer_node dummy_lib::dummy_lib rclcpp::rclcpp)

install(TARGETS consumer_node DESTINATION lib/${PROJECT_NAME})

ament_package()
