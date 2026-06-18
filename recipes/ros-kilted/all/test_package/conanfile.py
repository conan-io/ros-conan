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

            # Isolate whether the crash is in rcl logging init or in DDS init,
            # by calling the pybind11 Context.init() directly with logging disabled.
            diag_script = os.path.join(self.build_folder, "diag_rclpy.py")
            with open(diag_script, "w") as _f:
                _f.write(
                    "import sys\n"
                    "print('exe:', sys.executable)\n"
                    "import rclpy\n"
                    "print('rclpy imported OK')\n"
                    "print('Testing init(initialize_logging=False)...')\n"
                    "rclpy.init(args=[], initialize_logging=False)\n"
                    "print('init(logging=False) OK')\n"
                    "rclpy.shutdown()\n"
                    "print('shutdown OK')\n"
                    "print('Testing init(initialize_logging=True)...')\n"
                    "rclpy.init(args=[], initialize_logging=True)\n"
                    "print('init(logging=True) OK')\n"
                    "rclpy.shutdown()\n"
                    "print('ALL OK')\n"
                )
            prefix = 'set "RMW_IMPLEMENTATION=rmw_cyclonedds_cpp" && '
            self.run(
                f'{prefix}"{python_exe}" -Xfaulthandler "{diag_script}" '
                '|| echo [diag] script FAILED',
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
