from conan import ConanFile
from conan.tools.cmake import cmake_layout


class PoseEstimationRecipe(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "CMakeDeps", "CMakeToolchain"

    def requirements(self):
        self.requires("ros-kilted/2026.06.17")
        self.requires("tensorflow-lite/2.15.0")
        self.requires("opencv/4.12.0")
        # ruy (via tensorflow-lite) pins cpuinfo/cci.20231129 exactly, while
        # libsvtav1/xnnpack use cpuinfo/[>=cci.20231129] which resolves to
        # cci.20251210 on a fresh resolve — override to a single version.
        self.requires("cpuinfo/cci.20231129", override=True)

    def layout(self):
        cmake_layout(self)
