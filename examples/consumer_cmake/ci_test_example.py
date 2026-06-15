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
run(f"conan build --profile ../../profiles/{profile}")
