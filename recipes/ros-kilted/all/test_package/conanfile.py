import os
import sys

from conan import ConanFile
from conan.tools.build import can_run, cross_building
from conan.tools.cmake import CMake, cmake_layout

# Fast-DDS uses shared memory (builtin transport) by default on Windows, which
# crashes with STATUS_ACCESS_VIOLATION (0xC0000005) during rclpy.init() on
# headless/CI environments. This profile disables builtin transports and uses
# plain UDPv4 only. Written to disk and pointed at via FASTDDS_DEFAULT_PROFILES_FILE.
_FASTDDS_NO_SHM_PROFILE = """\
<?xml version="1.0" encoding="UTF-8" ?>
<profiles>
    <transport_descriptors>
        <transport_descriptor>
            <transport_id>LoopbackUDP</transport_id>
            <type>UDPv4</type>
            <interfaceWhiteList>
                <address>127.0.0.1</address>
            </interfaceWhiteList>
        </transport_descriptor>
    </transport_descriptors>
    <participant profile_name="default_profile" is_default_profile="true">
        <rtps>
            <userTransports>
                <transport_id>LoopbackUDP</transport_id>
            </userTransports>
            <useBuiltinTransports>false</useBuiltinTransports>
        </rtps>
    </participant>
</profiles>
"""


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

            profile_path = os.path.join(self.build_folder, "fastdds_no_shm.xml")
            with open(profile_path, "w") as f:
                f.write(_FASTDDS_NO_SHM_PROFILE)
            prefix = (
                f'set "FASTDDS_DEFAULT_PROFILES_FILE={profile_path}" && '
                'set "ROS_LOCALHOST_ONLY=1" && '
            )
            # Direct rclpy.init() test (non-fatal): tells us whether the Fast-DDS
            # profile actually prevents the crash, independent of the daemon path.
            self.run(
                f'{prefix}"{python_exe}" -c '
                '"import rclpy; rclpy.init(); print(chr(79)*3); rclpy.shutdown()" '
                '|| echo [diag] rclpy.init FAILED with profile',
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
