cmake_minimum_required(VERSION 3.22)
project(consumer_node)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

find_package(ament_cmake REQUIRED)

# TEMP debug: CI-only diagnostic to see what CMAKE_PREFIX_PATH colcon actually
# hands to this package's configure step, vs. the raw env var it inherited.
message(STATUS "[DEBUG] CMAKE_PREFIX_PATH (cmake var) = ${CMAKE_PREFIX_PATH}")
message(STATUS "[DEBUG] CMAKE_PREFIX_PATH (env var)   = $ENV{CMAKE_PREFIX_PATH}")

find_package(dummy_lib REQUIRED)
find_package(rclcpp REQUIRED)

add_executable(consumer_node src/main.cpp)
target_link_libraries(consumer_node dummy_lib::dummy_lib rclcpp::rclcpp)

install(TARGETS consumer_node DESTINATION lib/${PROJECT_NAME})

ament_package()
