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
            # Diagnose which Python backs the finalize() venv. The `home` field in
            # pyvenv.cfg points to the base interpreter: uv-managed = python-build-standalone
            # (incompatible VCRUNTIME with rclpy extensions); system = correct CPython.
            dep = self.dependencies["ros-kilted"]
            py_ver = f"{sys.version_info.major}_{sys.version_info.minor}"
            pyenv_dir = os.path.join(dep.package_folder, f"conan_pyenv_{py_ver}")
            pyvenv_cfg = os.path.join(pyenv_dir, "pyvenv.cfg")
            if os.path.exists(pyvenv_cfg):
                with open(pyvenv_cfg) as _f:
                    self.output.info(f"[diag] pyvenv.cfg:\n{_f.read()}")
            python_exe = os.path.join(pyenv_dir, "Scripts", "python.exe")
            self.run(f'"{python_exe}" -c "import sys; print(sys.executable); print(sys.version)"',
                     env="conanrun")

            # Direct rclpy.init() with faulthandler to see exact crash location.
            # -Xfaulthandler prints the C/Python stack when an access violation occurs.
            prefix = 'set "RMW_IMPLEMENTATION=rmw_cyclonedds_cpp" && '
            self.run(
                f'{prefix}"{python_exe}" -Xfaulthandler -c '
                '"import rclpy; rclpy.init(); print(chr(79)*3); rclpy.shutdown()" '
                '|| echo [diag] rclpy.init FAILED',
                env="conanrun")
            self.run(f"{prefix}ros2 node list", env="conanrun")
            self.run(f"{prefix}ros2 topic list", env="conanrun")
            self.run(f"{prefix}ros2 service list", env="conanrun")
            self.run(f"{prefix}ros2 action list", env="conanrun")
        else:
            self.run("ros2 node list", env="conanrun")
            self.run("ros2 topic list", env="conanrun")
            self.run("ros2 service list", env="conanrun")
            self.run("ros2 action list", env="conanrun")
