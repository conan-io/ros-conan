import glob
import os
import pathlib

from conan import ConanFile
from conan.errors import ConanException
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMakeDeps, CMakeToolchain
from conan.tools.env import Environment, VirtualBuildEnv
from conan.tools.files import (
    apply_conandata_patches,
    copy,
    get,
    mkdir,
    rmdir,
    save,
)
from conan.tools.microsoft import VCVars, is_msvc
from conan.tools.system import PyEnv

# Packages needed at runtime by consumers of this package (ros2 CLI, colcon, rqt, etc.).
# Also installed into the build venv during generate().
PIP_RUNTIME_TOOLS = (
    # --- colcon ---
    "colcon-cmake>=0.2.28,<0.3",
    "colcon-core>=0.17.1,<0.22",
    "colcon-defaults>=0.2.8,<0.3",
    "colcon-library-path>=0.2.1,<0.3",
    "colcon-metadata>=0.2.5,<0.3",
    "colcon-mixin>=0.2.3,<0.3",
    "colcon-output>=0.2.13,<0.3",
    "colcon-package-information>=0.4.0,<0.5",
    "colcon-package-selection>=0.2.10,<0.3",
    "colcon-parallel-executor>=0.2.4,<0.3",
    "colcon-pkg-config>=0.1.0,<0.2",
    "colcon-powershell>=0.4.0,<0.5",
    "colcon-python-setup-py>=0.2.7,<0.3",
    "colcon-recursive-crawl>=0.2.3,<0.3",
    "colcon-ros>=0.5.0,<0.6",
    "colcon-ros-domain-id-coordinator>=0.2.1,<0.3",
    "colcon-test-result>=0.3.8,<0.4",
    # --- ROS runtime Python deps ---
    "argcomplete==3.1.4",
    "catkin_pkg==1.0.0",
    "cryptography==41.0.7",
    "docutils==0.20.1",
    "empy>=4.0,<5",
    "fastjsonschema==2.19.0",
    "importlib-metadata==4.13.0",
    "lark==1.1.9",
    "lxml==5.2.1",
    "numpy==1.26.4",
    "packaging==24.0",
    "pathspec==0.12.1",
    "pluggy==1.4.0",
    "psutil==5.9.8",
    "pydot==1.4.2",
    "pyparsing==3.1.1",
    # PyQt5 provides the Python Qt bindings for rqt; the Conan qt/* dep covers the C++ side.
    "PyQt5==5.15.11",
    "python-dateutil==2.8.2",
    "PyYAML==6.0.1",
    "setuptools==68.1.2",
    "six==1.16.0",
    "typing_extensions==4.10.0",
    "vcstool==0.3.0",
    "zipp==1.0.0",
    "wheel",
)

# Lint and test tooling needed during the ROS build (ament_lint, ament_cmake_pytest, etc.)
# but not at runtime. Only installed in the build venv; not bundled into the consumer package.
_PIP_BUILD_ONLY = (
    "coverage==7.4.4",
    "distlib==0.3.8",
    "flake8==7.0.0",
    "flake8-blind-except==0.2.1",
    "flake8-builtins==2.1.0",
    "flake8-class-newline==1.6.0",
    "flake8-comprehensions==3.14.0",
    "flake8-deprecated==2.2.1",
    "flake8-docstrings==1.6.0",
    "flake8-import-order==0.18.2",
    "flake8-quotes==3.4.0",
    "iniconfig==1.1.1",
    "mccabe==0.7.0",
    "mypy==1.9.0",
    "mypy-extensions==1.0.0",
    "pycodestyle==2.11.1",
    "pydocstyle==6.3.0",
    "pyflakes==3.2.0",
    "pytest==7.4.4",
    "pytest-cov==4.1.0",
    "pytest-mock==3.12.0",
    "pytest-repeat==0.9.3",
    "pytest-rerunfailures==12.0",
    "pytest-runner==6.0.0",
    "pytest-timeout==2.2.0",
    "snowballstemmer==2.2.0",
    "yamllint==1.33.0",
)

PIP_BUILD_TOOLS = PIP_RUNTIME_TOOLS + _PIP_BUILD_ONLY


class Ros2KiltedConan(ConanFile):
    name = "ros-kilted"
    version = "2026.06.17"
    provides = "ros"  # avoids conflicts with ros-rolling, ros-humble, etc.
    exports_sources = "conandata.yml", "patches/*"
    # shared-library keeps require.run=True so VirtualRunEnv maps cpp_info.bindirs → PATH
    package_type = "shared-library"
    license = "Apache-2.0"
    url = "https://docs.ros.org/en/kilted/"
    description = "ROS 2 Kilted merged install from source."
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "variant": ["core", "base", "desktop", "desktop_full"],
        "python_version": ["3.9", "3.10", "3.11", "3.12", "3.13", "3.14"],
    }
    default_options = {
        "variant": "core",
        "python_version": "3.12",
        # CCI ffmpeg declares avcodec.requires("libwebp::libwebp") but the CCI libwebp recipe
        # exposes component "webp", not "libwebp"; the mismatch breaks OpenCV's CMakeDeps.
        "ffmpeg/*:with_libwebp": False,
        # RViz QPA platform plugin (cocoa/xcb/qwindows) is loaded at runtime from disk;
        # static Qt requires Q_IMPORT_PLUGIN (not done by rviz) and causes ObjC class
        # collisions across rviz_rendering/rviz_common/rviz2.
        "qt/*:shared": True,
        # rviz_common loads toolbar/cursor SVG icons via QPixmap; without QtSvg they silently
        # fail with "Could not load pixmap package://rviz_common/icons/...svg".
        "qt/*:qtsvg": True,
    }

    def validate(self):
        check_min_cppstd(self, 17)

    def configure(self):
        if str(self.options.variant) in ("desktop", "desktop_full"):
            # pcl_io links Boost::iostreams, requires a compiled boost
            self.options["boost/*"].header_only = False
            if self.settings.os == "Windows":
                self.options["opencv/*"].with_ffmpeg = False
        if str(self.options.variant) in ("base", "desktop", "desktop_full"):
            self.options["python_orocos_kdl/*"].python_version = str(self.options.python_version)

    def layout(self):
        ws = "ros2_ws"
        self.folders.source = ws
        self.folders.build = ws
        self.folders.generators = os.path.join(ws, "conan")

    def requirements(self):
        # Runtime/build Python interpreter from the graph (python-build-standalone, the same
        # source uv uses). Maps the python_version minor to its only available patch range,
        # e.g. "3.12" -> cpython-portable/[>=3.12 <3.13]. VirtualRunEnv exposes it on PATH so
        # the '#!/usr/bin/env python3' shebangs resolve to it on every OS.
        py = str(self.options.python_version)
        next_minor = f"{py.split('.')[0]}.{int(py.split('.')[1]) + 1}"
        self.requires(f"cpython-portable/[>={py} <{next_minor}]")
        self.requires("openssl/[>=3.3 <4]", transitive_libs=True)
        self.requires("zlib/1.3.1")
        self.requires("fmt/10.2.1")
        self.requires("spdlog/1.12.0")
        self.requires("eigen/3.4.0")
        self.requires("yaml-cpp/0.8.0")
        self.requires("sqlite3/3.45.2")
        self.requires("lz4/1.9.4")
        self.requires("zstd/1.5.5")
        self.requires("tinyxml2/10.0.0")
        self.requires("nlohmann_json/3.11.3")
        self.requires("asio/1.28.1")
        self.requires("benchmark/1.8.3", options={"shared": True})
        self.requires("console_bridge/1.0.2")
        self.requires("bullet3/3.25")
        self.requires("libyaml/0.2.5")
        self.requires("pybind11/2.11.1")
        # TODO: zenoh Rust/cargo pipeline is flaky on macOS 26; re-enable once stable.
        # self.requires("zenoh-c/1.8.0")
        # self.requires("zenoh-cpp/1.8.0")
        self.requires("foonathan-memory/0.7.3", transitive_headers=True, transitive_libs=True)
        # Replaces mcap_vendor's FetchContent of foxglove/mcap.
        self.requires("mcap/1.4.1")

        variant = str(self.options.variant)

        if variant in ("base", "desktop", "desktop_full"):
            # base adds orocos_kdl + python_orocos_kdl so python_orocos_kdl_vendor finds PyKDL
            self.requires("orocos_kdl/1.5.1")
            self.requires("python_orocos_kdl/1.5.1")

        if variant in ("desktop", "desktop_full"):
            self.requires("opencv/4.9.0")
            self.requires("assimp/5.3.1")
            self.requires("freetype/2.13.2")
            self.requires("libcurl/8.5.0")
            self.requires("openjpeg/2.5.2", override=True)
            # sdl2_vendor calls find_package(SDL2) before its ExternalProject; CMakeDeps
            # satisfies the check so the ExternalProject build is skipped entirely.
            self.requires("sdl/2.32.10")
            self.requires("qt/5.15.18", options={"shared": True})
            # OGRE's bundled glew.h includes <GL/glu.h>; qt/opencv bring opengl/system but not
            # GLU. glu/system installs libglu1-mesa-dev on Linux, is a no-op on macOS (part of
            # the OpenGL framework), and exposes glu32 on Windows.
            self.requires("glu/system")
            if self.settings.os == "Linux":
                # qt/5.15.18 pins xkbcommon/1.5.0; opencv (with_wayland=True) pins 1.6.0.
                # Both use the same targets so forcing 1.6.0 is safe.
                self.requires("xkbcommon/1.6.0", override=True)
            self.requires("pcl/1.14.1")
            # TODO: vtk/9.x not yet on ConanCenter; needed for PCL visualization module.

    def build_requirements(self):
        self.tool_requires("cmake/3.28.5")
        # Same interpreter that runs at runtime (the host requires), pinned to the exact
        # version it resolved to via <host_version>. Used to build the colcon venv so build
        # and runtime share one Python (same patch), no uv involved.
        self.tool_requires("cpython-portable/<host_version>")
        # TODO: cppcheck/2.15.0 has no prebuilt binary for Windows/MSVC profile.
        self.tool_requires("uncrustify/0.78.1")
        if self.settings.os == "Windows":
            self.tool_requires("7zip/23.01")

    def _build_python(self):
        # Interpreter from the build-context cpython-portable (tool_requires). Layout matches
        # the build machine OS (settings_build), not the target.
        root = self.dependencies.build["cpython-portable"].package_folder
        if str(self.settings_build.os) == "Windows":
            return os.path.join(root, "python.exe").replace("\\", "/")
        return os.path.join(root, "bin", "python3").replace("\\", "/")

    def generate(self):
        # Build venv layered over the cpython-portable interpreter (same Python that runs at
        # runtime). venv only holds the build tools; headers/libpython resolve via the venv's
        # base prefix, exactly as the previous uv venv did.
        venv_dir = os.path.join(self.build_folder, "build_venv")
        if not os.path.exists(venv_dir):
            self.run(f'"{self._build_python()}" -m venv "{venv_dir}"')
        if str(self.settings_build.os) == "Windows":
            venv_bin = os.path.join(venv_dir, "Scripts")
            py_exe = os.path.join(venv_bin, "python.exe")
        else:
            venv_bin = os.path.join(venv_dir, "bin")
            py_exe = os.path.join(venv_bin, "python")
        venv_bin = venv_bin.replace("\\", "/")
        py_exe = py_exe.replace("\\", "/")
        py_root = venv_dir.replace("\\", "/")

        def _pip_install(pkgs):
            quoted = " ".join(f'"{p}"' for p in pkgs)
            self.run(f'"{py_exe}" -m pip install --disable-pip-version-check '
                     f'--no-warn-script-location {quoted}')

        _pip_install(PIP_BUILD_TOOLS)
        # ament_cmake_core imports ament_package at CMake configure time, but colcon schedules
        # both packages in the same parallel batch so ament_cmake_core runs first. Pre-install
        # from source (vcstool unpacked it under src/ament/ament_package) so the first cmake
        # invocation succeeds.
        ament_package_src = os.path.join(
            self.source_folder, "src", "ament", "ament_package")
        if os.path.isdir(ament_package_src):
            _pip_install([ament_package_src])
        # Colcon must not descend into site-packages under this venv.
        save(self, os.path.join(venv_dir, "COLCON_IGNORE"), "")

        install_root = os.path.join(self.build_folder, "install")

        tc = CMakeToolchain(self)
        # asio 1.28.1 and FastDDS 3.2.3 trip on C++23 rules enforced by Clang 15+/Apple Clang 21.
        if self.settings.compiler in ("apple-clang", "clang"):
            tc.extra_cxxflags.extend([
                "-Wno-error=deprecated-literal-operator",  # asio operator"" _buf
                "-Wno-error=nonnull",                      # FastDDS TypeObjectRegistry.cpp
            ])
        tc.variables["BUILD_TESTING"] = False
        # Disable cv_bridge python to avoid Boost::python require due to numpy
        tc.variables["CV_BRIDGE_DISABLE_PYTHON"] = True
        # Python3_ROOT_DIR/Python3_EXECUTABLE for CMake >=3.12 FindPython3;
        # Python_ROOT_DIR/Python_EXECUTABLE for legacy FindPython used by some ROS packages.
        tc.variables["Python3_ROOT_DIR"] = py_root
        tc.variables["Python3_EXECUTABLE"] = py_exe
        tc.variables["Python_ROOT_DIR"] = py_root
        tc.variables["Python_EXECUTABLE"] = py_exe
        # TODO: tc.variables["USE_SYSTEM_ZENOH"] = True  # re-enable with zenoh-c/zenoh-cpp requires
        tc.variables["CMAKE_BUILD_TYPE"] = str(self.settings.build_type)
        if self.settings.os == "Linux":
            # tracetools' CMakeLists is disabled on WIN32/APPLE/ANDROID/BSD; do the same for Linux.
            tc.variables["TRACETOOLS_DISABLED"] = True
        tc.generate()
        # Conan's vs_runtime block calls cmake_policy(GET CMP0091) before any variables block runs,
        # so CMAKE_POLICY_DEFAULT_CMP0091 set inside the toolchain is already too late. Use a wrapper
        # that sets the policy and then includes the real toolchain
        conan_tc = os.path.join(self.generators_folder, CMakeToolchain.filename).replace("\\", "/")
        save(self, os.path.join(self.generators_folder, "ros_toolchain.cmake"),
             "if(POLICY CMP0091)\n"
             "  cmake_policy(SET CMP0091 NEW)\n"
             "endif()\n"
             f'include("{conan_tc}")\n')
        cmakedeps = CMakeDeps(self)
        cmakedeps.set_property("foonathan-memory", "cmake_file_name", "foonathan_memory")
        cmakedeps.set_property("tinyxml2", "cmake_file_name", "TinyXML2")
        cmakedeps.set_property("tinyxml2", "cmake_extra_variables", {"TINYXML2_LIBRARY": "tinyxml2::tinyxml2"})
        cmakedeps.set_property("asio", "cmake_file_name", "Asio")
        cmakedeps.set_property("lz4", "cmake_target_name", "LZ4::lz4")
        cmakedeps.set_property("zstd", "cmake_target_name", "zstd::zstd")
        cmakedeps.generate()
        if is_msvc(self):
            VCVars(self).generate()
        vbe = VirtualBuildEnv(self)
        # Build venv bin first on PATH so colcon and 'python' resolve to it (it holds the
        # build tools), ahead of the bare cpython-portable interpreter from tool_requires.
        vbe.environment().prepend_path("PATH", venv_bin)
        vbe.environment().define("ROS_DISTRO", "kilted")
        py_ver = str(self.options.python_version)
        vbe.environment().prepend_path("PYTHONPATH",
            os.path.join(install_root, "lib", f"python{py_ver}", "site-packages"))
        vbe.environment().prepend_path("PYTHONPATH",
            os.path.join(install_root, "Lib", "site-packages"))
        # LD_LIBRARY_PATH/DYLD_LIBRARY_PATH/PATH so tools built mid-build (e.g. cyclonedds idlc)
        # can dlopen their own libs before the merged install is complete.
        install_lib = os.path.join(install_root, "lib")
        install_bin = os.path.join(install_root, "bin")
        if self.settings.os == "Linux":
            vbe.environment().prepend_path("LD_LIBRARY_PATH", install_lib)
        elif self.settings.os == "Macos":
            vbe.environment().prepend_path("DYLD_LIBRARY_PATH", install_lib)
        vbe.environment().prepend_path("PATH", install_bin)
        vbe.generate()

    def source(self):
        rosdistro_dir = os.path.join(self.source_folder, ".rosdistro")
        get(self, **self.conan_data["sources"][self.version]["rosdistro"],
            destination=rosdistro_dir, strip_root=True)

        # vcstool 0.3.0 imports pkg_resources, removed in setuptools 80.
        boot_folder = os.path.join(self.source_folder, ".bootstrap")
        boot = PyEnv(self, folder=boot_folder, name="vcs")
        boot.install(["setuptools<80", "vcstool", "rosinstall_generator"])

        # Always clone desktop_full (superset); build() filters by variant.
        repos_path = os.path.join(self.source_folder, "sources.repos")
        rig_exe = os.path.join(boot.bin_path, "rosinstall_generator")
        rosdistro_env = Environment()
        rosdistro_env.define("ROSDISTRO_INDEX_URL",
                             pathlib.Path(rosdistro_dir, "index-v4.yaml").as_uri())
        with open(repos_path, "w", encoding="utf-8") as fh:
            with rosdistro_env.vars(self).apply():
                self.run(
                    f'"{rig_exe}" desktop_full --rosdistro kilted --deps --format repos',
                    stdout=fh, cwd=self.source_folder)
        src_dir = os.path.join(self.source_folder, "src")
        if os.path.isdir(src_dir):
            rmdir(self, src_dir)
        mkdir(self, src_dir)
        vcs_exe = os.path.join(boot.bin_path, "vcs")
        self.run(f'"{vcs_exe}" import --input "{repos_path}" src',
                 cwd=self.source_folder)

        apply_conandata_patches(self)

        # rviz_ogre_vendor picks up extra patches from its own patches/ subdirectory via the
        # CMake PATCHES directive during OGRE's ExternalProject build — not apply_conandata_patches.
        # Copy our macOS sysroot fix there so it is picked up. Dead code on Linux/Windows.
        copy(self, "ogre-1.12.10-fix-macos-sysroot.patch",
             src=os.path.join(self.export_sources_folder, "patches"),
             dst=os.path.join(self.source_folder, "src", "rviz",
                              "rviz_ogre_vendor", "patches"))

    def build(self):
        variant_targets = {
            "core": "ros_core", "base": "ros_base",
            "desktop": "desktop", "desktop_full": "desktop_full",
        }
        # Leading space in --cmake-args value required: colcon-cmake's argparse sees -D... as a
        # new flag without it; type=str.lstrip strips the space before passing to cmake.
        toolchain_file = os.path.join(
            self.generators_folder, "ros_toolchain.cmake").replace("\\", "/")
        variant = variant_targets[str(self.options.variant)]
        cmd = (
            f'colcon build --merge-install '
            f'--cmake-args " -DCMAKE_TOOLCHAIN_FILE={toolchain_file}" '
            '--catkin-skip-building-tests '
            f'--packages-up-to {variant} '
            '--packages-ignore zenoh_c_vendor zenoh_cpp_vendor rmw_zenoh_cpp '
            '--event-handlers console_cohesion+'
        )
        self.run(cmd, env="conanbuild")

    def package(self):
        inst = os.path.join(self.build_folder, "install")
        if not os.path.isdir(inst):
            raise ConanException(f"No merged install found at {inst}")
        copy(self, "*", src=inst, dst=self.package_folder)

        # Install pip runtime tools at build time so the package is hermetic:
        # no network access or venv creation needed at install time.
        pkg = self.package_folder
        pkgs = " ".join(f'"{p}"' for p in PIP_RUNTIME_TOOLS)
        self.run(
            f'"{self._build_python()}" -m pip install --quiet --disable-pip-version-check '
            f'--ignore-installed --no-warn-script-location --prefix "{pkg}" {pkgs}'
        )
        if str(self.settings.os) == "Windows":
            # pip generates binary .exe launchers with the build-time Python path baked in;
            # replace them with .cmd shims that resolve python from PATH instead.
            scripts_dir = os.path.join(pkg, "Scripts")
            if os.path.isdir(scripts_dir):
                for name in os.listdir(scripts_dir):
                    if not name.endswith("-script.py"):
                        continue
                    entry = name[:-len("-script.py")]
                    save(self, os.path.join(scripts_dir, entry + ".cmd"),
                         "@echo off\r\npython \"%~dp0%~n0-script.py\" %*\r\n")
                    exe = os.path.join(scripts_dir, entry + ".exe")
                    if os.path.isfile(exe):
                        os.remove(exe)
        else:
            new_shebang = b"#!/usr/bin/env python3\n"
            bin_dir = os.path.join(pkg, "bin")
            for name in (os.listdir(bin_dir) if os.path.isdir(bin_dir) else ()):
                path = os.path.join(bin_dir, name)
                if not os.path.isfile(path) or os.path.islink(path):
                    continue
                with open(path, "rb") as f:
                    data = f.read()
                head, sep, rest = data.partition(b"\n")
                if sep and head.startswith(b"#!") and b"python" in head:
                    with open(path, "wb") as f:
                        f.write(new_shebang + rest)

    def package_info(self):
        self.cpp_info.set_property("cmake_find_mode", "none")
        p = self.package_folder
        bin_path = os.path.join(p, "bin")
        scripts_path = os.path.join(p, "Scripts")
        self.cpp_info.bindirs.append(bin_path)
        self.cpp_info.bindirs.append(scripts_path)
        self.buildenv_info.prepend_path("PATH", bin_path)
        self.buildenv_info.prepend_path("PATH", scripts_path)

        python_sites = [os.path.join(p, "Lib", "site-packages")] + sorted(
            glob.glob(os.path.join(p, "lib", "python*", "site-packages")))
        for env in (self.buildenv_info, self.runenv_info):
            env.prepend_path("AMENT_PREFIX_PATH", p)
            for site in python_sites:
                env.prepend_path("PYTHONPATH", site)
            env.prepend_path("CMAKE_PREFIX_PATH", p)
            env.define("ROS_DISTRO", "kilted")
            env.define("ROS_VERSION", "2")
            env.define("ROS_PYTHON_VERSION", "3")
            env.prepend_path("COLCON_PREFIX_PATH", p)

        # Vendor packages install under opt/<pkg>/{include,lib,bin}; replicate what ROS's
        # setup.sh does so dlopen works without sourcing the ROS environment.
        opt_dir = os.path.join(p, "opt")
        if os.path.isdir(opt_dir):
            for name in sorted(os.listdir(opt_dir)):
                vendor = os.path.join(opt_dir, name)
                if not os.path.isdir(vendor):
                    continue
                inc = os.path.join(vendor, "include")
                if os.path.isdir(inc):
                    self.cpp_info.includedirs.append(inc)
                for libname in ("lib", "lib64"):
                    vlib = os.path.join(vendor, libname)
                    if os.path.isdir(vlib):
                        self.runenv_info.prepend_path("DYLD_LIBRARY_PATH", vlib)
                        self.runenv_info.prepend_path("LD_LIBRARY_PATH", vlib)
                        self.cpp_info.libdirs.append(vlib)
                bindir = os.path.join(vendor, "bin")
                if os.path.isdir(bindir):
                    self.cpp_info.bindirs.append(bindir)
        # CCI qt doesn't set QT_PLUGIN_PATH; without it rviz2/rqt fail to find the platform plugin.
        if str(self.options.variant) in ("desktop", "desktop_full"):
            qt_dep = self.dependencies.get("qt")
            if qt_dep:
                qt_plugins = os.path.join(qt_dep.package_folder, "plugins")
                if os.path.isdir(qt_plugins):
                    self.runenv_info.prepend_path("QT_PLUGIN_PATH", qt_plugins)
                    self.buildenv_info.prepend_path("QT_PLUGIN_PATH", qt_plugins)

        # Interpreter from the cpython-portable dependency. Put its bindir on PATH (so the
        # '#!/usr/bin/env python3' shebangs and Windows .cmd shims resolve to it) and point
        # colcon/ament at it explicitly for deterministic Python selection.
        cpy_root = self.dependencies["cpython-portable"].package_folder
        if str(self.settings.os) == "Windows":
            cpy_bin = cpy_root
            cpy_exe = os.path.join(cpy_root, "python.exe")
        else:
            cpy_bin = os.path.join(cpy_root, "bin")
            cpy_exe = os.path.join(cpy_bin, "python3")
        for env in (self.buildenv_info, self.runenv_info):
            env.prepend_path("PATH", cpy_bin)
            env.define("COLCON_PYTHON_EXECUTABLE", cpy_exe)
            env.define("AMENT_PYTHON_EXECUTABLE", cpy_exe)

        self.conf_info.define_path("user.ros2:install_prefix", p)
        setup = os.path.join(p, "setup")
        self.output.info(f"[bash] Setup the ROS Kilted environment: 'source {setup}.sh'")
        self.output.info(f"[batch] Setup the ROS Kilted environment: 'call {setup}.bat'")
        self.output.info(f"[powershell] Setup the ROS Kilted environment: '. {setup}.ps1'")
        self.conf_info.define_path("user.ros2:setup_sh", f"{setup}.sh")
        self.conf_info.define_path("user.ros2:setup_bat", f"{setup}.bat")
        self.conf_info.define_path("user.ros2:setup_ps1", f"{setup}.ps1")
