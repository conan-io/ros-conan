import platform
import shlex
import subprocess
import sys

from test.examples_tools import run

# Use the same interpreter as this script for pip and for CMake/ament Python
# scripts. Otherwise on macOS, `python3` on PATH (e.g. Homebrew 3.14) can
# differ from the `python` that launched CI, so catkin_pkg installs in one
# site-packages while ament_cmake's find_package(Python3) picks another.
_pip = [
    sys.executable,
    "-m",
    "pip",
    "install",
    "-q",
    "--upgrade",
    "pip",
    "colcon-common-extensions",
    "catkin_pkg",
]
if platform.system() == "Windows":
    run(subprocess.list2cmdline(_pip))
else:
    run(shlex.join(_pip))

profile = "windows-msvc" if platform.system() == "Windows" else "macos-clang"

run(f"conan install --profile ../../profiles/{profile} --build=missing")

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
