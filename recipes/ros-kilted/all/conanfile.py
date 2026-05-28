import glob
import os
import sys

from conan import ConanFile
from conan.errors import ConanException
from conan.tools.cmake import CMakeDeps, CMakeToolchain
from conan.tools.env import VirtualBuildEnv
from conan.tools.files import (
    apply_conandata_patches,
    copy,
    download,
    get,
    mkdir,
    replace_in_file,
    rmdir,
    save,
)
from conan.tools.microsoft import VCVars
from conan.tools.system import PyEnv

PIP_BUILD_TOOLS = (
    # --- colcon ---
    "colcon-cmake>=0.2.28,<0.3",
    "colcon-core>=0.17.1,<0.18",
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
    # --- Python pins ---
    "argcomplete==3.1.4",
    "catkin_pkg==1.0.0",
    "coverage==7.4.4",
    "cryptography==41.0.7",
    "distlib==0.3.8",
    "docutils==0.20.1",
    "empy==3.3.4",
    "flake8==7.0.0",
    "flake8-blind-except==0.2.1",
    "flake8-builtins==2.1.0",
    "flake8-class-newline==1.6.0",
    "flake8-comprehensions==3.14.0",
    "flake8-deprecated==2.2.1",
    "flake8-docstrings==1.6.0",
    "flake8-import-order==0.18.2",
    "flake8-quotes==3.4.0",
    "importlib-metadata==4.13.0",
    "iniconfig==1.1.1",
    "lark==1.1.9",
    "lxml==5.2.1",
    "mccabe==0.7.0",
    "mypy==1.9.0",
    "mypy-extensions==1.0.0",
    "numpy==1.26.4",
    "packaging==24.0",
    "pathspec==0.12.1",
    "pluggy==1.4.0",
    "psutil==5.9.8",
    "pycodestyle==2.11.1",
    "pydocstyle==6.3.0",
    "pydot==1.4.2",
    "pyflakes==3.2.0",
    #"pygraphviz==1.11",
    "pyparsing==3.1.1",
    # PyQt5 / PyQt5-sip are only needed by rqt_* GUI packages. They are NOT
    # in the --packages-up-to rclcpp subset we build, and installing them
    # from pip triggers a from-source PyQt5 build that requires qmake (Qt's
    # build tool) on the host. On macOS without Qt installed that fails with
    # `PyProjectOptionException('qmake', ...)`. Re-enable only when the recipe
    # scales up to packages that genuinely need them.
    # "PyQt5==5.15.9",
    # "PyQt5-sip==12.12.2",
    "pytest==7.4.4",
    "pytest-cov==4.1.0",
    "pytest-mock==3.12.0",
    "pytest-repeat==0.9.3",
    "pytest-rerunfailures==12.0",
    "pytest-runner==6.0.0",
    "pytest-timeout==2.2.0",
    "python-dateutil==2.8.2",
    "fastjsonschema==2.19.0",
    #"python-orocos-kdl==1.5.1",
    "PyYAML==6.0.1",
    "setuptools==68.1.2",
    "six==1.16.0",
    "snowballstemmer==2.2.0",
    "typing_extensions==4.10.0",
    "vcstool==0.3.0",
    "yamllint==1.33.0",
    "zipp==1.0.0",
    "wheel",
)


class Ros2KiltedConan(ConanFile):
    name = "ros-kilted"
    version = "0.1.0"
    provides = "ros"  # To avoid name conflicts with other ros packages: ros-rolling, ros-humble, etc.
    exports_sources = "conandata.yml", "patches/*"
    # Shared stack + executables: keeps require.run=True so VirtualRunEnv maps cpp_info.bindirs → PATH.
    package_type = "shared-library"
    license = "Apache-2.0"
    url = "https://docs.ros.org/en/kilted/"
    description = "ROS 2 Kilted merged install from source, dependencies via Conan + PyEnv."
    settings = "os", "compiler", "build_type", "arch"
    options = {"variant": ["core", "base", "desktop", "desktop_full"]}
    default_options = {
        "variant": "core",
        # CCI ffmpeg recipe declares `avcodec.requires.append("libwebp::libwebp")` but the
        # libwebp recipe exposes components `webp`/`webpdecoder`/...; the missing target name
        # breaks OpenCV's CMakeDeps consumption. OpenCV links libwebp directly for image I/O
        # so disabling FFmpeg's WebP path costs nothing for ROS desktop usage.
        "ffmpeg/*:with_libwebp": False,
        # Qt must be shared for rviz: the QPA platform plugin (cocoa on macOS, xcb on Linux,
        # qwindows on Windows) is loaded at runtime from disk. With static Qt the plugin
        # would have to be baked in via Q_IMPORT_PLUGIN, which rviz does not do, so the GUI
        # fails with "Could not find the Qt platform plugin". Static Qt also duplicates Qt
        # symbols across rviz_rendering/rviz_common/rviz2 binaries (objc class collisions).
        "qt/*:shared": True,
        # rviz_common ships its toolbar/cursor icons as SVG and loads them through
        # QPixmap. Without the QtSvg image plugin those files silently fail with
        # "Could not load pixmap package://rviz_common/icons/...svg".
        "qt/*:qtsvg": True,
        "openssl/*:shared": True
    }

    # ros2/variants metapackages. core/base prefixed with `ros_`; desktop variants not.
    # Status: `core` builds. `base` reuses core's Conan deps (only adds ROS source pkgs).
    # `desktop` blocked on Qt5, `desktop_full` on Qt5 + VTK (none on CCI). See requirements().
    _VARIANT_TARGET = {
        "core": "ros_core",
        "base": "ros_base",
        "desktop": "desktop",
        "desktop_full": "desktop_full",
    }

    def configure(self):
        # PCL's io module links Boost::iostreams. If boost gets resolved as
        # header-only, CMakeDeps does not generate that imported target and
        # desktop_full variant fails.
        if str(self.options.variant) == "desktop_full":
            self.options["boost/*"].header_only = False

    def layout(self):
        # Single-tree colcon workspace: src/, build/, install/, log/ under ros2_ws/
        ws = "ros2_ws"
        self.folders.source = ws
        self.folders.build = ws
        self.folders.generators = os.path.join(ws, "conan")

    def requirements(self):
        self.requires("openssl/3.3.2", transitive_libs=True)
        self.requires("zlib/1.3.1")
        self.requires("fmt/10.2.1")
        # Temporarily off: no matching ConanCenter prebuilt for this Windows/MSVC profile (re-enable with
        # --build=missing or after binaries exist). Missing-binary set included:
        # assimp/5.3.1, cppcheck/2.15.0, dav1d/1.5.3, ffmpeg/4.4.4, freetype/2.13.2, libcurl/8.5.0,
        # libtiff/4.6.0, libvpx/1.15.2, libx265/3.6, openh264/2.6.0,
        # protobuf/3.21.12, xz_utils/5.8.3 (opencv pulls most of the media stack).
        self.requires("spdlog/1.12.0")
        self.requires("eigen/3.4.0")
        self.requires("yaml-cpp/0.8.0")
        self.requires("sqlite3/3.45.2")
        self.requires("lz4/1.9.4")
        self.requires("zstd/1.5.5")
        self.requires("tinyxml2/10.0.0")
        self.requires("nlohmann_json/3.11.3")
        self.requires("asio/1.28.1")
        self.requires("gtest/1.17.0")
        self.requires("benchmark/1.8.3", options={"shared": True})
        self.requires("console_bridge/1.0.2")
        self.requires("bullet3/3.25")
        self.requires("cunit/2.1-3")
        self.requires("libyaml/0.2.5")
        #self.requires("zenoh-c/1.8.0")
        #self.requires("zenoh-cpp/1.8.0")
        self.requires("pybind11/2.11.1")
        # Replaces Fast-DDS' ExternalProject of eProsima/memory. Note CCI uses
        # a hyphen in the package name; cmake_file_name is forced below so the
        # vendor's `find_package(foonathan_memory)` (underscore) still resolves.
        self.requires("foonathan-memory/0.7.3", transitive_headers=True, transitive_libs=True)
        # Replaces mcap_vendor's FetchContent of foxglove/mcap.
        self.requires("mcap/1.4.1")

        # Variant-scoped requires (package_id reflects the exact dep set per variant).
        # `base` adds orocos_kdl + python_orocos_kdl so python_orocos_kdl_vendor finds PyKDL
        # on PYTHONPATH; other base-only ROS packages still reuse core Conan deps.
        variant = str(self.options.variant)

        if variant in ("base", "desktop", "desktop_full"):
            self.requires("orocos_kdl/1.5.1")
            self.requires("python_orocos_kdl/1.5.1")

        if variant in ("desktop", "desktop_full"):
            self.requires("opencv/4.9.0")
            self.requires("assimp/5.3.1")
            self.requires("freetype/2.13.2")
            self.requires("libcurl/8.5.0")
            self.requires("openjpeg/2.5.2", override=True)
            # Default qt/*:shared=False is static-only (no qwindows.dll under plugins/);
            # RViz/Qt QPA still loads platform plugins at runtime → require shared Qt.
            self.requires("qt/5.15.18", options={"shared": True})
            # OGRE is built by rviz_ogre_vendor from upstream sources; zlib/freetype are
            # find_package'd on Windows (patched) and supplied via Conan with the colcon toolchain.

        if variant == "desktop_full":
            self.requires("pcl/1.14.1")  # built with with_vtk=False on CCI; OK for headless, not for full viz.
            # self.requires("vtk/9.x")  # Not on ConanCenter; required for PCL visualization — provide via system or custom recipe.

    def build_requirements(self):
        self.tool_requires("cmake/3.28.5")
        # self.tool_requires("cppcheck/2.15.0")  # see requirements() comment: missing binary for profile
        self.tool_requires("uncrustify/0.78.1")
        if self.settings.os == "Windows":
            self.tool_requires("7zip/23.01")

    def generate(self):
        pyenv = PyEnv(self)
        pyenv.install(list(PIP_BUILD_TOOLS))
        pyenv.generate()
        # Colcon must not descend into site-packages under this venv.
        save(self, os.path.join(pyenv.env_dir, "COLCON_IGNORE"), "")

        py_exe = pyenv.env_exe.replace("\\", "/")
        py_root = pyenv.env_dir.replace("\\", "/")

        tc = CMakeToolchain(self)
        # Clang 15+/Apple Clang 21 enforce C++23 rules that asio 1.28.1 and
        # FastDDS 3.2.3 still trip on. -Wno-error=<tag> downgrades each to a
        # warning but keeps it visible; plain -Wno-<tag> would be re-enabled
        # by the `-Wall` that fastdds/cyclonedds append later in their own
        # target_compile_options.
        if self.settings.compiler in ("apple-clang", "clang"):
            tc.extra_cxxflags.extend([
                "-Wno-error=deprecated-literal-operator",  # asio operator"" _buf
                "-Wno-error=nonnull",                      # FastDDS TypeObjectRegistry.cpp
            ])
        tc.cache_variables["BUILD_TESTING"] = False
        tc.variables["BUILD_TESTING"] = False
        tc.cache_variables["Python3_ROOT_DIR"] = pyenv.env_dir
        tc.cache_variables["Python3_EXECUTABLE"] = pyenv.env_exe
        tc.cache_variables["Python_ROOT_DIR"] = pyenv.env_dir
        tc.cache_variables["Python_EXECUTABLE"] = pyenv.env_exe
        tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0091"] = "NEW"
        # Zenoh RMW is disabled: its rust/cargo pipeline is flaky on macOS 26.
        # Re-enable by: uncomment zenoh-c/zenoh-cpp requires, USE_SYSTEM_ZENOH,
        # and the matching --packages-ignore entries in build().
        # tc.cache_variables["USE_SYSTEM_ZENOH"] = True
        # MSVC path limit (~260) vs deep Conan build dirs + long rosidl names.

        # Duplicated into tc.variables because colcon invokes cmake directly
        # (no CMakePresets), so it only sees what lands in conan_toolchain.cmake.
        tc.variables["Python3_ROOT_DIR"] = py_root
        tc.variables["Python3_EXECUTABLE"] = py_exe
        tc.variables["Python_ROOT_DIR"] = py_root
        tc.variables["Python_EXECUTABLE"] = py_exe
        tc.variables["CMAKE_POLICY_DEFAULT_CMP0091"] = "NEW"
        # tc.variables["USE_SYSTEM_ZENOH"] = True
        tc.variables["CMAKE_BUILD_TYPE"] = str(self.settings.build_type)
        tc.generate()
        self._patch_conan_toolchain_cmp0091_early()
        cmakedeps = CMakeDeps(self)
        cmakedeps.set_property("tinyxml2", "cmake_file_name", "TinyXML2")
        cmakedeps.set_property("tinyxml2", "cmake_extra_variables", {"TINYXML2_LIBRARY": "tinyxml2::tinyxml2"})
        cmakedeps.set_property("asio", "cmake_file_name", "Asio")
        cmakedeps.set_property("lz4", "cmake_target_name", "LZ4::lz4")
        cmakedeps.set_property("zstd", "cmake_target_name", "zstd::zstd")
        cmakedeps.generate()
        VCVars(self).generate()
        vbe = VirtualBuildEnv(self)
        vbe.environment().define("ROS_DISTRO", "kilted")
        vbe.generate()

    def _patch_conan_toolchain_cmp0091_early(self):
        """Conan's vs_runtime block runs cmake_policy(GET CMP0091) before variables set the default.
        Colcon does not preset CMP0091; set the policy at the top of the toolchain so the check passes.
        """
        path = os.path.join(self.generators_folder, CMakeToolchain.filename)
        block = (
            "include_guard()\n"
            "message(STATUS \"Using Conan toolchain: ${CMAKE_CURRENT_LIST_FILE}\")\n"
        )
        injection = (
            "include_guard()\n"
            "if(POLICY CMP0091)\n"
            "  cmake_policy(SET CMP0091 NEW)\n"
            "endif()\n"
            "message(STATUS \"Using Conan toolchain: ${CMAKE_CURRENT_LIST_FILE}\")\n"
        )
        replace_in_file(self, path, block, injection, strict=True)

    def source(self):
        pyenv = PyEnv(self, folder=self.source_folder)
        pyenv.install(["setuptools==68.1.2", "vcstool==0.3.0"])
        sources_data = self.conan_data["sources"][str(self.version)]
        repos = os.path.join(self.source_folder, "ros2.repos")
        download(self, url=sources_data["url"], sha256=sources_data["sha256"], filename=repos)
        src_dir = os.path.join(self.source_folder, "src")
        if os.path.isdir(src_dir):
            rmdir(self, src_dir)
        mkdir(self, src_dir)

        # Bootstrap a minimal PyEnv for `vcs`; the main PyEnv in generate()
        # runs too late. setuptools<80 is pinned because vcstool 0.3.0 still
        # imports pkg_resources (removed in setuptools 80).
        boot_folder = os.path.join(self.source_folder, ".bootstrap")
        boot = PyEnv(self, folder=boot_folder, name="vcs")
        boot.install(["setuptools<80", "vcstool"])
        vcs_exe = os.path.join(boot.bin_path, "vcs")
        self.run(f'"{vcs_exe}" import --input "{repos}" src',
                 cwd=self.source_folder)

        # ros2/variants tarball into src/ros2/variants/ so colcon resolves
        # --packages-up-to {ros_core,ros_base,desktop,desktop_full}.
        get(self, **sources_data["variants"],
            destination=os.path.join(src_dir, "ros2", "variants"),
            strip_root=True)

        apply_conandata_patches(self)

        # OGRE 1.12.10's CMakeLists.txt has a buggy execute_process invocation that
        # passes a literal shell pipe to xcodebuild, which fails on Xcode 26 (macOS
        # 26 SDK) and corrupts CMAKE_OSX_SYSROOT. rviz_ogre_vendor consumes any
        # patches under its `patches/` folder (PATCHES directive), so dropping our
        # OGRE-targeting patch there gets applied to the upstream tarball before
        # the OGRE configure runs. Copied unconditionally because Conan 2 forbids
        # self.settings access in source(); the patched code path lives behind
        # `elseif (APPLE AND NOT APPLE_IOS)` so it's dead code on Linux/Windows.
        copy(self, "ogre-1.12.10-fix-macos-sysroot.patch",
             src=os.path.join(self.export_sources_folder, "patches"),
             dst=os.path.join(self.source_folder, "src", "ros2", "rviz",
                              "rviz_ogre_vendor", "patches"))

    def build(self):
        # Pass the Conan toolchain to each colcon-invoked cmake via -D. The
        # leading space inside the value is required by colcon-cmake's
        # argparse (-D... otherwise read as a new flag; `type=str.lstrip`
        # strips it).
        # --packages-ignore skips zenoh (Rust crates; flaky on macOS 26);
        # rclcpp works fine with the default rmw_fastrtps_cpp.
        toolchain_file = os.path.join(
            self.generators_folder, CMakeToolchain.filename).replace("\\", "/")
        variant = self._VARIANT_TARGET[str(self.options.variant)]
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

    def package_info(self):
        self.cpp_info.set_property("cmake_find_mode", "none")
        p = self.package_folder
        bin_path = os.path.join(p, "bin")
        scripts_path = os.path.join(p, "Scripts")
        self.cpp_info.bindirs.append(bin_path)
        self.cpp_info.bindirs.append(scripts_path)
        self.buildenv_info.prepend_path("PATH", bin_path)
        self.buildenv_info.prepend_path("PATH", scripts_path)
        self.buildenv_info.append_path("AMENT_PREFIX_PATH", p)
        self.buildenv_info.prepend_path("PYTHONPATH", os.path.join(p, "Lib", "site-packages"))
        for site in sorted(glob.glob(os.path.join(p, "lib", "python*", "site-packages"))):
            self.buildenv_info.prepend_path("PYTHONPATH", site)
        self.buildenv_info.prepend_path("AMENT_PREFIX_PATH", p)
        self.buildenv_info.prepend_path("CMAKE_PREFIX_PATH", p)
        self.buildenv_info.define("ROS_DISTRO", "kilted")
        self.buildenv_info.define("ROS_VERSION", "2")
        self.buildenv_info.define("ROS_PYTHON_VERSION", "3")
        self.buildenv_info.prepend_path("COLCON_PREFIX_PATH", p)

        # Run PATH: rely on cpp_info.bindirs + VirtualRunEnv (see package_type); avoids duplicating PATH here.
        self.runenv_info.append_path("AMENT_PREFIX_PATH", p)
        self.runenv_info.prepend_path("PYTHONPATH", os.path.join(p, "Lib", "site-packages"))
        for site in sorted(glob.glob(os.path.join(p, "lib", "python*", "site-packages"))):
            self.runenv_info.prepend_path("PYTHONPATH", site)
        self.runenv_info.prepend_path("AMENT_PREFIX_PATH", p)
        self.runenv_info.prepend_path("CMAKE_PREFIX_PATH", p)
        self.runenv_info.define("ROS_DISTRO", "kilted")
        self.runenv_info.define("ROS_VERSION", "2")
        self.runenv_info.define("ROS_PYTHON_VERSION", "3")
        self.runenv_info.prepend_path("COLCON_PREFIX_PATH", p)

        # ament_cmake_vendor_package isolates each vendor's libs under opt/<pkg>/lib.
        # ROS's setup.sh sources per-vendor hooks that prepend those paths to
        # DYLD_/LD_LIBRARY_PATH; consumers running through `conan run` do not source
        # setup.sh, so dlopen of e.g. librviz_default_plugins (-> libgz-math) fails.
        # Replicate the hook output directly in runenv so plugins resolve out of the box.
        opt_dir = os.path.join(p, "opt")
        if os.path.isdir(opt_dir):
            for vendor in sorted(os.listdir(opt_dir)):
                for libdir in ("lib", "lib64"):
                    vlib = os.path.join(opt_dir, vendor, libdir)
                    if os.path.isdir(vlib):
                        self.runenv_info.prepend_path("DYLD_LIBRARY_PATH", vlib)
                        self.runenv_info.prepend_path("LD_LIBRARY_PATH", vlib)
        # ConanCenter qt exposes plugins under <prefix>/plugins but does not set
        # QT_PLUGIN_PATH; without it rviz2/rqt fail (e.g. "Could not find the Qt
        # platform plugin \"windows\"" on MSVC builds).
        if str(self.options.variant) in ("desktop", "desktop_full"):
            try:
                qt_dep = self.dependencies["qt"]
            except KeyError:
                qt_dep = None
            if qt_dep is not None:
                qt_plugins = os.path.join(qt_dep.package_folder, "plugins")
                if os.path.isdir(qt_plugins):
                    self.runenv_info.prepend_path("QT_PLUGIN_PATH", qt_plugins)
                    self.buildenv_info.prepend_path("QT_PLUGIN_PATH", qt_plugins)

        # Vendors (OGRE, Gazebo CMake, mimick, …) install merged relocatable trees under
        # <prefix>/opt/<pkg>/{include,lib,bin}. Expose them for consumers (CMake, PATH).
        opt_root = os.path.join(p, "opt")
        if os.path.isdir(opt_root):
            for name in sorted(os.listdir(opt_root)):
                vendor = os.path.join(opt_root, name)
                if not os.path.isdir(vendor):
                    continue
                inc = os.path.join(vendor, "include")
                if os.path.isdir(inc):
                    self.cpp_info.includedirs.append(inc)
                for libname in ("lib", "lib64"):
                    libdir = os.path.join(vendor, libname)
                    if os.path.isdir(libdir):
                        self.cpp_info.libdirs.append(libdir)
                bindir = os.path.join(vendor, "bin")
                if os.path.isdir(bindir):
                    self.cpp_info.bindirs.append(bindir)

        # colcon local_setup.* and ament prefix hooks embed a build-time Python path.
        # Pre-set these so consumers (VirtualRunEnv / conanrun) override before calling
        # local_setup.bat/ps1. Profile: ros2-kilted/*:user.ros2:python_executable=/path/to/python.exe
        py_exe = self.conf.get("user.ros2:python_executable", default=sys.executable)
        if py_exe:
            self.runenv_info.define("COLCON_PYTHON_EXECUTABLE", py_exe)
            self.runenv_info.define("AMENT_PYTHON_EXECUTABLE", py_exe)
            self.buildenv_info.define("COLCON_PYTHON_EXECUTABLE", py_exe)
            self.buildenv_info.define("AMENT_PYTHON_EXECUTABLE", py_exe)

        # Consumers often use local_setup.bat; document path.
        self.conf_info.define_path("user.ros2:install_prefix", p)
        setup_script_path = os.path.join(p, "setup")
        setup_script_path_sh = setup_script_path + ".sh"
        setup_script_path_bat = setup_script_path + ".bat"
        setup_script_path_ps1 = setup_script_path + ".ps1"
        self.output.info(f"[bash] Setup the ROS Kilted environment: 'source {setup_script_path_sh}'")
        self.output.info(f"[batch] Setup the ROS Kilted environment: 'call {setup_script_path_bat}'")
        self.output.info(f"[powershell] Setup the ROS Kilted environment: '. {setup_script_path_ps1}'")
        self.conf_info.define_path("user.ros2:setup_sh", setup_script_path_sh)
        self.conf_info.define_path("user.ros2:setup_bat", setup_script_path_bat)
        self.conf_info.define_path("user.ros2:setup_ps1", setup_script_path_ps1)
