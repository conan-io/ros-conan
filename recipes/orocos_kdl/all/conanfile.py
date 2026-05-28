import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get, load, replace_in_file


class OrocosKdlConan(ConanFile):
    name = "orocos_kdl"
    description = "Orocos Kinematics and Dynamics C++ library (KDL)."
    license = "LGPL-2.1-or-later"
    url = "https://github.com/orocos/orocos_kinematics_dynamics"
    homepage = "http://wiki.ros.org/orocos_kdl"
    topics = ("robotics", "kinematics", "kdl", "orocos", "ros2")

    package_type = "library"
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False]}
    default_options = {"shared": True}

    def config_options(self):
        if self.settings.get_safe("os") == "Windows":
            self.options.shared = False

    def validate(self):
        if self.options.shared and self.settings.os == "Windows":
            raise ConanInvalidConfiguration("orocos_kdl: shared is not supported on Windows (upstream static only).")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        # KDL public headers include Eigen and Boost; consumers must see their includes (Conan 2 graph).
        self.requires("eigen/3.4.0", transitive_headers=True)
        self.requires("boost/1.83.0", options={"header_only": True}, transitive_headers=True)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.16 <4]")

    def source(self):
        get(self, **self.conan_data["sources"][str(self.version)], strip_root=True)

    def generate(self):
        CMakeDeps(self).generate()
        tc = CMakeToolchain(self)
        tc.cache_variables["BUILD_SHARED_LIBS"] = self.options.shared
        tc.cache_variables["ENABLE_TESTS"] = False
        tc.cache_variables["ENABLE_EXAMPLES"] = False
        tc.cache_variables["KDL_USE_NEW_TREE_INTERFACE"] = False
        tc.generate()

    def build(self):
        kdl = os.path.join(self.source_folder, "orocos_kdl")
        src_cmake = os.path.join(kdl, "src", "CMakeLists.txt")
        if "if(BUILD_SHARED_LIBS)" not in load(self, src_cmake):
            replace_in_file(
                self,
                src_cmake,
                "ELSE(MSVC)\n    SET(LIB_TYPE SHARED)\nENDIF(MSVC)",
                "ELSE(MSVC)\n    if(BUILD_SHARED_LIBS)\n        SET(LIB_TYPE SHARED)\n    else()\n        SET(LIB_TYPE STATIC)\n    endif()\nENDIF(MSVC)",
            )
        cmake = CMake(self)
        cmake.configure(build_script_folder=kdl)
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        copy(self, "COPYING", os.path.join(self.source_folder, "orocos_kdl"), os.path.join(self.package_folder, "licenses"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "orocos_kdl")
        self.cpp_info.set_property("cmake_target_name", "orocos-kdl")
        self.cpp_info.libs = ["orocos-kdl"]
        self.cpp_info.includedirs = ["include"]
        self.cpp_info.requires = ["eigen::eigen", "boost::boost"]
