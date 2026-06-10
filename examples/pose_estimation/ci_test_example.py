import platform

from test.examples_tools import run

_system = platform.system()
if _system == "Windows":
    profile = "windows-msvc"
elif _system == "Darwin":
    profile = "macos-clang"
else:
    profile = "linux-gcc"

run(f"conan install --profile ../../profiles/{profile} --build=missing")

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
