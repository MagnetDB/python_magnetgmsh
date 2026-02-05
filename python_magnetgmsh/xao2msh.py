"""
XAO to Gmsh Mesh Converter.

This module converts Salome XAO (eXtended Application Object) format files
to Gmsh mesh format. XAO files contain CAD geometry and groups exported from
Salome Platform, which is widely used for complex geometry modeling in
scientific computing.

The converter:
    - Loads CAD geometry from XAO file
    - Imports physical groups (volumes, surfaces, curves)
    - Applies mesh generation using Gmsh algorithms
    - Preserves group names and hierarchy from Salome
    - Optionally filters groups (e.g., cooling channels only)

Typical Usage:
    # Convert XAO to mesh with physical groups
    python -m python_magnetgmsh.xao2msh test-Axi.xao --geo test.yaml \\
        --wd /data mesh --group CoolingChannels
    
    # Multiple processing
    python -m python_magnetgmsh.xao2msh M9_HLtest-Axi.xao \\
        --geo M9_HLtest.yaml mesh --group CoolingChannels
    
    # As installed command
    python_xao2gmsh test.xao --geo config.yaml mesh

Workflow:
    1. XAO file created in Salome with geometry and groups
    2. Export from Salome to XAO format
    3. Use this tool to generate Gmsh mesh
    4. Mesh file (.msh) ready for FEM solvers (FeelPP, etc.)

XAO Format:
    XAO (eXtended Application Object) is an XML-based format developed by
    EDF for CAD data exchange. It contains:
        - Geometric shapes (BREP format)
        - Physical groups (volumes, faces, edges, vertices)
        - Assembly structure and metadata
    
    See: https://docs.salome-platform.org/

Command-Line Interface:
    Subcommands:
        mesh: Generate mesh from XAO geometry
        adapt: Adapt existing mesh (TODO)
    
    Arguments:
        input_file: XAO file path
        --geo: YAML geometry configuration (for metadata)
        --wd: Working directory
        --group: Filter specific physical group
        --algo2d/--algo3d: Meshing algorithms
        --show: Display Gmsh GUI

Dependencies:
    - gmsh >= 4.13.1: Mesh generation and XAO import
    - python_magnetgeo >= 1.0.0: Geometry metadata
    - xmltodict: XAO file parsing
    - pyyaml >= 6.0: Configuration parsing

Limitations:
    - XAO must contain valid BREP geometry
    - Physical groups must be properly defined in Salome
    - Mesh quality depends on geometry complexity
    - Large assemblies may require significant memory

See Also:
    - Salome Platform: https://www.salome-platform.org/
    - python_magnetgmsh.cli: Direct
"""

import argparse
import logging
import os

import gmsh

from .argparse_utils import add_common_args, add_wd_arg
from .cfg import loadcfg
from .logging_config import setup_logging
from .mesh.axi import get_allowed_algo as get_allowed_algo2D
from .mesh.groups import create_physicalbcs, create_physicalgroups
from .mesh.m3d import get_allowed_algo as get_allowed_algo3D
from .utils.files import load_Xao

logger = logging.getLogger(__name__)


def main():
    tags = {}

    parser = argparse.ArgumentParser()
    parser.add_argument("input_file")
    add_common_args(parser)
    parser.add_argument("--env", help="load settings.env", action="store_true")
    add_wd_arg(parser)
    parser.add_argument(
        "--geo",
        help="specifiy geometry yaml file (use Auto to automatically retreive yaml filename fro xao, default is None)",
        type=str,
        default="None",
    )

    subparsers = parser.add_subparsers(title="commands", dest="command", help="sub-command help")

    # parser_cfg = subparsers.add_parser('cfg', help='cfg help')
    parser_mesh = subparsers.add_parser("mesh", help="mesh help")
    parser_adapt = subparsers.add_parser("adapt", help="adapt help")

    # Import after creating parser to avoid circular imports
    from .argparse_utils import add_algo2d_arg, add_algo3d_arg, add_scaling_arg, add_lc_arg, add_show_arg
    
    add_algo2d_arg(parser_mesh, get_allowed_algo2D())
    add_algo3d_arg(parser_mesh, get_allowed_algo3D())
    add_lc_arg(parser_mesh)
    add_scaling_arg(parser_mesh)
    add_show_arg(parser_mesh)
    parser_mesh.add_argument(
        "--dry-run",
        help="mimic mesh operation without actually meshing",
        action="store_true",
    )

    # TODO add similar option to salome HIFIMAGNET plugins
    parser_mesh.add_argument(
        "--group",
        help="group selected items in mesh generation (Eg Isolants, Leads, CoolingChannels)",
        nargs="+",
        metavar="BC",
        type=str,
    )
    parser_mesh.add_argument(
        "--hide",
        help="hide selected items in mesh generation (eg Isolants)",
        nargs="+",
        metavar="Domain",
        type=str,
    )

    parser_adapt.add_argument("--bgm", help="specify a background mesh", type=str, default=None)
    parser_adapt.add_argument(
        "--estimator", help="specify an estimator (pos file)", type=str, default=None
    )

    args = parser.parse_args()

    # Setup logging based on command-line arguments
    setup_logging(
        verbose=args.verbose,
        debug=args.debug,
        log_file=args.log,  # Only log to file if explicitly specified
    )

    logger.debug(f"Command-line arguments: {args}")

    cwd = os.getcwd()
    if args.wd:
        logger.info(f"Working directory: {args.wd}")
        os.chdir(args.wd)

    hideIsolant = False
    groupIsolant = False
    groupLeads = False
    groupCoolingChannels = False

    is2D = False
    GeomParams = {"Solid": (3, "solids"), "Face": (2, "face")}

    # check if Axi is in input_file to see wether we are working with a 2D or 3D geometry
    if "Axi" in args.input_file:
        logger.info("2D axisymmetric geometry detected")
        is2D = True
        GeomParams["Solid"] = (2, "faces")
        GeomParams["Face"] = (1, "edge")

    if args.command == "mesh":
        if args.hide:
            hideIsolant = "Isolants" in args.hide
        if args.group:
            groupIsolant = "Isolants" in args.group
            groupLeads = "Leads" in args.group
            groupCoolingChannels = "CoolingChannels" in args.group

    logger.debug(f"hideIsolant: {hideIsolant}")
    logger.debug(f"groupIsolant: {groupIsolant}")
    logger.debug(f"groupLeads: {groupLeads}")
    logger.debug(f"groupCoolingChannels: {groupCoolingChannels}")

    # init gmsh
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 1)

    # Coordinate Gmsh verbosity with our logging level
    if args.debug:
        gmsh.option.setNumber("General.Verbosity", 2)
        logger.debug("Gmsh verbosity: warnings (2)")
    elif args.verbose:
        gmsh.option.setNumber("General.Verbosity", 1)
        logger.debug("Gmsh verbosity: errors (1)")
    else:
        gmsh.option.setNumber("General.Verbosity", 0)
        logger.debug("Gmsh verbosity: silent (0)")

    # inspect Xao
    logger.info(f"Loading XAO file: {args.input_file}")
    file = args.input_file  # r"HL-31_H1.xao"
    (gname, tags) = load_Xao(file, GeomParams, args.debug)
    (vtags, stags, ltags) = tags
    logger.debug(f"Loaded {len(stags)} surface tags, {len(vtags)} volume tags")

    # Loading yaml file to get infos on volumes
    cfgfile = ""

    if args.geo != "None":
        cfgfile = args.geo
    if args.geo == "Auto":
        cfgfile = gname + ".yaml"
    logger.info(f"Loading geometry configuration: {cfgfile}")

    (solid_names, Channels) = loadcfg(cfgfile, gname, is2D, args.verbose)
    logger.debug(f"Loaded {len(solid_names)} solids")
    logger.debug(f"Channels: {Channels}")
    mdict = {}
    for name in solid_names:
        mdict[name] = ""

    excluded_tags = []
    if is2D:
        excluded_tags = [name for name in stags if name not in mdict and not name == "Air"]
    logger.debug(f"Excluded tags: {excluded_tags}")
    # remove exclude_tags from stags

    if "Air" in args.input_file:
        solid_names.append("Air")
        if hideIsolant:
            raise Exception("--hide Isolants cannot be used since cad contains Air region")

    nsolids = len(gmsh.model.getEntities(GeomParams["Solid"][0]))
    assert (
        len(solid_names) == nsolids
    ), f"Wrong number of solids: in yaml {len(solid_names)} in gmsh {nsolids}"

    logger.debug(
        f"Creating physical groups: hideIsolant={hideIsolant}, groupIsolant={groupIsolant}, is2D={is2D}"
    )
    create_physicalgroups(
        vtags,
        stags,
        excluded_tags,
        GeomParams,
        hideIsolant,
        groupIsolant,
        is2D,
        args.debug,
    )

    logger.debug(
        f"Creating physical boundary conditions for {len(Channels) if Channels else 0} channels"
    )
    create_physicalbcs(
        ltags,
        GeomParams,
        groupCoolingChannels,
        Channels,
        hideIsolant,
        groupIsolant,
        args.debug,
    )

    if args.command == "mesh" and not args.dry_run:
        logger.info("Generating mesh...")
        refinedboxes = []

        air = False
        AirData = ()
        if "Air" in args.input_file:
            air = True
            logger.info("Air domain detected")

        from python_magnetgeo.utils import getObject

        Object = getObject(cfgfile)
        logger.debug(f"Loaded object: {Object.name}, type={type(Object).__name__}")

        if is2D:
            from .axi.MeshAxiData import createMeshAxiData
            from .mesh.axi import gmsh_msh as msh2D

            if air:
                from .axi.Air import gmsh_boundingbox

                box = gmsh_boundingbox("Air")
                AirData = (box[1], box[4], box[3], 10)

            yamlfile = cfgfile.replace(".yaml", "")
            if air:
                yamlfile += "_Air"
            yamlfile += "_gmshaxidata"
            meshAxiData = createMeshAxiData("", Object, AirData, yamlfile, args.algo2d)

            # cracks = {}
            msh2D(args.algo2d, meshAxiData, refinedboxes, air, args.scaling)
        else:
            from .m3d.MeshData import createMeshData
            from .mesh.m3d import gmsh_msh as msh3D

            yamlfile = cfgfile.replace(".yaml", "")
            if air:
                yamlfile += "_Air"
            yamlfile += "_gmshdata"
            meshData = createMeshData("", Object, yamlfile, AirData, args.algo2d, args.algo3d)

            msh3D(args.algo2d, args.algo3d, meshData, refinedboxes, air, args.scaling)
            logger.warning("3D meshing from XAO not fully implemented")

        meshname = file.replace(".xao", ".msh")
        gmsh.write(f"{meshname}")
        logger.info(f"Mesh saved: {meshname}")

    if args.command == "adapt":
        logger.warning("Mesh adaptation not implemented yet")
    
    # Display Gmsh GUI if requested (only for mesh command)
    if args.command == "mesh" and hasattr(args, 'show') and args.show:
        logger.info("Launching Gmsh GUI...")
        gmsh.fltk.run()
    
    gmsh.finalize()

    if args.wd:
        os.chdir(cwd)

    return 0


if __name__ == "__main__":
    main()
