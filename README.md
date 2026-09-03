# ros-conan

[![Conan create ros-kilted](https://github.com/conan-io/ros-conan/actions/workflows/conan-create-ros-kilted.yml/badge.svg)](https://github.com/conan-io/ros-conan/actions/workflows/conan-create-ros-kilted.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Conan recipes for building [ROS 2](https://docs.ros.org/) from source. Pull ROS 2 and all its dependencies with a single `conan install`, no `rosdep`, `apt`, `brew` or `choco` required. Works with plain CMake projects, `colcon` workspaces, and [Conan workspaces](https://docs.conan.io/2/tutorial/developing_packages/workspaces.html), on Windows, macOS and Linux.

---

## Prerequisites

- **Install/use Python 3.12**
  [REP-2000](https://github.com/ros2/ros2_documentation/blob/kilted/source/Releases/Release-Kilted-Kaiju.rst#id22) lists the 3.12.3 Python version as the reference version on the Tier 1 platforms.

- **Install Conan 2 in a Python virtual environment**:

  ```bash
  python -m venv .venv
  source .venv/bin/activate  # Windows: .venv\Scripts\activate
  pip install conan
  conan profile detect --force
  ```

- **Install the ROS custom commands** (once per Conan home), so `package.xml`
  workspaces can call `conan ros:install` without writing a `conanfile`:

  ```bash
  conan config install /path/to/ros-conan -sf extensions -tf extensions
  ```

## Quick start

```bash
git clone https://github.com/conan-io/ros-conan.git
conan config install ./ros-conan -sf extensions -tf extensions
conan remote add ros-conan ./ros-conan --type=local-recipes-index

conan install --requires=ros-kilted/2026.06.17 \
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

To build a different variant, pass the variant option with `-o`:

```bash
conan install --requires=ros-kilted/2026.06.17 \
    --profile=ros-conan/profiles/ros \
    -o ros-kilted/*:variant=desktop \
    --build=missing
```

> [!NOTE]
> ROS is too large and heterogeneous to ship as a single complete catalog. The
> variants above follow the usual distro metapackages (`ros-core`, `ros-base`,
> `desktop`, `desktop-full`), as they cover the common stacks, not every package in
> rosdistro. C++ libraries that ROS projects often need (OpenCV, PCL, BehaviorTree.CPP,
> Eigen...) already live in [ConanCenter](https://conan.io/center/) and can be added next
> to `ros-kilted` like any other Conan requirement.
>
> **If you need extra ROS packages that are not in those variants**,
> [open an issue](https://github.com/conan-io/ros-conan/issues) with what you are missing.
> We can then look at the easiest way to add them. Thank you!

## From a ROS `package.xml`

If the project is a colcon workspace (or any tree of `package.xml` files) whose
ROS dependencies are already in a `ros-kilted` variant (`core`, `base`, or
`desktop`), generate the Conan consumer file from those manifests instead of
writing a `conanfile` by hand:

```bash
conan ros:install --build=missing
```

`conan ros:install` composes the ROS profile overlay (C++17, `cmake/3.29.3`, Python
version) on top of your profile. Pass `-pr/--profile` to choose a different base;
if you omit it, Conan's `default` profile is used.

`conan ros:init` only writes `conanfile.txt`. `conan ros:init --dry-run` prints
the mapping (local packages vs `ros-kilted` vs unknown) without writing files.
Unknown dependencies that are not in `ros-kilted` and not local to the workspace
are an error; extra ROS stacks such as Nav2 are not generated in this version.

See [`examples/consumer_colcon`](examples/consumer_colcon/readme.md) for a full
`colcon` build after `conan ros:install`.

## Versioning

`ros-kilted` uses **calendar versioning** that mirrors the upstream
[`ros/rosdistro` sync tag](https://github.com/ros/rosdistro/tags) the recipe is
pinned to. The Conan version `YYYY.MM.DD` maps 1:1 to the rosdistro tag
`kilted/YYYY-MM-DD`. After bumping that pin, regenerate the consumer catalog with
`python tools/gen_kilted_catalog.py` (writes `extensions/commands/ros/data/kilted_variants.json`).

## Recipes

| Package             | Description                                         |
| ------------------- | --------------------------------------------------- |
| [`ros-kilted`](recipes/ros-kilted/all/conanfile.py)        | ROS 2 Kilted built from source as a single package. |
| [`orocos_kdl`](recipes/orocos_kdl/all/conanfile.py)        | Orocos KDL C++ library.                             |
| [`python_orocos_kdl`](recipes/python_orocos_kdl/all/conanfile.py) | PyKDL, Python bindings for Orocos KDL.              |

`orocos_kdl` and `python_orocos_kdl` are not in ConanCenter and are required by `ros-kilted`.

## Examples

| Example                                                       | What it shows                                                               |
| ------------------------------------------------------------- | --------------------------------------------------------------------------- |
| [`consumer_cmake`](examples/consumer_cmake/readme.md)         | Pure-CMake consumer using `rclcpp` via `CMakeDeps`, no `colcon` needed.     |
| [`consumer_colcon`](examples/consumer_colcon/readme.md)       | `colcon` workspace: `conan ros:install` from `package.xml`, then `ROSEnv`. |
| [`conan_workspace`](examples/conan_workspace/readme.md)       | Same `src/` layout as `consumer_colcon`, orchestrated with a Conan workspace (CMake only). |
| [`pose_estimation`](examples/pose_estimation/readme.md)       | `ros-kilted` + `opencv` + `tensorflow-lite` publishing a skeleton overlay.  |
| [`consumer_desktop`](examples/consumer_desktop/readme.md)     | Installs the `desktop` variant and runs its GUI tooling (`rviz2`, `rqt`).  |

## Tested platforms on CI

| OS | Architecture | Variants |
| -- | ------------ | -------- |
| Windows Server 2022 | x86_64 | `core`, `desktop` |
| Ubuntu 24.04 | x86_64 | `core`, `desktop` |
| Ubuntu 24.04 | arm64 | `core` |
| macOS 15 | x86_64, arm64 | `core`, `desktop` |

## License

MIT, see [LICENSE](LICENSE).
