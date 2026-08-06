import platform

from test.examples_tools import VARIANT_ARGS, run

run(f"conan install --profile ../../profiles/ros {VARIANT_ARGS} --build=missing")

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
