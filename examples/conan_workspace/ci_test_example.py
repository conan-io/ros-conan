import platform

from test.examples_tools import VARIANT_ARGS, run

run(
    f"conan workspace build --profile ../../profiles/ros {VARIANT_ARGS} --build=missing"
)

if platform.system() == "Windows":
    run(
        r"call .\src\consumer_node\build\generators\conanrun.bat && "
        r".\src\consumer_node\build\Release\consumer_node.exe"
    )
else:
    run(
        ". ./src/consumer_node/build/Release/generators/conanrun.sh && "
        "./src/consumer_node/build/Release/consumer_node"
    )
