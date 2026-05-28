from conan import ConanFile
from conan.tools.cmake import CMake, cmake_layout


class ConsumerConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "CMakeDeps", "CMakeToolchain"

    def layout(self):
        cmake_layout(self)

    def requirements(self):
        self.requires("ros-kilted/0.1.0")

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()
