import os
import sys

from conan import ConanFile
from conan.tools.build import can_run, cross_building
from conan.tools.cmake import CMake, cmake_layout


class TestPackageConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "CMakeDeps", "CMakeToolchain"
    test_type = "explicit"

    def layout(self):
        cmake_layout(self)

    def requirements(self):
        self.requires(self.tested_reference_str)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.28 <4]")

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        if not can_run(self) or cross_building(self):
            return
        bin_path = os.path.join(self.cpp.build.bindirs[0], "test_package_node")
        self.run(bin_path, env="conanrun")
        self.run("ros2 pkg list", env="conanrun")
        if self.settings.os == "Windows":
            dep = self.dependencies[self.tested_reference_str]
            py_ver = f"{sys.version_info.major}_{sys.version_info.minor}"
            conan_py = os.path.join(dep.package_folder, f"conan_pyenv_{py_ver}", "Scripts", "python.exe")
            # Step 1: confirm we're using the finalize-venv Python + key env vars
            self.run(
                f'"{conan_py}" -c "import sys, os; print(\'exe:\', sys.executable); '
                'print(\'RMW:\', os.environ.get(\'RMW_IMPLEMENTATION\', \'(not set)\')); '
                '[print(\'PATH:\', p) for p in os.environ.get(\'PATH\',\'\').split(\';\') '
                'if any(x in p.lower() for x in [\'ros\', \'conan_py\', \'install\'])]"',
                env="conanrun")
            # Step 2: load the rclpy C-extension (loads DDS DLLs) — crash likely here
            self.run(
                f'"{conan_py}" -c "print(\'importing _rclpy_pybind11...\'); '
                'import rclpy._rclpy_pybind11; print(\'ok\')"',
                env="conanrun")
            # Step 3: full rclpy + RMW identifier
            self.run(
                f'"{conan_py}" -c "import rclpy; '
                'print(\'RMW impl:\', rclpy.get_rmw_implementation_identifier())"',
                env="conanrun")
        self.run("ros2 node list", env="conanrun")
        self.run("ros2 topic list", env="conanrun")
        self.run("ros2 service list", env="conanrun")
        self.run("ros2 action list", env="conanrun")
