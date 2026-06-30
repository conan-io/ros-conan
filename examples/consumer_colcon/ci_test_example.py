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

run("conan install --profile ../../profiles/ros --build=missing")

if platform.system() == "Windows":
    cmake_py = subprocess.list2cmdline([f"-DPython3_EXECUTABLE={sys.executable}"])
    # TEMP DEBUG: dump the environment colcon will run under (remove once consumer_colcon is fixed)
    run(
        r"call .\build\generators\conanrosenv.bat && "
        r"where colcon python python3 & "
        r"echo AMENT=%AMENT_PREFIX_PATH% & echo CMAKE=%CMAKE_PREFIX_PATH% & "
        r"echo COLCON_PY=%COLCON_PYTHON_EXECUTABLE% & echo AMENT_PY=%AMENT_PYTHON_EXECUTABLE%"
    )
    run(
        r"call .\build\generators\conanrosenv.bat && "
        f"colcon build --event-handlers console_direct+ --cmake-args {cmake_py}"
    )
else:
    cmake_py = f"-DPython3_EXECUTABLE={shlex.quote(sys.executable)}"
    # TEMP DEBUG: dump the environment colcon will run under (remove once consumer_colcon is fixed)
    run(
        ". ./build/Release/generators/conanrosenv.sh && "
        "which -a colcon python python3; "
        "echo AMENT=$AMENT_PREFIX_PATH; echo CMAKE=$CMAKE_PREFIX_PATH; "
        "echo COLCON_PY=$COLCON_PYTHON_EXECUTABLE; echo AMENT_PY=$AMENT_PYTHON_EXECUTABLE; "
        "echo COLCON_HEAD=$(head -1 $(which colcon))"
    )
    run(
        f". ./build/Release/generators/conanrosenv.sh && "
        f"colcon build --event-handlers console_direct+ --cmake-args {cmake_py}"
    )
