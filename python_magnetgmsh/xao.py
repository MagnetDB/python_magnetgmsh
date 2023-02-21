"""
Retreive Physical Group from xao
Mesh using gmsh

TODO:
test with an xao file with embedded cad data (use stringio to cad)
retreive volume names from yaml file
link with MeshData
remove unneeded class like NumModel, freesteam, pint and SimMaterial

see gmsh/api/python examples for that
ex also in https://www.pygimli.org/_examples_auto/1_meshing/plot_cad_tutorial.html
"""
from typing import Type

import os

import re
import argparse

import yaml

import gmsh

from python_magnetgeo.Helix import Helix
from python_magnetgeo.Insert import Insert
from python_magnetgeo.Bitter import Bitter
from python_magnetgeo.Supra import Supra
from python_magnetgeo.Bitters import Bitters
from python_magnetgeo.Supras import Supras
from python_magnetgeo.MSite import MSite

from .utils import load_Xao
from .volumes import create_physicalgroups, create_bcs


def Supra_Gmsh(mname: str, cad: Supra, gname: str, is2D: bool, verbose: bool = False):
    """ Load Supra cad """
    print(f"Supra_Gmsh: mname={mname}, cad={cad.name}, gname={gname}")
    return cad.get_names(mname, is2D, verbose)


def Bitter_Gmsh(mname: str, cad: Bitter, gname: str, is2D: bool, verbose: bool = False):
    """ Load Bitter cad """
    print(f"Bitter_Gmsh: cad={cad.name}, gname={gname}")
    return cad.get_names(mname, is2D, verbose)


def Helix_Gmsh(mname: str, cad: Helix, gname: str, is2D: bool, verbose: bool = False):
    """ Load Helix cad """
    print(f"Helix_Gmsh: mname={mname}, cad={cad.name}, gname={gname}")
    return cad.get_names(mname, is2D, verbose)


def Bitters_Gmsh(
    mname: str, cad: Bitters, gname: str, is2D: bool, verbose: bool = False
):
    """ Load Bitters """
    print(f"Bitters_Gmsh: mname={mname}, gname={gname}")
    solid_names = []
    for magnet in cad.magnets:
        pcad = None
        with open(magnet + ".yaml", "r") as f:
            pcad = yaml.load(f, Loader=yaml.FullLoader)

        solid_names += Bitter_Gmsh(mname, pcad, gname, is2D, verbose)
    return solid_names


def Supras_Gmsh(mname: str, cad: Supras, gname: str, is2D: bool, verbose: bool = False):
    """ Load Supras """
    print(f"Supras_Gmsh: mname={mname}, gname={gname}")
    solid_names = []
    for magnet in cad.magnets:
        pcad = None
        with open(magnet + ".yaml", "r") as f:
            pcad = yaml.load(f, Loader=yaml.FullLoader)

        solid_names += Supra_Gmsh(mname, pcad, gname, is2D, verbose)
    return solid_names


def Insert_Gmsh(mname: str, cad: Insert, gname: str, is2D: bool, verbose: bool = False):
    """ Load Insert """
    print(f"Insert_Gmsh: mname={mname}, cad={cad.name}, gname={gname}")
    solid_names = cad.get_names(mname, is2D, verbose)
    NHelices = cad.get_nhelices()
    return (solid_names, NHelices)


def Magnet_Gmsh(mname: str, cad, gname: str, is2D: bool, verbose: bool = False):
    """ Load Magnet cad """
    print(f"Magnet_Gmsh: mname={mname}, cad={cad}, gname={gname}")
    solid_names = []
    NHelices = []
    Boxes = {}

    cfgfile = cad + ".yaml"
    with open(cfgfile, "r") as cfgdata:
        pcad = yaml.load(cfgdata, Loader=yaml.FullLoader)
        pname = pcad.name

    # print('pcad: {pcad} type={type(pcad)}')
    if isinstance(pcad, Bitter):
        solid_names += Bitter_Gmsh(mname, pcad, pname, is2D, verbose)
        NHelices.append(0)
        Boxes[pname] = ("Bitter", pcad.boundingBox())
        # TODO prepend name with part name
    elif isinstance(pcad, Supra):
        solid_names += Supra_Gmsh(mname, pcad, pname, is2D, verbose)
        NHelices.append(0)
        Boxes[pname] = ("Supra", pcad.boundingBox())
        # TODO prepend name with part name
    elif isinstance(pcad, Insert):
        # keep pname
        # print(f'Insert: {pname}')
        (_names, _NHelices, _Boxes, _Channels) = Insert_Gmsh(
            mname, pcad, pname, is2D, verbose
        )
        solid_names += _names
        NHelices.append(_NHelices)
        prefix = pname
        if mname:
            prefix = f"{mname}"

        Boxes[pname] = ("Insert", pcad.boundingBox())
        # print(f'Boxes[{pname}]={Boxes[pname]}')
        # TODO prepend name with part name
    if verbose:
        print(f"Magnet_Gmsh: {cad} Done [solids {len(solid_names)}]")
        print(f"Magnet_Gmsh: Boxes={Boxes}")
    return (pname, solid_names, NHelices, Boxes)


def MSite_Gmsh(cad, gname, is2D, verbose):
    """
    Load MSite cad
    """

    print("MSite_Gmsh:", cad)
    print("MSite_Gmsh Channels:", cad.get_channels())

    compound = []
    solid_names = []
    NHelices = []
    Channels = cad.get_channels()
    Isolants = cad.get_isolants()
    Boxes = []

    def ddd(mname, cad_data, solid_names, NHelices):
        # print(f"ddd: mname={mname}, cad_data={cad_data}")
        (pname, _names, _NHelices, _Boxes) = Magnet_Gmsh(
            mname, cad_data, gname, is2D, verbose
        )
        compound.append(cad_data)
        solid_names += _names
        NHelices += _NHelices
        Boxes.append(_Boxes)
        if verbose:
            print(
                f"MSite_Gmsh: cad_data={cad_data}, pname={pname}, _names={len(solid_names)}, solids={len(solid_names)}"
            )

    if isinstance(cad.magnets, str):
        print(f"magnet={cad.magnets}, type={type(cad.magnets)}")
        ddd(cad.magnets, cad.magnets, solid_names, NHelices)
    elif isinstance(cad.magnets, dict):
        for key in cad.magnets:
            print(f"magnet={key}, dict")
            if isinstance(cad.magnets[key], str):
                ddd(key, cad.magnets[key], solid_names, NHelices)
            elif isinstance(cad.magnets[key], list):
                for mpart in cad.magnets[key]:
                    ddd(key, mpart, solid_names, NHelices)

    print(f"Channels: {Channels}")
    if verbose:
        print(f"MSite_Gmsh: {cad} Done [solids {len(solid_names)}]")
    return (compound, solid_names, NHelices, Channels, Isolants, Boxes)


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
        choices=[
            "MeshAdapt",
            "Automatic",
            "Initial",
            "Delaunay",
            "Frontal-Delaunay",
            "BAMG",
        ],
        default="Delaunay",
    )
    parser_mesh.add_argument(
        "--algo3d",
        help="select an algorithm for 3d mesh",
        type=str,
        choices=["Delaunay", "Initial", "Frontal", "MMG3D", "HXT", "None"],
        default="None",
    )
    parser_mesh.add_argument(
        "--lc",
        help="specify characteristic lengths (Magnet1, Magnet2, ..., Air (aka default))",
        type=float,
        nargs="+",
        metavar="LC",
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

    MeshAlgo2D = {
        "MeshAdapt": 1,
        "Automatic": 2,
        "Initial": 3,
        "Delaunay": 5,
        "Frontal-Delaunay": 6,
        "BAMG": 7,
    }

    MeshAlgo3D = {"Delaunay": 1, "Initial": 3, "Frontal": 4, "MMG3D": 7, "HXT": 10}

    # init gmsh
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 1)
    # (0: silent except for fatal errors, 1: +errors, 2: +warnings, 3: +direct, 4: +information, 5: +status, 99: +debug)
    gmsh.option.setNumber("General.Verbosity", 0)
    if args.debug or args.verbose:
        gmsh.option.setNumber("General.Verbosity", 2)

    file = args.input_file  # r"HL-31_H1.xao"
    (gname, tree) = load_Xao(file, GeomParams, args.debug)

    # Loading yaml file to get infos on volumes
    cfgfile = ""
    solid_names = []
    bc_names = []

    innerLead_exist = False
    outerLead_exist = False
    NHelices = 0
    Channels = None
    Boxes = []

    if args.geo != "None":
        cfgfile = args.geo
    if args.geo == "Auto":
        cfgfile = gname + ".yaml"
    print("cfgfile:", cfgfile)

    compound = []
    cad = None
    with open(cfgfile, "r") as cfgdata:
        cad = yaml.load(cfgdata, Loader=yaml.FullLoader)

        print(f"cfgfile: {cad}")
        # TODO get solid names (see Salome HiFiMagnet plugin)
        if isinstance(cad, MSite):
            if args.verbose:
                print("load cfg MSite")
            (compound, _names, NHelices, Channels, Isolants, _Boxes) = MSite_Gmsh(
                cad, gname, is2D, args.verbose
            )
            # print(f'_Boxes: {_Boxes}, {len(_Boxes)}')
            Boxes = _Boxes
            solid_names += _names
        elif isinstance(cad, Bitters):
            if args.verbose:
                print("load cfg Bitters")
            mname = ""
            solid_names += Bitters_Gmsh(mname, cad, gname, is2D, args.verbose)
            Boxes.append({cad.name: ("Bitters", cad.boundingBox())})
            _Channels = cad.get_channels(mname)
            if mname:
                Channels[mname] = _Channels
            else:
                Channels = _Channels

        elif isinstance(cad, Supras):
            if args.verbose:
                print("load cfg Supras")
            mname = ""
            solid_names += Supras_Gmsh(mname, cad, gname, is2D, args.verbose)
            Boxes.append({cad.name: ("Supras", cad.boundingBox())})
        elif isinstance(cad, Bitter):
            if args.verbose:
                print("load cfg Bitter")
            mname = ""
            solid_names += Bitter_Gmsh(mname, cad, gname, is2D, args.verbose)
            Boxes.append({cad.name: ("Bitter", cad.boundingBox())})
            _Channels = cad.get_channels(mname)
            if mname:
                Channels[mname] = _Channels
            else:
                Channels = _Channels
        elif isinstance(cad, Supra):
            if args.verbose:
                print("load cfg Supra")
            mname = ""
            solid_names += Supra_Gmsh(mname, cad, gname, is2D, args.verbose)
            Boxes.append({cad.name: ("Supra", cad.boundingBox())})
        elif isinstance(cad, Insert):
            if args.verbose:
                print("load cfg Insert")
            mname = ""
            (_names, NHelices) = Insert_Gmsh(mname, cad, gname, is2D, args.verbose)
            Boxes.append({cad.name: ("Insert", cad.boundingBox())})
            _Channels = cad.get_channels(mname)
            if mname:
                Channels[mname] = _Channels
            else:
                Channels = _Channels
            print(f"_Channels: {_Channels}")
            solid_names += _names
        elif isinstance(cad, Helix):
            if args.verbose:
                print("load cfg Helix")
            mname = ""
            solid_names += Helix_Gmsh(mname, cad, gname, is2D, args.verbose)
            Boxes.append({cad.name: ("Helix", cad.boundingBox())})
        else:
            raise Exception(f"unsupported type of cad {type(cad)}")

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

    print(f"compound = {compound}")
    print(f"NHelices = {NHelices}")
    print(f"Channels = {Channels}")
    print(f"Boxes = {Boxes}")

    # use yaml data to identify solids id...
    # Insert solids: H1_Cu, H1_Glue0, H1_Glue1, H2_Cu, ..., H14_Glue1, R1, R2, ..., R13, InnerLead, OuterLead, Air
    # HR: Cu, Kapton0, Kapton1, ... KaptonXX
    stags = create_physicalgroups(
        tree, solid_names, GeomParams, hideIsolant, groupIsolant, args.debug
    )

    # get groups
    bctags = create_bcs(
        tree,
        gname,
        GeomParams,
        NHelices,
        innerLead_exist,
        outerLead_exist,
        groupCoolingChannels,
        Channels,
        compound,
        hideIsolant,
        groupIsolant,
        args.debug,
    )

    # Generate the mesh and write the mesh file
    Origin = gmsh.model.occ.addPoint(0, 0, 0, 0.1, 0)
    gmsh.model.occ.synchronize()

    # TODO write a template geo gmsh file for later use(gname + ".geo")

    # TODO: get solid id for glue
    # Get Helical cuts EndPoints
    EndPoints_tags = [0]
    VPoints_tags = []

    if isinstance(cad, Insert) or isinstance(cad, Helix):
        # TODO: loop over tag from Glue or Kaptons (here [2, 3])
        glue_tags = [
            i + 1
            for i, name in enumerate(solid_names)
            if ("Isolant" in name or ("Glue" in name or "Kapton" in name))
        ]
        if args.verbose:
            print("glue_tags: ", glue_tags)
        for tag in glue_tags:
            if args.verbose:
                print(
                    f"BC glue[{tag}:",
                    gmsh.model.getBoundary([(GeomParams["Solid"][0], tag)]),
                )
            for (dim, tag) in gmsh.model.getBoundary([(GeomParams["Solid"][0], tag)]):
                gtype = gmsh.model.getType(dim, tag)
                if gtype == "Plane":
                    Points = gmsh.model.getBoundary(
                        [(GeomParams["Face"][0], tag)], recursive=True
                    )
                    for p in Points:
                        EndPoints_tags.append(p[1])
            print("EndPoints:", EndPoints_tags)

        """
        # TODO: get solid id for Helix (here [1])
        cu_tags = [i  for i,name in enumerate(solid_names) if name.startswith('H') and "Cu" in name]
        # TODO: for shape force also the mesh to be finer near shapes
        # How to properly detect shapes in brep ???
        # Get V0/V1 EndPoints
        # Eventually add point from V probes see: https://www.pygimli.org/_examples_auto/1_meshing/plot_cad_tutorial.html
        for (dim, tag) in gmsh.model.getBoundary([(3,1)]):
            type = gmsh.model.getType(dim, tag)
            if type == "Plane":
                Points = gmsh.model.getBoundary([(2, tag)], recursive=True)
                    for p in Points:
                        if not p[1] in EndPoints_tags:
                            VPoints_tags.append(p[1])
        """
        print("VPoints:", VPoints_tags)

    if args.command == "mesh" and not args.dry_run:

        lcs = []
        if args.debug:
            print("args.lc={args.lc}")

        # if not mesh characteristic length is given
        if not args.lc is None:
            if not isinstance(args.lc, list):
                lcs.append(args.lc)
            else:
                lcs = args.lc

        unit = 1
        # load brep file into gmsh
        if args.scaling:
            unit = 0.001
            gmsh.option.setNumber("Geometry.OCCScaling", unit)

        if not lcs:
            print("Mesh Length Characteristics:")
            # print(f'Boxes: {Boxes}, type={type(Boxes)}')
            for box in Boxes:
                for item in box:
                    # print(f'{item}: box[item]={box[item]}')
                    cadtype, (r, z) = box[item]
                    r1 = float(r[1])
                    r0 = float(r[0])
                    lcs.append((r1 - r0) / 30.0)  # r,z are in mm in yaml files
                    print(f"\t{item}: {lcs[-1]}")
            if "Air" in args.input_file:
                lcs.append(lcs[-1] * 20)
                print(f"Air: {lcs[-1]}")
        else:
            # print(f'Boxes: {Boxes}')
            nboxes = len(Boxes)
            if "Air" in args.input_file:
                assert (
                    nboxes == len(lcs) - 1
                ), f"Wrong number of mesh length size: {len(Boxes)} magnets whereas lcs contains {len(lcs)-1} mesh size"
            else:
                assert nboxes == len(
                    lcs
                ), f"Wrong number of mesh length size: {len(Boxes)} magnets whereas lcs contains {len(lcs)} mesh size"

        # load brep file into gmsh
        if args.scaling:
            unit = 0.001
            gmsh.option.setNumber("Geometry.OCCScaling", unit)

        # Assign a mesh size to all the points:
        lcar1 = lcs[-1]
        gmsh.model.mesh.setSize(gmsh.model.getEntities(0), lcar1)

        # Get points from Physical volumes
        # from volume name use correct lc characteristic
        z_eps = 1.0e-6
        for i, box in enumerate(Boxes):
            for key in box:
                mtype = box[key][0]
                # print(f'box[{i}]={key} mtype={mtype} lc={lcs[i]} boundingBox={box[key][1]}')
                (r, z) = box[key][1]
                if mtype == "Supra":
                    z[0] *= 1.1
                    z[1] *= 1.1

                ov = gmsh.model.getEntitiesInBoundingBox(
                    r[0], z[0], -z_eps, r[1], z[1], z_eps, 0
                )
                gmsh.model.mesh.setSize(ov, lcs[i])

        # LcMax -                         /------------------
        #                               /
        #                             /
        #                           /
        # LcMin -o----------------/
        #        |                |       |
        #      Point           DistMin DistMax
        # Field 1: Distance to electrodes

        if EndPoints_tags:
            gmsh.model.mesh.field.add("Distance", 1)
            gmsh.model.mesh.field.setNumbers(1, "NodesList", EndPoints_tags)

            # Field 2: Threshold that dictates the mesh size of the background field
            gmsh.model.mesh.field.add("Threshold", 2)
            gmsh.model.mesh.field.setNumber(2, "IField", 1)
            gmsh.model.mesh.field.setNumber(2, "LcMin", lcar1 / 20.0)
            gmsh.model.mesh.field.setNumber(2, "LcMax", lcar1)
            gmsh.model.mesh.field.setNumber(2, "DistMin", 5 * unit)
            gmsh.model.mesh.field.setNumber(2, "DistMax", 10 * unit)
            gmsh.model.mesh.field.setNumber(2, "StopAtDistMax", 15 * unit)
            gmsh.model.mesh.field.setAsBackgroundMesh(2)

            # gmsh.model.mesh.field.add("Distance", 3)
            # gmsh.model.mesh.field.setNumbers(3, "NodesList", VPoints_tags)

            # # Field 3: Threshold that dictates the mesh size of the background field
            # gmsh.model.mesh.field.add("Threshold", 4)
            # gmsh.model.mesh.field.setNumber(4, "IField", 3)
            # gmsh.model.mesh.field.setNumber(4, "LcMin", lcar1/3.)
            # gmsh.model.mesh.field.setNumber(4, "LcMax", lcar1)
            # gmsh.model.mesh.field.setNumber(4, "DistMin", 0.2)
            # gmsh.model.mesh.field.setNumber(4, "DistMax", 1.5)
            # gmsh.model.mesh.field.setNumber(4, "StopAtDistMax", 1)

            # # Let's use the minimum of all the fields as the background mesh field:
            # gmsh.model.mesh.field.add("Min", 5)
            # gmsh.model.mesh.field.setNumbers(5, "FieldsList", [2, 4])
            # gmsh.model.mesh.field.setAsBackgroundMesh(5)

        if args.algo2d != "BAMG":
            gmsh.option.setNumber("Mesh.Algorithm", MeshAlgo2D[args.algo2d])
        else:
            # # They can also be set for individual surfaces, e.g. for using `MeshAdapt' on
            gindex = len(stags) + len(bctags)
            for tag in range(len(stags), gindex):
                print(f"Apply BAMG on tag={tag}")
                gmsh.model.mesh.setAlgorithm(2, tag, MeshAlgo2D[args.algo2d])

        if args.algo3d != "None":
            gmsh.option.setNumber("Mesh.Algorithm3D", MeshAlgo3D[args.algo3d])
            gmsh.model.mesh.generate(3)
        else:
            gmsh.model.mesh.generate(2)

        meshname = gname
        if is2D:
            meshname += "-Axi"
        if "Air" in args.input_file:
            meshname += "_withAir"
        print(f"Save mesh {meshname}.msh to {os.getcwd()}")
        gmsh.write(f"{meshname}.msh")

    if args.command == "adapt":
        print("adapt mesh not implemented yet")
    gmsh.finalize()
    return 0


if __name__ == "__main__":
    main()
