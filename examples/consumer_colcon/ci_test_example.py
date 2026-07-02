import platform

from test.examples_tools import run

# colcon and catkin_pkg are runtime tools of ros-kilted (PIP_RUNTIME_TOOLS), installed
# into the package's own site-packages and exposed on PATH/PYTHONPATH via package_info().
# Consumers don't need to install them separately.
run("conan install --profile ../../profiles/ros --build=missing")

if platform.system() == "Windows":
    run(
        r"call .\build\generators\conanrosenv.bat && "
        "colcon build --event-handlers console_cohesion+"
    )
else:
    run(
        ". ./build/Release/generators/conanrosenv.sh && "
        "colcon build --event-handlers console_cohesion+"
    )
