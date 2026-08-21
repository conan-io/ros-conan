from conan import ConanFile
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.env import VirtualRunEnv


class ConsumerNodeConan(ConanFile):
    name = "consumer_node"
    version = "0.1"
    package_type = "application"
    settings = "os", "compiler", "build_type", "arch"
    exports_sources = "CMakeLists.txt", "src/*"

    def layout(self):
        cmake_layout(self)

    def requirements(self):
        self.requires("dummy_lib/0.1")
        self.requires("ros-kilted/2026.06.17")

    def generate(self):
        deps = CMakeDeps(self)
        deps.generate()
        tc = CMakeToolchain(self)
        tc.generate()
        VirtualRunEnv(self).generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()
