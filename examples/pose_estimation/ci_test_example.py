import os
import platform

from test.examples_tools import run

run(
    "conan install --profile ../../profiles/ros --build=missing "
    "--format=json --out-file=install_graph.json"
)

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
