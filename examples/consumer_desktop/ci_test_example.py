import os
import platform

from test.examples_tools import run

run(
    "conan install --profile ../../profiles/ros --build=missing "
    "-o ros-kilted/*:variant=desktop"
)

# Qt's "offscreen" platform plugin lets rviz2/rqt initialize without a real display
# or window manager, so this runs unmodified on Linux/macOS/Windows CI runners.
os.environ["QT_QPA_PLATFORM"] = "offscreen"

if platform.system() == "Windows":
    run(
        r"call .\build\generators\conanrun.bat && "
        "rviz2 --help && "
        "rqt --help"
    )
else:
    run(
        ". ./build/Release/generators/conanrun.sh && "
        "rviz2 --help && "
        "rqt --help"
    )
