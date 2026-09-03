import sys
from pathlib import Path

_EXT = Path(__file__).resolve().parent
if str(_EXT) not in sys.path:
    sys.path.insert(0, str(_EXT))

from conan.api.output import ConanOutput
from conan.cli.command import conan_command
from conan.errors import ConanException

import ros_pkgxml


@conan_command(group="ROS")
def init(conan_api, parser, *args):
    """
    Generate a conanfile.txt from ROS package.xml files in a workspace.
    """
    ros_pkgxml.add_mapping_args(parser)
    args = parser.parse_args(*args)
    try:
        mapping = ros_pkgxml.mapping_from_args(args)
    except ros_pkgxml.RosConsumerError as exc:
        raise ConanException(str(exc)) from exc

    out = ConanOutput()
    out.info(mapping.format_report())
    if args.dry_run:
        out.info("dry-run: conanfile.txt not written")
        out.info(ros_pkgxml.render_conanfile_txt(mapping))
        return mapping.format_report()

    path = ros_pkgxml.write_conanfile_txt(mapping)
    out.success(f"Wrote {path}")
    return mapping.format_report()
