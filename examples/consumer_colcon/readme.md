# consumer_colcon

Example showing how a [`colcon`](https://colcon.readthedocs.io/) workspace can pick up
`ros-kilted` from Conan as if it were a system-installed ROS distribution. Two ROS packages
are built side-by-side:

- `dummy_lib` — a plain `ament_cmake` static library with no ROS dependencies, used to
  demonstrate cross-package linking inside the workspace.
- `consumer_node` — depends on `dummy_lib` and `rclcpp`, prints a message and starts a
  short-lived node.

There is **no hand-written `conanfile`**. `conan ros:install` reads the `package.xml` files
under `src/` and generates one.

[← back to main README](../../README.md)

## How it is wired

`conan ros:install` scans `package.xml`, ignores workspace-local names (`dummy_lib`), maps
the rest (`ament_cmake`, `rclcpp`) onto the smallest `ros-kilted` variant that contains them
(`core`), and writes `conanfile.txt` with the generators that make `colcon` discover ROS 2:

| Generator         | Role                                                                                              |
| ----------------- | ------------------------------------------------------------------------------------------------- |
| `CMakeToolchain`  | Produces `conan_toolchain.cmake` — pinned compiler/std/runtime for every CMake project.            |
| `CMakeDeps`       | Generates `<Pkg>-config.cmake` for every Conan dependency, so `find_package` just works.          |
| `VCVars`          | Sets up the MSVC environment on Windows.                                                          |
| `ROSEnv`          | Generates `conanrosenv.{bat,sh}` — exposes `AMENT_PREFIX_PATH`, `CMAKE_PREFIX_PATH`, `PYTHONPATH`, and the ROS install/runtime so `colcon` finds messages, Python tooling and runtime libraries. |

The command always composes the [ROS profile overlay](../../extensions/commands/ros/data/ros.profile)
on top of your Conan profile (`default` if you pass none): C++17, `cmake/3.29.3`, and the
`ros-kilted` Python version. Extra `-pr/--profile` flags are still the base; the overlay is
appended after them.

## Prerequisites

- A C++17 compiler.
- CMake ≥ 3.22 (the overlay tool-requires `cmake/3.29.3`).
- Conan 2 and a detected default profile — see the
  [main README](../../README.md#prerequisites).

Clone this repository, install the `ros:*` commands into the Conan home, and
register the clone as a [local-recipes-index](https://docs.conan.io/2/devops/devops_local_recipes_index.html)
remote (once per machine):

```bash
git clone https://github.com/conan-io/ros-conan.git
cd ros-conan
conan config install . -sf extensions -tf extensions
conan remote add ros-conan . --type=local-recipes-index
```

`conan config install` copies the custom commands. `conan remote add` points Conan
at the `recipes/` tree in this clone so `ros-kilted` resolves like any other remote.
ConanCenter remains the source for everything else.

If the clone is already on disk, from `examples/consumer_colcon` the same two
commands are:

```bash
conan config install ../.. -sf extensions -tf extensions
conan remote add ros-conan ../.. --type=local-recipes-index
```

`colcon` and `catkin_pkg` are shipped by `ros-kilted`. Activating
`conanrosenv.{bat,sh}` puts them on `PATH` / `PYTHONPATH`; they do not need a
separate system or pip install.

## Build & run

From `examples/consumer_colcon` in the clone:

```bash
conan ros:install --build=missing
```

Optional: `conan ros:install --profile=myprofile --build=missing` uses `myprofile` as the
base and still applies the ROS overlay on top.

`conan ros:init --dry-run` prints the mapping without installing. To write
`conanfile.txt` without installing, use `conan ros:init`.

Activate the Conan-generated ROS environment and let `colcon` drive the rest:

**Windows (cmd):**

```bat
call build\generators\conanrosenv.bat
colcon build --event-handlers console_cohesion+
call install\setup.bat

ros2 run consumer_node consumer_node
```

**macOS / Linux (bash/zsh):**

```bash
. ./build/Release/generators/conanrosenv.sh
colcon build --event-handlers console_cohesion+
. ./install/setup.sh

ros2 run consumer_node consumer_node
```

`ros2` and `colcon` are shipped by `ros-kilted` (`Scripts/` on Windows, `bin/` on
macOS/Linux) and `conanrosenv.{bat,sh}` puts them on `PATH` together with the
`AMENT_PREFIX_PATH` / `PYTHONPATH` entries they need. Sourcing the workspace's
`install/setup.{bat,sh}` then prepends the freshly built `consumer_node` to that
`AMENT_PREFIX_PATH`, so `ros2 run` (or any other `ros2` subcommand) resolves it like
on a system-installed ROS 2.

If you prefer to skip `ros2`, the executable is also reachable directly from the
install tree:

```bat
install\consumer_node\lib\consumer_node\consumer_node.exe
```

```bash
./install/consumer_node/lib/consumer_node/consumer_node
```

Expected output (truncated):

```text
[dummy_lib] hello from library
[INFO] [...] [colcon_consumer_node]: colcon consumer_node: rclcpp linked and node started.
```

The exact CI invocation lives in [`ci_test_example.py`](ci_test_example.py).
