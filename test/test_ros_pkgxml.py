from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "extensions" / "commands" / "ros"))

import ros_pkgxml  # noqa: E402


def _write_pkg(root: Path, name: str, depends: list[str], subdir: str | None = None) -> None:
    pkg_dir = root / (subdir or name)
    pkg_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        '<?xml version="1.0"?>',
        '<package format="3">',
        f"  <name>{name}</name>",
        "  <version>0.0.0</version>",
        "  <description>test</description>",
        '  <maintainer email="a@b.c">t</maintainer>',
        "  <license>MIT</license>",
        "  <buildtool_depend>ament_cmake</buildtool_depend>",
    ]
    lines.extend(f"  <depend>{d}</depend>" for d in depends)
    lines.append("</package>")
    (pkg_dir / "package.xml").write_text("\n".join(lines) + "\n", encoding="utf-8")


CATALOG = {
    "distro": "kilted",
    "conan_version": "2026.06.17",
    "variants": {
        "core": ["ament_cmake", "rclcpp", "std_msgs"],
        "base": ["ament_cmake", "rclcpp", "std_msgs", "tf2", "kdl_parser"],
        "desktop": ["ament_cmake", "rclcpp", "std_msgs", "tf2", "kdl_parser", "rviz2"],
    },
}


class TestRosPkgXml(unittest.TestCase):
    def test_core_from_rclcpp_and_local_dep(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_pkg(root, "dummy_lib", [])
            _write_pkg(root, "consumer_node", ["dummy_lib", "rclcpp"])
            mapping = ros_pkgxml.map_workspace(root, catalog=CATALOG)
            self.assertEqual(mapping.variant, "core")
            self.assertEqual(mapping.requires, "ros-kilted/2026.06.17")
            self.assertIn("dummy_lib", mapping.local_packages)
            self.assertIn("consumer_node", mapping.local_packages)
            self.assertEqual(mapping.covered["rclcpp"], "core")
            self.assertEqual(mapping.covered["ament_cmake"], "core")
            self.assertNotIn("dummy_lib", mapping.covered)

    def test_base_from_tf2(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_pkg(root, "nav_node", ["tf2"])
            mapping = ros_pkgxml.map_workspace(root, catalog=CATALOG)
            self.assertEqual(mapping.variant, "base")
            self.assertEqual(mapping.covered["tf2"], "base")

    def test_unknown_dependency_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_pkg(root, "nav_node", ["nav2_bringup"])
            with self.assertRaises(ros_pkgxml.RosConsumerError) as ctx:
                ros_pkgxml.map_workspace(root, catalog=CATALOG)
            self.assertIn("nav2_bringup", str(ctx.exception))
            self.assertIn("not supported yet", str(ctx.exception))

    def test_variant_too_small(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_pkg(root, "viz", ["rviz2"])
            with self.assertRaises(ros_pkgxml.RosConsumerError) as ctx:
                ros_pkgxml.map_workspace(root, catalog=CATALOG, variant="core")
            self.assertIn("smaller than required", str(ctx.exception))

    def test_skips_ament_ignore_and_build_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_pkg(root, "ok", ["rclcpp"], subdir="src/ok")
            ignored = root / "src" / "ignored"
            ignored.mkdir(parents=True)
            (ignored / "AMENT_IGNORE").write_text("", encoding="utf-8")
            _write_pkg(root, "ignored_pkg", ["nav2_bringup"], subdir="src/ignored/pkg")
            _write_pkg(root, "stale", ["nav2_bringup"], subdir="build/stale")
            mapping = ros_pkgxml.map_workspace(root, catalog=CATALOG)
            self.assertEqual(mapping.local_packages, {"ok"})
            self.assertEqual(mapping.variant, "core")

    def test_render_conanfile(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_pkg(root, "n", ["rclcpp"])
            mapping = ros_pkgxml.map_workspace(root, catalog=CATALOG)
            text = ros_pkgxml.render_conanfile_txt(mapping)
            self.assertIn("ros-kilted/2026.06.17", text)
            self.assertIn("ros-kilted/*:variant=core", text)
            self.assertIn("ROSEnv", text)

    def test_consumer_colcon_example_maps_to_core(self):
        example = ROOT / "examples" / "consumer_colcon"
        catalog_path = ROOT / "extensions" / "commands" / "ros" / "data" / "kilted_variants.json"
        if not catalog_path.is_file():
            self.skipTest("kilted_variants.json not generated yet")
        mapping = ros_pkgxml.map_workspace(example)
        self.assertEqual(mapping.variant, "core")
        self.assertIn("dummy_lib", mapping.local_packages)
        self.assertIn("rclcpp", mapping.covered)

    def test_compose_ros_profiles_defaults_then_overlay(self):
        overlay = ros_pkgxml.ros_profile_overlay_path()
        host, build = ros_pkgxml.compose_ros_profiles(None, None, default_host="default", default_build="default")
        self.assertEqual(host, ["default", str(overlay)])
        self.assertEqual(build, ["default", str(overlay)])

    def test_compose_ros_profiles_appends_overlay_to_user_profile(self):
        overlay = ros_pkgxml.ros_profile_overlay_path()
        host, build = ros_pkgxml.compose_ros_profiles(
            ["myprofile"],
            ["mybuild"],
            default_host="default",
            default_build="default",
        )
        self.assertEqual(host, ["myprofile", str(overlay)])
        self.assertEqual(build, ["mybuild", str(overlay)])

    def test_compose_ros_profiles_does_not_duplicate_overlay(self):
        overlay = str(ros_pkgxml.ros_profile_overlay_path())
        host, build = ros_pkgxml.compose_ros_profiles([overlay], [overlay])
        self.assertEqual(host, [overlay])
        self.assertEqual(build, [overlay])


if __name__ == "__main__":
    unittest.main()
