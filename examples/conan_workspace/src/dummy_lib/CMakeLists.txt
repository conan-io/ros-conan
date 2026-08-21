cmake_minimum_required(VERSION 3.22)
project(dummy_lib CXX)

add_library(dummy_lib STATIC src/print.cpp)
target_include_directories(dummy_lib PUBLIC
  "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>"
  "$<INSTALL_INTERFACE:include>")

install(TARGETS dummy_lib
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin)
install(DIRECTORY include/ DESTINATION include)
