import platform
import shlex
import subprocess
import sys

from test.examples_tools import run

# Install colcon tooling into the consumer's own Python interpreter (sys.executable).
# The profile pins ros-kilted's python_version to this same interpreter's major.minor,
# so colcon, catkin_pkg and ament all share one site-packages.
_pip = [sys.executable, "-m", "pip", "install", "-q", "--upgrade",
        "pip", "colcon-common-extensions", "catkin_pkg"]
if platform.system() == "Windows":
    run(subprocess.list2cmdline(_pip))
else:
    run(shlex.join(_pip))

run("conan install --profile ../../profiles/ros --build=missing")

if platform.system() == "Windows":
    cmake_py = subprocess.list2cmdline([f"-DPython3_EXECUTABLE={sys.executable}"])
    run(
        r"call .\build\generators\conanrosenv.bat && "
        f"colcon build --event-handlers console_cohesion+ --cmake-args {cmake_py}"
    )
else:
    cmake_py = f"-DPython3_EXECUTABLE={shlex.quote(sys.executable)}"
    run(
        f". ./build/Release/generators/conanrosenv.sh && "
        f"colcon build --event-handlers console_cohesion+ --cmake-args {cmake_py}"
    )
