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

            # Isolate whether the crash is in rcl logging init or in DDS init,
            # by calling the pybind11 Context.init() directly with logging disabled.
            diag_script = os.path.join(self.build_folder, "diag_rclpy.py")
            with open(diag_script, "w") as _f:
                _f.write(
                    "import ctypes, sys, os\n"
                    "\n"
                    "class _EXCEPTION_RECORD(ctypes.Structure): pass\n"
                    "_EXCEPTION_RECORD._fields_ = [\n"
                    "    ('ExceptionCode', ctypes.c_uint32),\n"
                    "    ('ExceptionFlags', ctypes.c_uint32),\n"
                    "    ('ExceptionRecord', ctypes.POINTER(_EXCEPTION_RECORD)),\n"
                    "    ('ExceptionAddress', ctypes.c_void_p),\n"
                    "    ('NumberParameters', ctypes.c_uint32),\n"
                    "    ('ExceptionInformation', ctypes.c_void_p * 15),\n"
                    "]\n"
                    "class _EXCEPTION_POINTERS(ctypes.Structure):\n"
                    "    _fields_ = [('ExceptionRecord', ctypes.POINTER(_EXCEPTION_RECORD)),\n"
                    "                ('ContextRecord', ctypes.c_void_p)]\n"
                    "class _MODULEINFO(ctypes.Structure):\n"
                    "    _fields_ = [('lpBaseOfDll', ctypes.c_void_p),\n"
                    "                ('SizeOfImage', ctypes.c_uint32),\n"
                    "                ('EntryPoint', ctypes.c_void_p)]\n"
                    "\n"
                    "def _crash_filter(exc_ptr):\n"
                    "    try:\n"
                    "        rec = exc_ptr.contents.ExceptionRecord.contents\n"
                    "        addr = rec.ExceptionAddress or 0\n"
                    "        sys.stderr.write(f'[native-crash] code=0x{rec.ExceptionCode:08X} addr=0x{addr:016X}\\n')\n"
                    "        psapi = ctypes.WinDLL('psapi')\n"
                    "        k32 = ctypes.windll.kernel32\n"
                    "        hProc = k32.GetCurrentProcess()\n"
                    "        mods = (ctypes.c_void_p * 512)()\n"
                    "        needed = ctypes.c_uint32()\n"
                    "        psapi.EnumProcessModules(hProc, mods, ctypes.sizeof(mods), ctypes.byref(needed))\n"
                    "        for h in mods[:needed.value // ctypes.sizeof(ctypes.c_void_p)]:\n"
                    "            if not h: continue\n"
                    "            mi = _MODULEINFO()\n"
                    "            psapi.GetModuleInformation(hProc, ctypes.c_void_p(h), ctypes.byref(mi), ctypes.sizeof(mi))\n"
                    "            b = mi.lpBaseOfDll or 0\n"
                    "            if b and b <= addr < b + mi.SizeOfImage:\n"
                    "                nm = ctypes.create_string_buffer(512)\n"
                    "                psapi.GetModuleFileNameExA(hProc, ctypes.c_void_p(h), nm, 512)\n"
                    "                sys.stderr.write(f'[native-crash] in: {nm.value.decode(errors=\"replace\")} +0x{addr-b:08X}\\n')\n"
                    "                break\n"
                    "    except Exception as e:\n"
                    "        sys.stderr.write(f'[filter-error] {e}\\n')\n"
                    "    sys.stderr.flush()\n"
                    "    return 0\n"
                    "\n"
                    "_FilterType = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.POINTER(_EXCEPTION_POINTERS))\n"
                    "_filter_ref = _FilterType(_crash_filter)\n"
                    "ctypes.windll.kernel32.SetUnhandledExceptionFilter(_filter_ref)\n"
                    "\n"
                    "import rclpy\n"
                    "sys.stderr.write('[diag] rclpy imported OK\\n'); sys.stderr.flush()\n"
                    "rclpy.init()\n"
                    "sys.stderr.write('[diag] init() OK\\n'); sys.stderr.flush()\n"
                    "rclpy.shutdown()\n"
                    "sys.stderr.write('[diag] ALL OK\\n'); sys.stderr.flush()\n"
                )
            prefix = ''
            self.run(
                f'"{python_exe}" -Xfaulthandler "{diag_script}" '
                '|| echo [diag] script FAILED',
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
