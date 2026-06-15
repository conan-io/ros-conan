# ros-conan

[![Conan create ros-kilted](https://github.com/conan-io/ros-conan/actions/workflows/conan-create-ros-kilted.yml/badge.svg)](https://github.com/conan-io/ros-conan/actions/workflows/conan-create-ros-kilted.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Conan recipes for building [ROS 2](https://docs.ros.org/) from source. Pull ROS 2 and all its dependencies with a single `conan install`, no `rosdep`, `apt`, `brew` or `choco` required. Works with plain CMake projects and `colcon` workspaces, on Windows, macOS and Linux.

---

## Quick start

```bash
git clone https://github.com/conan-io/ros-conan.git
conan remote add ros-conan ./ros-conan --type=local-recipes-index

conan install --requires=ros-kilted/0.1.0 \
    --profile=ros-conan/profiles/ros \
    --build=missing
```

`ros-kilted` and its bundled dependencies resolve from this index. Everything else comes from [ConanCenter](https://conan.io/center/).

Activate the Conan virtual run environment and verify:

```bash
# Linux / macOS
source conanrun.sh
ros2 pkg list
```

```bat
REM Windows
conanrun.bat
ros2 pkg list
```

### Variants

| Variant              | Contents                                                         |
| -------------------- | ---------------------------------------------------------------- |
| `core`               | rcl, rclcpp, rclpy, rmw, common interfaces. Default.            |
| `base`               | Adds tf2, kdl_parser, robot_state_publisher.                     |
| `desktop`            | Adds rviz2, demo nodes, visualization tools.                     |
| `desktop_full` (WIP) | Adds simulation and perception stacks.                           |

## Recipes

| Package             | Description                                         |
| ------------------- | --------------------------------------------------- |
| `ros-kilted`        | ROS 2 Kilted built from source as a single package. |
| `orocos_kdl`        | Orocos KDL C++ library.                             |
| `python_orocos_kdl` | PyKDL, Python bindings for Orocos KDL.              |

`orocos_kdl` and `python_orocos_kdl` are not in ConanCenter and are required by `ros-kilted`.

## Examples

| Example                                                       | What it shows                                                               |
| ------------------------------------------------------------- | --------------------------------------------------------------------------- |
| [`consumer_cmake`](examples/consumer_cmake/readme.md)         | Pure-CMake consumer using `rclcpp` via `CMakeDeps`, no `colcon` needed.     |
| [`consumer_colcon`](examples/consumer_colcon/readme.md)       | `colcon` workspace consuming the ROS runtime from Conan via `ROSEnv`.       |
| [`pose_estimation`](examples/pose_estimation/readme.md)       | `ros-kilted` + `opencv` + `tensorflow-lite` publishing a skeleton overlay.  |

## License

MIT, see [LICENSE](LICENSE).
