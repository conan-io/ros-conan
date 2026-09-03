import platform

from test.examples_tools import VARIANT_ARGS, run

run("conan config install ../.. -sf extensions -tf extensions")
run(f"conan ros:install {VARIANT_ARGS} --build=missing")

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
