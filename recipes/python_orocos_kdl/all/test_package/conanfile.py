from conan import ConanFile
from conan.tools.build import can_run, cross_building
from conan.tools.system import PyEnv


class TestPackageConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    test_type = "explicit"

    def requirements(self):
        self.requires(self.tested_reference_str)

    def generate(self):
        PyEnv(self).generate()

    def test(self):
        if not can_run(self) or cross_building(self):
            return
        py_env = PyEnv(self)
        cmd = f"{py_env.env_exe} -c \"import PyKDL; print(PyKDL.Vector())\""
        self.run(cmd, env="conanrun", scope="run")
