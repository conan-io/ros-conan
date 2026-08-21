from conan import ConanFile
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout


class DummyLibConan(ConanFile):
    name = "dummy_lib"
    version = "0.1"
    package_type = "static-library"
    settings = "os", "compiler", "build_type", "arch"
    exports_sources = "CMakeLists.txt", "src/*", "include/*"

    def layout(self):
        cmake_layout(self)

    def generate(self):
        deps = CMakeDeps(self)
        deps.generate()
        tc = CMakeToolchain(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["dummy_lib"]
