# consumer_colcon

Example showing how a [`colcon`](https://colcon.readthedocs.io/) workspace can pick up
`ros-kilted` from Conan as if it were a system-installed ROS distribution. Two ROS packages
are built side-by-side:

- `dummy_lib` — a plain `ament_cmake` static library with no ROS dependencies, used to
  demonstrate cross-package linking inside the workspace.
- `consumer_node` — depends on `dummy_lib` and `rclcpp`, prints a message and starts a
  short-lived node.

[← back to main README](../../README.md)

## How it is wired

[`conanfile.txt`](conanfile.txt) requires `ros-kilted/0.1.0` and pulls in the generators
that make `colcon` discover ROS 2:

| Generator         | Role                                                                                              |
| ----------------- | ------------------------------------------------------------------------------------------------- |
| `CMakeToolchain`  | Produces `conan_toolchain.cmake` — pinned compiler/std/runtime for every CMake project.            |
| `CMakeDeps`       | Generates `<Pkg>-config.cmake` for every Conan dependency, so `find_package` just works.          |
| `VCVars`          | Sets up the MSVC environment on Windows.                                                          |
| `ROSEnv`          | Generates `conanrosenv.{bat,sh}` — exposes `AMENT_PREFIX_PATH`, `CMAKE_PREFIX_PATH`, `PYTHONPATH`, and the ROS install/runtime so `colcon` finds messages, Python tooling and runtime libraries. |

## Prerequisites

- A C++17 compiler.
- CMake ≥ 3.22 (the [profiles](../../profiles) tool-require `cmake/3.29.3`).
- `colcon` and `catkin_pkg` available on `PATH`:

  ```bash
  python -m pip install --upgrade colcon-common-extensions catkin_pkg
  ```

  On macOS, make sure the `python` that runs `colcon` is the same one that `ament_cmake`
  picks up via `find_package(Python3)` — different Python versions on `PATH` cause
  `catkin_pkg` to land in the wrong `site-packages`. The CI example pins this explicitly
  with `-DPython3_EXECUTABLE=...`.

## Build & run

From this directory:

```bash
conan install . --profile=../../profiles/windows-msvc --build=missing
```

Activate the Conan-generated ROS environment and let `colcon` drive the rest:

**Windows (cmd):**

```bat
call build\generators\conanrosenv.bat
colcon build --event-handlers console_cohesion+
call install\setup.bat

install\consumer_node\lib\consumer_node\consumer_node.exe
```

**macOS / Linux (bash/zsh):**

```bash
. ./build/Release/generators/conanrosenv.sh
colcon build --event-handlers console_cohesion+
. ./install/setup.sh

./install/consumer_node/lib/consumer_node/consumer_node
```

Expected output (truncated):

```text
Hello from dummy_lib
[INFO] [...] [colcon_consumer_node]: colcon consumer_node: rclcpp linked and node started.
```

## Known limitations

The `ros2` CLI (Python entry points such as `ros2 run`, `ros2 launch`, ...) is not yet
exposed by `ros-kilted`, so the canonical invocation

```bash
# after `colcon build` and sourcing install/setup.{sh,bat}
ros2 run consumer_node consumer_node
```

does not work today. Run the executable directly from the `install/` tree as shown above.

The exact CI invocation (with the Python-interpreter pinning mentioned above) lives in
[`ci_test_example.py`](ci_test_example.py).
