# SPDX-License-Identifier: LGPL-2.1-or-later

import os

from conan import ConanFile
from conan.tools.system import PyEnv
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, copy, get


class PythonOrocosKdlConan(ConanFile):
    name = "python_orocos_kdl"
    description = (
        "PyKDL Python bindings for Orocos KDL (PyBind11 extension). "
        "Set conf user.python_orocos_kdl:python_executable to the same interpreter "
        "that will load the module (e.g. ros-kilted PyEnv) so the extension ABI matches."
    )
    license = "LGPL-2.1-or-later"
    url = "https://github.com/orocos/orocos_kinematics_dynamics"
    homepage = "http://wiki.ros.org/python_orocos_kdl"
    topics = ("robotics", "kinematics", "kdl", "pykdl", "ros2")

    settings = "os", "compiler", "build_type", "arch"
    exports_sources = "conandata.yml", "patches/*"

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("orocos_kdl/1.5.1", transitive_headers=True, transitive_libs=True)
        self.requires("pybind11/2.11.1", transitive_headers=True)
        # Direct deps so CMakeDeps generates Eigen3/boost configs (transitive-only deps are omitted).
        self.requires("eigen/3.4.0", transitive_headers=True)
        self.requires("boost/1.83.0", options={"header_only": True}, transitive_headers=True)

    def source(self):
        get(self, **self.conan_data["sources"][str(self.version)], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        CMakeDeps(self).generate()
        tc = CMakeToolchain(self)
        pyenv = PyEnv(self)
        pyenv.generate()
        tc.cache_variables["Python3_EXECUTABLE"] = pyenv.env_exe
        # Embed RPATH of linked deps (orocos_kdl) into the installed .so so
        # `import PyKDL` finds liborocos-kdl.dylib without DYLD_LIBRARY_PATH.
        tc.cache_variables["CMAKE_INSTALL_RPATH_USE_LINK_PATH"] = True
        tc.generate()

    def build(self):
        cmake = CMake(self)
        sub = os.path.join(self.source_folder, "python_orocos_kdl")
        cmake.configure(build_script_folder=sub)
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        copy(
            self,
            "COPYING",
            os.path.join(self.source_folder, "orocos_kdl"),
            os.path.join(self.package_folder, "licenses"),
        )

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "python_orocos_kdl")
        self.cpp_info.set_property("cmake_target_name", "python_orocos_kdl::python_orocos_kdl")

        def _prepend_pythonpath(p):
            if os.path.isdir(p):
                self.runenv_info.prepend_path("PYTHONPATH", p)
                self.buildenv_info.prepend_path("PYTHONPATH", p)

        lib_root = os.path.join(self.package_folder, "lib")
        if os.path.isdir(lib_root):
            for name in os.listdir(lib_root):
                for sub in ("site-packages", "dist-packages"):
                    _prepend_pythonpath(os.path.join(lib_root, name, sub))
        _prepend_pythonpath(os.path.join(self.package_folder, "Lib", "site-packages"))
