"""Run unit tests for the ROS consumer custom command."""

import sys
from pathlib import Path

from test.examples_tools import run

repo = Path(__file__).resolve().parents[1]
run(f'"{sys.executable}" -m unittest discover -s "{repo / "test"}" -p "test_ros_pkgxml.py" -v')
