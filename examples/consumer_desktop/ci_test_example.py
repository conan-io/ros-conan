import os
import platform

from test.examples_tools import VARIANT, run


if VARIANT and VARIANT not in ("desktop", "desktop_full"):
    print(f"Skipping consumer_desktop for ros-kilted variant '{VARIANT}'")
    raise SystemExit(0)

run(
    f"conan install --profile ../../profiles/ros --build=missing"
)

# rviz2 ignores QT_QPA_PLATFORM=offscreen on Windows and hangs instead of exiting.
os.environ["QT_QPA_PLATFORM"] = "offscreen"

if platform.system() == "Windows":
    run(
        r"call .\build\generators\conanrun.bat && "
        "ros2 pkg prefix rviz2 && "
        "ros2 pkg prefix rqt_gui"
    )
else:
    run(
        ". ./build/Release/generators/conanrun.sh && "
        "rviz2 --help && "
        "rqt --help"
    )
