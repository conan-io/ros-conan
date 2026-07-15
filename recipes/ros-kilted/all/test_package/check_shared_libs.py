"""Fail if any shared library under the ros-kilted install is missing a runtime dependency.

Loads every .so/.dylib/.dll it finds via the OS loader (ctypes) instead of parsing
ldd/otool output, so it catches the same "library not found" failures a consumer would
hit at runtime (this is the class of bug the macOS rpath fixes in finalize() exist for).
"""
import ctypes
import os
import sys

prefix = sys.argv[1]
is_windows = sys.platform == "win32"
is_macos = sys.platform == "darwin"


def is_lib(name):
    if is_windows:
        return name.lower().endswith(".dll")
    if is_macos:
        return name.endswith(".dylib")
    return ".so" in name


def load(path):
    return ctypes.WinDLL(path) if is_windows else ctypes.CDLL(path)


roots = [os.path.join(prefix, "lib")]
opt_dir = os.path.join(prefix, "opt")
if os.path.isdir(opt_dir):
    for vendor in os.listdir(opt_dir):
        for sub in ("lib", "lib64"):
            d = os.path.join(opt_dir, vendor, sub)
            if os.path.isdir(d):
                roots.append(d)

checked = 0
failures = []
for root_dir in roots:
    for root, _, files in os.walk(root_dir):
        if "site-packages" in root.split(os.sep):
            continue
        for name in files:
            path = os.path.join(root, name)
            if os.path.islink(path) or not is_lib(name):
                continue
            checked += 1
            try:
                load(path)
            except OSError as exc:
                failures.append(f"{path}: {exc}")

print(f"checked {checked} shared libraries under {prefix}")
if failures:
    print("missing runtime dependencies detected:")
    for failure in failures:
        print(f"  {failure}")
    sys.exit(1)
