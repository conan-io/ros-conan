import platform
import shlex
import sys

from test.examples_tools import run

run("conan install --profile ../../profiles/ros --build=missing")

if platform.system() == "Windows":
    cmake_py = f" -DPython3_EXECUTABLE={sys.executable}"
    run(
        r"call .\build\generators\conanrosenv.bat && "
        f'colcon build --event-handlers console_cohesion+ --cmake-args "{cmake_py}"'
    )
else:
    cmake_py = f" -DPython3_EXECUTABLE={shlex.quote(sys.executable)}"
    run(
        f". ./build/Release/generators/conanrosenv.sh && "
        f'colcon build --event-handlers console_cohesion+ --cmake-args "{cmake_py}"'
    )
