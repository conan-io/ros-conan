# ros-conan

[![Conan create ros-kilted](https://github.com/conan-io/ros-conan/actions/workflows/conan-create-ros-kilted.yml/badge.svg)](https://github.com/conan-io/ros-conan/actions/workflows/conan-create-ros-kilted.yml)

Conan recipes for building and packaging [ROS 2](https://docs.ros.org/) from sources. The
recipes follow the official upstream development setup for each platform:

- Windows: <https://docs.ros.org/en/kilted/Installation/Alternatives/Windows-Development-Setup.html>
- macOS: <https://docs.ros.org/en/kilted/Installation/Alternatives/macOS-Development-Setup.html>
- Linux: <https://docs.ros.org/en/kilted/Installation/Alternatives/Ubuntu-Development-Setup.html>

The goal is to make ROS 2 consumable from any Conan-based project (plain CMake, `colcon`
workspaces, or other build systems) with a single `conan install` step. System dependencies
are resolved through Conan instead of `rosdep` / `apt` / `brew` / `choco`, and most of the
Python build tooling (`colcon-*`, `catkin_pkg`, `empy`, ...) is provisioned inside the
package via Conan's `PyEnv`.

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

## Usage

Add this repository as a [`local-recipes-index`](https://docs.conan.io/2/tutorial/conan_repositories/setup_local_recipes_index.html#local-recipes-index-repository)
remote, then `ros-kilted` (and the dependency recipes above) resolve like any other Conan
package:

```bash
git clone https://github.com/conan-io/ros-conan.git
conan remote add ros-conan ./ros-conan --type=local-recipes-index
```

Install or build from the index, for example:

```bash
conan install --requires=ros-kilted/0.1.0 \
    --build=missing \
    --profile=ros-conan/profiles/windows-msvc
```

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

Sample projects consuming `ros-kilted` through Conan. Each example has its own readme with
build & run steps:

- [`examples/consumer_cmake`](examples/consumer_cmake/readme.md) — Minimal pure-CMake
  consumer using `rclcpp`. Shows how `find_package(rclcpp)` is satisfied directly through
  `CMakeDeps` (no `colcon` needed).
- [`examples/consumer_colcon`](examples/consumer_colcon/readme.md) — A `colcon` workspace
  (`dummy_lib` + `consumer_node`) that takes its toolchain and ROS runtime from Conan
  through the `ROSEnv` generator.
- [`examples/pose_estimation`](examples/pose_estimation/readme.md) — End-to-end demo
  combining `ros-kilted` (`desktop` variant) with `opencv` and `tensorflow-lite` from
  ConanCenter to publish a `MarkerArray` of a human skeleton extracted from a video stream.

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
