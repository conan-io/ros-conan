# consumer_desktop

Installs the `desktop` variant of `ros-kilted`, which adds GUI tooling (`rviz2`, `rqt`,
Qt/PyQt5 bindings) on top of the `core` packages, and runs it.

[← back to main README](../../README.md)

## Run

From this directory:

```bash
conan install . --profile=../../profiles/ros --build=missing

**Linux/macOS:**

```bash
. ./build/Release/generators/conanrun.sh
rviz2
rqt
```

**Windows (cmd):**

```bat
call build\generators\conanrun.bat
rviz2
rqt
```
