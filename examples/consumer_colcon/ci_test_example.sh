#!/bin/bash
set -e

python3 -m pip install -q --upgrade pip colcon-common-extensions catkin_pkg

conan install --profile ../../profiles/ros --build=missing

. ./build/Release/generators/conanrosenv.sh
colcon build --event-handlers console_cohesion+ --cmake-args -DPython3_EXECUTABLE="$(which python3)"
