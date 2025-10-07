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

import os

import re
import argparse

import yaml

import gmsh


from .utils.files import load_Xao
from .mesh.groups import create_physicalbcs, create_physicalgroups
from .mesh.axi import get_allowed_algo as get_allowed_algo2D

from .mesh.m3d import get_allowed_algo as get_allowed_algo3D
from .utils.lists import flatten
from .cfg import loadcfg


def main():
    tags = {}

    parser = argparse.ArgumentParser()
    parser.add_argument("input_file")
    parser.add_argument("--debug", help="activate debug", action="store_true")
    parser.add_argument("--verbose", help="activate verbose", action="store_true")
    parser.add_argument("--env", help="load settings.env", action="store_true")
    parser.add_argument("--wd", help="set a working directory", type=str, default="")
    parser.add_argument(
        "--geo",
        help="specifiy geometry yaml file (use Auto to automatically retreive yaml filename fro xao, default is None)",
        type=str,
        default="None",
    )

    subparsers = parser.add_subparsers(
        title="commands", dest="command", help="sub-command help"
    )

    # parser_cfg = subparsers.add_parser('cfg', help='cfg help')
    parser_mesh = subparsers.add_parser("mesh", help="mesh help")
    parser_adapt = subparsers.add_parser("adapt", help="adapt help")

    parser_mesh.add_argument(
        "--algo2d",
        help="select an algorithm for 2d mesh",
        type=str,
        choices=get_allowed_algo2D(),
        default="Delaunay",
    )
    parser_mesh.add_argument(
        "--algo3d",
        help="select an algorithm for 3d mesh",
        type=str,
        choices=get_allowed_algo3D(),
        default="HXT",
    )
    parser_mesh.add_argument(
        "--lc", help="load mesh size from file", action="store_true"
    )
    parser_mesh.add_argument(
        "--scaling", help="scale to m (default unit is mm)", action="store_true"
    )
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

    parser_adapt.add_argument(
        "--bgm", help="specify a background mesh", type=str, default=None
    )
    parser_adapt.add_argument(
        "--estimator", help="specify an estimator (pos file)", type=str, default=None
    )

    args = parser.parse_args()
    if args.debug:
        print(args)

    cwd = os.getcwd()
    if args.wd:
        os.chdir(args.wd)

    hideIsolant = False
    groupIsolant = False
    groupLeads = False
    groupCoolingChannels = False

    is2D = False
    GeomParams = {"Solid": (3, "solids"), "Face": (2, "face")}

    # check if Axi is in input_file to see wether we are working with a 2D or 3D geometry
    if "Axi" in args.input_file:
        print("2D geometry detected")
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

    print("hideIsolant:", hideIsolant)
    print("groupIsolant:", groupIsolant)
    print("groupLeads:", groupLeads)
    print("groupCoolingChannels:", groupCoolingChannels)

    # init gmsh
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 1)

    # gmsh verbosity:
    # 0: silent except for fatal errors,
    # 1: +errors,
    # 2: +warnings,
    # 3: +direct,
    # 4: +information,
    # 5: +status,
    # 99: +debug
    gmsh.option.setNumber("General.Verbosity", 0)
    if args.debug or args.verbose:
        gmsh.option.setNumber("General.Verbosity", 2)

    # inspect Xao
    file = args.input_file  # r"HL-31_H1.xao"
    (gname, tags) = load_Xao(file, GeomParams, args.debug)
    (vtags, stags, ltags) = tags
    print(f"stags={stags.keys()}")
    print(f"vtags={vtags.keys()}")

    # Loading yaml file to get infos on volumes
    cfgfile = ""

    if args.geo != "None":
        cfgfile = args.geo
    if args.geo == "Auto":
        cfgfile = gname + ".yaml"
    print("cfgfile:", cfgfile)

    (solid_names, Channels) = loadcfg(cfgfile, gname, is2D, args.verbose)
    print(f"input_file: {args.input_file}")
    print(f"solid_names: {solid_names}")
    print(f"Channels: {Channels}")
    mdict = {}
    for name in solid_names:
        mdict[name] = ""

    excluded_tags = []
    if is2D:
        excluded_tags = [
            name for name in stags if not name in mdict and not name == "Air"
        ]
    print(f"excluded_tags: {excluded_tags}")
    # remove exclude_tags from stags

    if "Air" in args.input_file:
        solid_names.append("Air")
        if hideIsolant:
            raise Exception(
                "--hide Isolants cannot be used since cad contains Air region"
            )

    nsolids = len(gmsh.model.getEntities(GeomParams["Solid"][0]))
    assert (
        len(solid_names) == nsolids
    ), f"Wrong number of solids: in yaml {len(solid_names)} in gmsh {nsolids}"

    print(f"hideIsolant={hideIsolant}, groupIsolant={groupIsolant}, is2D={is2D}")
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

    print(f"Channels = {Channels}")
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
        refinedboxes = []

        air = False
        AirData = ()
        if "Air" in args.input_file:
            air = True

        from python_magnetgeo.utils import getObject
        Object = getObject(cfgfile)
        print(f"Object={Object}, type={type(Object)}")

        if is2D:
            from .MeshAxiData import MeshAxiData
            from .mesh.axi import gmsh_msh

            if air:
                from .Air import gmsh_boundingbox

                box = gmsh_boundingbox("Air")
                AirData = (box[1], box[4], box[3], 10)

            meshAxiData = MeshAxiData(cfgfile.replace(".yaml", ""), args.algo2d)
            if args.lc:
                meshAxiData.load(air)
            else:
                meshAxiData.default("", Object, AirData)
                meshAxiData.dump(air)

            cracks = {}
            gmsh_msh(args.algo2d, meshAxiData, refinedboxes, air, args.scaling)
        else:
            from .MeshData import MeshData
            from .mesh.m3d import gmsh_msh

            meshData = MeshData(cfgfile.replace(".yaml", ""), args.algo2d, args.algo3d)
            if args.lc:
                meshData.load(air)
            else:
                meshData.default("", Object, AirData)
                meshData.dump(air)

            gmsh_msh(args.algo3d, meshData, refinedboxes, air, args.scaling)
            print("xao2msh: gmsh_msh for 3D not implemented")

        meshname = file.replace(".xao", ".msh")
        print(f"Save mesh {meshname} to {os.getcwd()}")
        gmsh.write(f"{meshname}")

    if args.command == "adapt":
        print("adapt mesh not implemented yet")
    gmsh.finalize()
    return 0


if __name__ == "__main__":
    main()
