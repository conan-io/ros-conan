import platform
from test.examples_tools import run

profile = "windows-msvc" if platform.system() == "Windows" else "macos-clang"

run(f"conan install --profile ../../profiles/{profile} --build=missing")
run(f"conan build --profile ../../profiles/{profile}")
