# conan_workspace

Same layout as [`consumer_colcon`](../consumer_colcon/readme.md) — two packages under
`src/` — but orchestrated with a [Conan workspace](https://docs.conan.io/2/tutorial/developing_packages/workspaces.html)
instead of `colcon`. There is no `package.xml`, no `ament_cmake`, and no `colcon`:
each package is a plain CMake project with its own `conanfile.py`. Workspace packages
are resolved as [editables](https://docs.conan.io/2/tutorial/developing_packages/editable_packages.html)
and built in dependency order.

- `dummy_lib` — a static library with no ROS dependencies, used to demonstrate
  cross-package linking inside the workspace.
- `consumer_node` — depends on `dummy_lib` and `ros-kilted` (`rclcpp`), prints a
  message and starts a short-lived node.

[← back to main README](../../README.md)

## Layout

```text
conan_workspace/
├── conanws.yml              # workspace root + package inventory
└── src/
    ├── dummy_lib/
    │   ├── conanfile.py     # replaces package.xml
    │   ├── CMakeLists.txt
    │   ├── include/
    │   └── src/
    └── consumer_node/
        ├── conanfile.py
        ├── CMakeLists.txt
        └── src/
```

Conan walks up from the current directory until it finds `conanws.yml` and/or
`conanws.py`; that folder is the workspace root. Paths in `conanws.yml` are
relative to it.

This example only needs `conanws.yml`. A `conanws.py` is optional Python
customization (`root_conanfile()` for a monolithic super-build, custom
`add`/`clean`/`build_order`, or `get_ref()` when name/version come from
`python_requires`). Orchestrated `conan workspace build` does not use any of
that.

This example uses the **orchestrated** workspace flow (`conan workspace build`),
which is the closest analogue to `colcon build`: each package is configured and
built on its own, in topological order, with workspace members consumed as
editables.

Conan workspaces are experimental and subject to breaking changes — see the
[Conan stability notes](https://docs.conan.io/2/introduction.html#stability).

## How it is wired

| Piece | Role |
| ----- | ---- |
| [`conanws.yml`](conanws.yml) | Lists `src/dummy_lib` and `src/consumer_node` as workspace packages. |
| [`src/dummy_lib/conanfile.py`](src/dummy_lib/conanfile.py) | CMake library recipe: `CMakeToolchain` + `CMakeDeps`, `cmake_layout()`. |
| [`src/consumer_node/conanfile.py`](src/consumer_node/conanfile.py) | Requires `dummy_lib/0.1` (editable, from this workspace) and `ros-kilted/2026.06.17`. |
| CMake | Plain `find_package(dummy_lib)` / `find_package(rclcpp)` — configs come from Conan, not from sourcing a ROS `setup` script. |

`conan workspace build` is `conan build` for every workspace package, in the
right order. External dependencies (`ros-kilted` and its graph) are installed
from the cache/remotes; `dummy_lib` is never looked up as a binary because it
is in the workspace.

## Prerequisites

- A C++17 compiler.
- CMake ≥ 3.22 (the [profile](../../profiles/ros) tool-requires `cmake/3.29.3`).
- Conan 2.12+ (`conan workspace build`; this repo is exercised with Conan 2.31).
- A Conan remote that exposes `ros-kilted` — see the
  [main README](../../README.md#quick-start).

## Build & run

From this directory:

```bash
conan workspace build --profile ../../profiles/ros --build=missing
```

Then activate the consumer's Conan run environment and execute the node:

**Windows (cmd):**

```bat
call src\consumer_node\build\generators\conanrun.bat
src\consumer_node\build\Release\consumer_node.exe
```

**macOS / Linux (bash/zsh):**

```bash
. ./src/consumer_node/build/Release/generators/conanrun.sh
./src/consumer_node/build/Release/consumer_node
```

Expected output (truncated):

```text
[dummy_lib] hello from library
[INFO] [...] [workspace_consumer_node]: Conan workspace consumer_node: rclcpp linked and node started.
```

The exact CI invocation lives in [`ci_test_example.py`](ci_test_example.py).
