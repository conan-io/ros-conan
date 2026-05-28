cmake_minimum_required(VERSION 3.16)
project(test_package_orocos_kdl LANGUAGES CXX)

find_package(orocos_kdl REQUIRED CONFIG)

add_executable(main main.cpp)
target_link_libraries(main PRIVATE orocos-kdl)
