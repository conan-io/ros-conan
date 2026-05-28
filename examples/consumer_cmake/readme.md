# consumer_cmake

Minimal example that consumes `ros-kilted` from a **pure CMake** project — no `colcon` and
no `ament_cmake`. Useful when you want to embed `rclcpp` into an application that already
uses Conan for its dependency management.

[← back to main README](../../README.md)

## What it does

A single executable `consumer_node` links against `rclcpp::rclcpp`, creates a node and
emits one log line:

```cpp
auto node = std::make_shared<rclcpp::Node>("conan_test_package_node");
RCLCPP_INFO(node->get_logger(), "Conan consumer_node: rclcpp linked and node started.");
```

See [`src/main.cpp`](src/main.cpp).

## How it is wired

- [`conanfile.py`](conanfile.py) declares a single requirement on `ros-kilted/0.1.0` and
  uses the `CMakeDeps` + `CMakeToolchain` generators with the standard `cmake_layout()`.
- [`CMakeLists.txt`](CMakeLists.txt) uses plain `find_package(rclcpp REQUIRED)`. The ROS 2
  CMake configs are provided by Conan, not by sourcing a `setup.{bash,bat,ps1}` script.

## Prerequisites

- A C++17 compiler (MSVC 19.4 / apple-clang 21 / GCC 11+ ...).
- CMake ≥ 3.22 (the [profiles](../../profiles) tool-require `cmake/3.29.3`).
- A Conan remote that exposes `ros-kilted` — see the
  [main README](../../README.md#usage).

## Build & run

From this directory:

```bash
conan install . --profile=../../profiles/windows-msvc --build=missing
conan build   . --profile=../../profiles/windows-msvc
```

Then run the binary produced by `cmake_layout()`:

```bat
:: Windows
build\Release\consumer_node.exe
```

```bash
# macOS / Linux
./build/Release/consumer_node
```

Expected output (truncated):

```text
[INFO] [...] [conan_test_package_node]: Conan consumer_node: rclcpp linked and node started.
```

The exact CI invocation lives in [`ci_test_example.py`](ci_test_example.py).
