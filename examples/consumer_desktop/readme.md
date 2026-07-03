# consumer_desktop

Headless check for the `desktop` variant of `ros-kilted`: installs the package with
GUI tooling (`rviz2`, `rqt`, Qt/PyQt5 bindings) and checks it starts up without a
real display, using Qt's offscreen platform plugin instead of `Xvfb`.

On Windows, `rviz2` doesn't respect the offscreen plugin and hangs instead of
exiting, so there this only checks the packages resolve (`ros2 pkg prefix`)
instead of launching them.

[← back to main README](../../README.md)

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
ros2 pkg prefix rviz2
ros2 pkg prefix rqt_gui
```

The exact CI invocation lives in [`ci_test_example.py`](ci_test_example.py).
