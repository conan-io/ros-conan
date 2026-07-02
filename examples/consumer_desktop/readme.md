# consumer_desktop

Headless check for the `desktop` variant of `ros-kilted`: installs the package with
GUI tooling enabled (`rviz2`, `rqt`, Qt/PyQt5 bindings) and checks the binaries start up
correctly without a real display.

[← back to main README](../../README.md)

## How it is wired

[`conanfile.txt`](conanfile.txt) requires `ros-kilted/2026.06.17` with `variant=desktop`
and uses `VirtualRunEnv` to generate `conanrun.{bat,sh}`, exposing `PATH`, `PYTHONPATH`
and `QT_PLUGIN_PATH` for the prebuilt binaries — no build step needed.

`QT_QPA_PLATFORM=offscreen` forces Qt to use its built-in offscreen platform plugin
instead of a real windowing system, so this runs the same way on Linux, macOS and
Windows CI runners without needing `Xvfb` or any other display server.

## Run

From this directory:

```bash
conan install . --profile=../../profiles/ros --build=missing -o ros-kilted/*:variant=desktop
```

**Linux/macOS:**

```bash
. ./build/Release/generators/conanrun.sh
QT_QPA_PLATFORM=offscreen rviz2 --help
QT_QPA_PLATFORM=offscreen rqt --help
```

**Windows (cmd):**

```bat
call build\generators\conanrun.bat
set QT_QPA_PLATFORM=offscreen
rviz2 --help
rqt --help
```

The exact CI invocation lives in [`ci_test_example.py`](ci_test_example.py).
