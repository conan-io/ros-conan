import platform
from test.examples_tools import run

run("conan install --profile ../../profiles/ros --build=missing")
run("conan build --profile ../../profiles/ros")
