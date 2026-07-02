cmake_minimum_required(VERSION 3.22)
project(dummy_lib)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

find_package(ament_cmake REQUIRED)

# TEMP debug: same probe as consumer_node's CMakeLists.txt, to see whether the
# stray ';' in CMAKE_PREFIX_PATH is already present before dummy_lib even builds.
message(STATUS "[DEBUG] CMAKE_PREFIX_PATH (cmake var) = ${CMAKE_PREFIX_PATH}")
message(STATUS "[DEBUG] CMAKE_PREFIX_PATH (env var)   = $ENV{CMAKE_PREFIX_PATH}")

add_library(${PROJECT_NAME} STATIC src/print.cpp)
target_include_directories(${PROJECT_NAME} PUBLIC
  "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>"
  "$<INSTALL_INTERFACE:include>")

install(TARGETS ${PROJECT_NAME} EXPORT export_${PROJECT_NAME}
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin)
install(DIRECTORY include/ DESTINATION include)

ament_export_targets(export_${PROJECT_NAME} HAS_LIBRARY_TARGET)
ament_export_include_directories(include)

ament_package()
