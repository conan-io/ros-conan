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

            diag_script = os.path.join(self.build_folder, "diag_rclpy.py")
            with open(diag_script, "w") as _f:
                _f.write(
                    "import ctypes, sys, os\n"
                    "# LoadLibrary with full path preloads System32 DLLs into the process.\n"
                    "# Once loaded, subsequent LoadLibrary('msvcp140.dll') calls (from Service\n"
                    "# Fabric DLLs or add_dll_directory entries) return the already-loaded module.\n"
                    "system32 = os.path.join(os.environ.get('SystemRoot', r'C:\\Windows'), 'System32')\n"
                    "for _dll in ['vcruntime140.dll', 'vcruntime140_1.dll', 'msvcp140.dll']:\n"
                    "    _p = os.path.join(system32, _dll)\n"
                    "    if os.path.exists(_p):\n"
                    "        ctypes.windll.LoadLibrary(_p)\n"
                    "        print(f'[diag] preloaded {_p}', flush=True)\n"
                    "import rclpy\n"
                    "_hmod = ctypes.windll.kernel32.GetModuleHandleA(b'msvcp140.dll')\n"
                    "if _hmod:\n"
                    "    _buf = ctypes.create_string_buffer(512)\n"
                    "    ctypes.windll.psapi.GetModuleFileNameExA(\n"
                    "        ctypes.windll.kernel32.GetCurrentProcess(), _hmod, _buf, 512)\n"
                    "    print(f'[diag] msvcp140.dll: {_buf.value.decode()}', flush=True)\n"
                    "rclpy.init()\n"
                    "print('[diag] rclpy.init() OK', flush=True)\n"
                    "rclpy.shutdown()\n"
                    "print('[diag] ALL OK', flush=True)\n"
                )
            self.run(
                f'"{python_exe}" -Xfaulthandler "{diag_script}" '
                '|| echo [diag] script FAILED',
                env="conanrun")
            self.run("ros2 node list", env="conanrun")
            self.run("ros2 topic list", env="conanrun")
            self.run("ros2 service list", env="conanrun")
            self.run("ros2 action list", env="conanrun")
        else:
            self.run("ros2 node list", env="conanrun")
            self.run("ros2 topic list", env="conanrun")
            self.run("ros2 service list", env="conanrun")
            self.run("ros2 action list", env="conanrun")
