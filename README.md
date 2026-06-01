<div align="center">

# 🤖 ros-conan

**🚀 Conan recipes for building [ROS 2](https://docs.ros.org/) from source — consumable like any other Conan package.**

[![Conan create ros-kilted](https://github.com/conan-io/ros-conan/actions/workflows/conan-create-ros-kilted.yml/badge.svg)](https://github.com/conan-io/ros-conan/actions/workflows/conan-create-ros-kilted.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![ROS 2 Kilted](https://img.shields.io/badge/ROS%202-Kilted-22314E.svg)](https://docs.ros.org/en/kilted/)
[![Conan 2](https://img.shields.io/badge/Conan-2.x-6699cb.svg)](https://conan.io)
[![Platforms](https://img.shields.io/badge/platforms-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](#profiles)

<img src="examples/pose_estimation/assets/output.gif" alt="Pose estimation demo built end-to-end from Conan packages" width="640" />

<sub>End-to-end demo built from Conan packages — `ros-kilted` (desktop) + OpenCV + TensorFlow Lite. See <a href="examples/pose_estimation/readme.md"><code>examples/pose_estimation</code></a>.</sub>

</div>

---

## ✨ Why ros-conan?

- 📦 **One `conan install`.** Pull ROS 2 and every system dependency from a Conan remote — no `rosdep`, `apt`, `brew` or `choco` required.
- 🔌 **Drop-in for any build system.** Plain CMake projects, `colcon` workspaces, or anything else that speaks `CMake's find_package` can consume `ros-kilted`.
- 🔁 **Reproducible & cacheable.** Profile-pinned binaries, uploaded to Artifactory, resolved deterministically across machines and CI.
- 🐍 **Hermetic Python tooling.** `colcon-*`, `catkin_pkg`, `empy`, ... ship inside the package via Conan's `PyEnv`. No global `pip` pollution.

The recipes follow the official upstream development setup for each platform:

- 🪟 Windows: <https://docs.ros.org/en/kilted/Installation/Alternatives/Windows-Development-Setup.html>
- 🍎 macOS: <https://docs.ros.org/en/kilted/Installation/Alternatives/macOS-Development-Setup.html>
- 🐧 Linux: <https://docs.ros.org/en/kilted/Installation/Alternatives/Ubuntu-Development-Setup.html>

## Recipes

| Package      | Description                                                                                                                       |
| ------------ | --------------------------------------------------------------------------------------------------------------------------------- |
| `ros-kilted` | ROS 2 **Kilted** built from sources as a single Conan package. Variants: `core`, `base`, `desktop`, `desktop_full`. |

### Dependencies provided in this repository

These recipes are not currently available in [ConanCenter](https://conan.io/center/) (or
need patches) and are required by `ros-kilted` or its consumers:

| Package             | Description                                                |
| ------------------- | ---------------------------------------------------------- |
| `orocos_kdl`        | Orocos Kinematics and Dynamics C++ library (KDL).          |
| `python_orocos_kdl` | PyKDL — Python (PyBind11) bindings for Orocos KDL.         |

All other third-party libraries (OpenSSL, Boost, Qt, OpenCV, Eigen, spdlog, gtest, ...) are
pulled from [ConanCenter](https://conan.io/center/).

## Quick start

Add this repo as a [`local-recipes-index`](https://docs.conan.io/2/tutorial/conan_repositories/setup_local_recipes_index.html#local-recipes-index-repository)
remote and install `ros-kilted` like any other Conan package:

```bash
git clone https://github.com/conan-io/ros-conan.git
conan remote add ros-conan ./ros-conan --type=local-recipes-index

conan install --requires=ros-kilted/0.1.0 \
    --build=missing \
    --profile=ros-conan/profiles/windows-msvc
```

That's it — `ros-kilted` and the dependency recipes above resolve from this index, every other dependency comes from [ConanCenter](https://conan.io/center/).

### Variants

The `variant` option on `ros-kilted` selects which subset of ROS 2 packages is built:

| Variant        | Contents (mirrors upstream `ros2/variants`)                                                       |
| -------------- | ------------------------------------------------------------------------------------------------- |
| `core`         | `ros_core` metapackage (rcl, rclcpp, rclpy, rmw, common interfaces, ...). Default.                |
| `base`         | `ros_base` — adds tf2, kdl_parser, robot_state_publisher, ...                                     |
| `desktop`      | `desktop` — adds rviz2, demo nodes, visualization, ...                                            |
| `desktop_full` (WIP) | `desktop_full` — adds simulation & perception stacks (heaviest, longest to build).                |

Set it on the command line:

```bash
conan install --requires=ros-kilted/0.1.0 -o ros-kilted/*:variant=desktop --build=missing
```

or in a profile (see `profiles/windows-msvc` and `profiles/macos-clang`).

## Profiles

Reference profiles for the CI-supported platforms live in [`profiles/`](profiles):

| Profile                 | Target                                                                                  |
| ----------------------- | --------------------------------------------------------------------------------------- |
| `profiles/windows-msvc` | Windows x86_64, MSVC 19.4 (Visual Studio 2022), C++17, dynamic runtime.                 |
| `profiles/macos-clang`  | macOS arm64, apple-clang 21, libc++, C++17.                                             |

Both profiles pin a recent `cmake/*` as a global `tool_requires`, default `ros-kilted` to
the `desktop` variant and disable `opencv:with_ffmpeg` on Windows to keep the dependency
graph small.

## Examples

Sample projects consuming `ros-kilted` through Conan. Each has its own readme with build & run steps.

| Example                                                            | What it shows                                                                                                                                                |
| ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| [`consumer_cmake`](examples/consumer_cmake/readme.md)              | Minimal pure-CMake consumer using `rclcpp`. `find_package(rclcpp)` satisfied directly through `CMakeDeps` — no `colcon` needed.                              |
| [`consumer_colcon`](examples/consumer_colcon/readme.md)            | A `colcon` workspace (`dummy_lib` + `consumer_node`) that takes its toolchain and ROS runtime from Conan via the `ROSEnv` generator.                          |
| [`pose_estimation`](examples/pose_estimation/readme.md)            | End-to-end demo combining `ros-kilted` (`desktop`) + `opencv` + `tensorflow-lite` from ConanCenter to publish a `MarkerArray` skeleton from a video stream. |

## Developing the `ros-kilted` recipe

Use Conan's local development flow to iterate the recipe methods independently:

```bash
conan source     recipes/ros-kilted/all --version=0.1.0
conan install    recipes/ros-kilted/all --version=0.1.0 --build=missing --profile=profiles/windows-msvc
conan build      recipes/ros-kilted/all --version=0.1.0                 --profile=profiles/windows-msvc
conan export-pkg recipes/ros-kilted/all --version=0.1.0                 --profile=profiles/windows-msvc
```

Once happy with the result, run `conan create` to produce a final package and execute its
`test_package`:

```bash
conan create recipes/ros-kilted/all --version=0.1.0 --profile=profiles/windows-msvc
```

The recipe builds the merged `install/` of a colcon workspace it materialises under
`recipes/ros-kilted/all/ros2_ws/` (ignored by git). Build artefacts of the local development
flow can be cleared by deleting that directory.

## Continuous integration

GitHub Actions builds `ros-kilted` (`desktop` variant) on `windows-latest` (MSVC) and
`macos-latest` (apple-clang) for every push to `main` and every pull request, then runs all
`examples/*/ci_test_example.py` against the freshly produced package. Built binaries that
hit the workflow (not those already cached on ConanCenter) are uploaded to a private
Artifactory remote. See
[`.github/workflows/conan-create-ros-kilted.yml`](.github/workflows/conan-create-ros-kilted.yml).

## License

Recipe metadata and supporting files in this repository are licensed under the MIT License —
see [LICENSE](LICENSE). The upstream ROS 2 archives and the third-party libraries built by
these recipes are subject to their own licenses (see the ROS 2 project and each component).
