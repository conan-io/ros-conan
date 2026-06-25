import platform

from test.examples_tools import run

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
