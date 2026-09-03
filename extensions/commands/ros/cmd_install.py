import os
import sys
from pathlib import Path

_EXT = Path(__file__).resolve().parent
if str(_EXT) not in sys.path:
    sys.path.insert(0, str(_EXT))

from conan.api.output import ConanOutput
from conan.cli.args import add_common_install_arguments, add_lockfile_args, add_reference_args
from conan.cli.command import conan_command
from conan.cli.formatters.graph import format_graph_json
from conan.cli.printers import print_profiles
from conan.cli.printers.graph import print_graph_basic, print_graph_packages
from conan.errors import ConanException

import ros_pkgxml


@conan_command(group="ROS", formatters={"json": format_graph_json})
def install(conan_api, parser, *args):
    """
    Generate a conanfile.txt from package.xml and install its requirements.
    """
    ros_pkgxml.add_mapping_args(parser)
    add_common_install_arguments(parser)
    add_reference_args(parser)
    add_lockfile_args(parser)
    parser.add_argument("-g", "--generator", action="append", help="Generators to use")
    parser.add_argument(
        "-of",
        "--output-folder",
        help="The root output folder for generated and build files",
    )
    parser.add_argument(
        "-d",
        "--deployer",
        action="append",
        help="Deploy using the provided deployer to the output folder.",
    )
    parser.add_argument("--deployer-folder", help="Deployer output folder")
    parser.add_argument("--deployer-package", action="append", help="Deploy matching packages")
    parser.add_argument(
        "--envs-generation",
        default=None,
        choices=["false"],
        help="Generation strategy for virtual environment files for the root",
    )
    args = parser.parse_args(*args)

    try:
        mapping = ros_pkgxml.mapping_from_args(args)
    except ros_pkgxml.RosConsumerError as exc:
        raise ConanException(str(exc)) from exc

    out = ConanOutput()
    out.info(mapping.format_report())

    if args.dry_run:
        out.info("dry-run: skipping conanfile.txt and install")
        out.info(ros_pkgxml.render_conanfile_txt(mapping))
        return {"graph": None, "conan_api": conan_api}

    conanfile_path = ros_pkgxml.write_conanfile_txt(mapping)
    out.success(f"Wrote {conanfile_path}")

    cwd = os.getcwd()
    path = str(conanfile_path)
    source_folder = str(conanfile_path.parent)
    output_folder = os.path.abspath(args.output_folder) if args.output_folder else None

    remotes = conan_api.remotes.list(args.remote) if not args.no_remote else []
    overrides = eval(args.lockfile_overrides) if args.lockfile_overrides else None
    lockfile = conan_api.lockfile.get_lockfile(
        lockfile=args.lockfile,
        conanfile_path=path,
        cwd=cwd,
        partial=args.lockfile_partial,
        overrides=overrides,
    )
    conan_api.lockfile.check_lockfile_config(lockfile)
    args.profile_host, args.profile_build = ros_pkgxml.compose_ros_profiles(
        args.profile_host,
        args.profile_build,
        default_host=conan_api.profiles.get_default_host(),
        default_build=conan_api.profiles.get_default_build(),
    )
    out.info(
        "Composing Conan profiles with the implicit ROS overlay "
        f"({ros_pkgxml.ros_profile_overlay_path()}). "
        "Pass -pr/--profile to choose the base; ROS settings are added on top."
    )
    profile_host, profile_build = conan_api.profiles.get_profiles_from_args(args)
    print_profiles(profile_host, profile_build)

    gapi = conan_api.graph
    deps_graph = gapi.load_graph_consumer(
        path,
        args.name,
        args.version,
        args.user,
        args.channel,
        profile_host,
        profile_build,
        lockfile,
        remotes,
        args.update,
    )
    print_graph_basic(deps_graph)
    deps_graph.report_graph_error()
    gapi.analyze_binaries(deps_graph, args.build, remotes, update=args.update, lockfile=lockfile)
    print_graph_packages(deps_graph)

    conan_api.install.install_binaries(deps_graph=deps_graph, remotes=remotes)
    ConanOutput().title("Finalizing install (deploy, generators)")
    conan_api.install.install_consumer(
        deps_graph,
        args.generator,
        source_folder,
        output_folder,
        deploy=args.deployer,
        deploy_package=args.deployer_package,
        deploy_folder=args.deployer_folder,
        envs_generation=args.envs_generation,
    )
    ConanOutput().success("Install finished successfully")

    lockfile = conan_api.lockfile.update_lockfile(
        lockfile, deps_graph, args.lockfile_packages, clean=args.lockfile_clean
    )
    conan_api.lockfile.save_lockfile(lockfile, args.lockfile_out, cwd)
    return {"graph": deps_graph, "conan_api": conan_api}
