import os

from conan import ConanFile
from conan.tools.build import can_run, cross_building
from conan.tools.cmake import CMake, cmake_layout

# Fast-DDS uses shared memory (builtin transport) by default on Windows, which
# crashes with STATUS_ACCESS_VIOLATION (0xC0000005) during rclpy.init() on
# headless/CI environments. This profile disables builtin transports and uses
# plain UDPv4 only. Written to disk and pointed at via FASTRTPS_DEFAULT_PROFILES_FILE.
_FASTDDS_NO_SHM_PROFILE = """\
<?xml version="1.0" encoding="UTF-8" ?>
<profiles xmlns="http://www.eprosima.com/XMLSchemas/fastRTPS_Profiles">
    <transport_descriptors>
        <transport_descriptor>
            <transport_id>UDPv4Only</transport_id>
            <type>UDPv4</type>
        </transport_descriptor>
    </transport_descriptors>
    <participant profile_name="default_profile" is_default_profile="true">
        <rtps>
            <userTransports>
                <transport_id>UDPv4Only</transport_id>
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
        if self.settings.os == "Windows":
            profile_path = os.path.join(self.build_folder, "fastdds_no_shm.xml")
            with open(profile_path, "w") as f:
                f.write(_FASTDDS_NO_SHM_PROFILE)
            os.environ["FASTRTPS_DEFAULT_PROFILES_FILE"] = profile_path
        bin_path = os.path.join(self.cpp.build.bindirs[0], "test_package_node")
        self.run(bin_path, env="conanrun")
        self.run("ros2 pkg list", env="conanrun")
        self.run("ros2 node list", env="conanrun")
        self.run("ros2 topic list", env="conanrun")
        self.run("ros2 service list", env="conanrun")
        self.run("ros2 action list", env="conanrun")
