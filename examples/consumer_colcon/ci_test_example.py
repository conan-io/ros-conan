import os
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
    # TEMP DEBUG: colcon build dies silently (~1-2s, zero output) right after vcvars
    # activation. `echo %VAR%` in the same chained line as the `call` that sets it is
    # useless (cmd pre-expands % vars before the line runs) -- `set VAR` prints the
    # live value instead. Also resolve the exact colcon executable that would be used
    # and run it directly, isolated from the "call ... && colcon build" chain, so its
    # real error (if any) isn't swallowed.
    where_out = run(r"call .\build\generators\conanrosenv.bat && where colcon")
    colcon_path = next(
        line.strip() for line in where_out.splitlines()
        if line.strip().lower().endswith((".exe", ".cmd", ".bat"))
    )
    print(f"[DEBUG] resolved colcon = {colcon_path}")
    run(f'dir "{os.path.dirname(colcon_path)}"')
    try:
        run(
            r"call .\build\generators\conanrosenv.bat && "
            "set AMENT_PREFIX_PATH & set CMAKE_PREFIX_PATH & set COLCON_PYTHON_EXECUTABLE"
        )
    except Exception as e:
        print(f"[DEBUG] env dump failed (likely a var is unset): {e}")
    try:
        run(
            r"call .\build\generators\conanrosenv.bat && "
            f'"{colcon_path}" version'
        )
    except Exception as e:
        print(f"[DEBUG] running colcon directly failed: {e}")

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
