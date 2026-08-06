import platform

from test.examples_tools import VARIANT_ARGS, run

run(f"conan install --profile ../../profiles/ros {VARIANT_ARGS} --build=missing")

if platform.system() == "Windows":
    run(
        r"call .\build\generators\conanbuild.bat && "
        r"cmake --preset conan-default && cmake --build --preset conan-release"
    )
else:
    run(
        ". ./build/Release/generators/conanbuild.sh && "
        "cmake --preset conan-release && cmake --build --preset conan-release"
    )
