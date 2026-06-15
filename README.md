<div align="center">

# ros-conan

[![Conan create ros-kilted](https://github.com/conan-io/ros-conan/actions/workflows/conan-create-ros-kilted.yml/badge.svg)](https://github.com/conan-io/ros-conan/actions/workflows/conan-create-ros-kilted.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![ROS 2 Kilted](https://img.shields.io/badge/ROS%202-Kilted-22314E.svg)](https://docs.ros.org/en/kilted/)
[![Conan 2](https://img.shields.io/badge/Conan-2.x-6699cb.svg)](https://conan.io)

</div>

---

## Quick start

```bash
git clone https://github.com/conan-io/ros-conan.git
conan remote add ros-conan ./ros-conan --type=local-recipes-index

conan install --requires=ros-kilted/0.1.0 \
    -o ros-kilted/*:variant=desktop \
    --build=missing
```

`ros-kilted` and its bundled dependencies resolve from this index. Everything else comes from [ConanCenter](https://conan.io/center/).

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
