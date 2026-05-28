# pose_estimation

End-to-end demo that uses `ros-kilted` (`desktop` variant) together with **OpenCV** and
**TensorFlow Lite** — all resolved through Conan — to publish a 3D `MarkerArray` of a human
skeleton extracted from a video stream. The skeleton can be visualised live in `rviz2`.

![pose estimation output](assets/output.gif)

## What it does

[`src/pose-estimation.cpp`](src/pose-estimation.cpp):

1. Loads the [MoveNet SinglePose Lightning](https://tfhub.dev/google/lite-model/movenet/singlepose/lightning/tflite/float16/4)
   TFLite model via `tflite::FlatBufferModel`.
2. Reads frames from a video file (`assets/dancing.mp4`), a still image, or a connected
   camera using OpenCV.
3. Runs inference on each frame and reconstructs a 17-joint skeleton.
4. Publishes joints + bones as `visualization_msgs::msg::MarkerArray` from an `rclcpp::Node`
   so the skeleton can be visualised in `rviz2`.

## How it is wired

- [`conanfile.txt`](conanfile.txt) — requires `ros-kilted/0.1.0` (`desktop` variant),
  `opencv/4.9.0` and `tensorflow-lite/2.12.0`.
- [`CMakeLists.txt`](CMakeLists.txt) — a single executable linked against
  `rclcpp::rclcpp`, `opencv::opencv`, `tensorflow::tensorflowlite` and the
  `geometry_msgs` / `visualization_msgs` targets.
- [`assets/`](assets) — ships the MoveNet TFLite model and a sample dancing video used by
  default when no `--video` / `--image` / `--camera` flag is provided.

## Prerequisites

- A C++17 compiler, CMake ≥ 3.15.
- A Conan remote that exposes `ros-kilted` — see the
  [main README](../../README.md#usage).

## Build

From this directory:

```bash
conan install . --profile=../../profiles/windows-msvc --build=missing
```

**Windows (cmd):**

```bat
call build\generators\conanbuild.bat
cmake --preset conan-default
cmake --build --preset conan-release
```

**macOS / Linux (bash/zsh):**

```bash
. ./build/Release/generators/conanbuild.sh
cmake --preset conan-release
cmake --build --preset conan-release
```

## Run

The executable resolves the model and the sample video relatively (`assets/lite-model_...tflite`,
`assets/dancing.mp4`), so run it **from this directory** so those paths exist:

```bat
:: Windows
build\Release\pose-estimation.exe
```

```bash
# macOS / Linux
./build/Release/pose-estimation
```

### Command-line options

| Flag                  | Description                                                      |
| --------------------- | ---------------------------------------------------------------- |
| `--model=<path>`      | Override the TFLite model file.                                  |
| `--video=<path>`      | Override the input video file.                                   |
| `--image=<path>`      | Process a single image instead of a video.                       |
| `--camera`            | Capture from the default camera (`cv::VideoCapture(0)`).         |
| `--no-windows`        | Disable OpenCV GUI windows (useful for CI / headless runs).      |

### Visualising in rviz2

```bash
conan run "ros2 run rviz2 rviz2"
```

The headless CI invocation lives in [`ci_test_example.py`](ci_test_example.py).
