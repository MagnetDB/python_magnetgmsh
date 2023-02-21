"""Console script for python_magnetgeo."""
from typing import List

import argparse
import sys
import os
import yaml

import gmsh
from python_magnetgeo import Helix
from python_magnetgeo import Insert
from python_magnetgeo import Bitter
from python_magnetgeo import Bitters
from python_magnetgeo import Supra
from python_magnetgeo import Supras
from python_magnetgeo import MSite

MeshAlgo2D = {
    "MeshAdapt": 1,
    "Automatic": 2,
    "Initial": 3,
    "Delaunay": 5,
    "Frontal-Delaunay": 6,
    "BAMG": 7,
}


def gmsh_msh(
    algo: str, boxes: list, lcs: List[float], air: bool = False, scaling: bool = False
):
    """
    create msh

    TODO:
    - select algo
    - mesh characteristics
    - crack plugin for Bitter CoolingSlits
    """
    print("TODO: set characteristic lengths")

    Origin = gmsh.model.occ.addPoint(0, 0, 0, 0.1, 0)
    gmsh.model.occ.synchronize()

    # add Points
    EndPoints_tags = [0]

    # scaling
    unit = 1
    if scaling:
        unit = 0.001
        gmsh.option.setNumber("Geometry.OCCScaling", unit)

    # Assign a mesh size to all the points:
    lcar1 = 10 * unit
    gmsh.model.mesh.setSize(gmsh.model.getEntities(0), lcar1)

    if not lcs:
        print("Mesh Length Characteristics:")
        for box in boxes:
            for item in box:
                # print(f'{item}: box[item]={box[item]}')
                cadtype, (r, z) = box[item]
                r1 = float(r[1])
                r0 = float(r[0])
                lcs.append((r1 - r0) / 30.0)  # r,z are in mm in yaml files
                print(f"\t{item}: {lcs[-1]}")
        if air:
            lcs.append(lcs[-1] * 20)
            print(f"Air: {lcs[-1]}")
    else:
        # print(f'Boxes: {Boxes}')
        nboxes = len(boxes)
        if air:
            assert (
                nboxes == len(lcs) - 1
            ), f"Wrong number of mesh length size: {len(boxes)} magnets whereas lcs contains {len(lcs)-1} mesh size"
        else:
            assert nboxes == len(
                lcs
            ), f"Wrong number of mesh length size: {len(boxes)} magnets whereas lcs contains {len(lcs)} mesh size"

    # Get points from Physical volumes
    # from volume name use correct lc characteristic
    z_eps = 1.0e-6
    for i, box in enumerate(boxes):
        for key in box:
            mtype = box[key][0]
            # print(f'box[{i}]={key} mtype={mtype} lc={lcs[i]} boundingBox={box[key][1]}')
            (r, z) = box[key][1]

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

    gmsh.option.setNumber("Mesh.Algorithm", MeshAlgo2D[algo])
    gmsh.model.mesh.generate(2)
    pass


def main():
    """Console script for python_magnetgeo."""
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "filename", help="name of the model to be loaded (yaml file)", type=str
    )
    parser.add_argument("--wd", help="set a working directory", type=str, default="")
    parser.add_argument(
        "--air",
        help="activate air generation",
        nargs=2,
        type=float,
        metavar=("infty_Rratio", "infty_Zratio"),
    )
    parser.add_argument("--mesh", help="activate mesh", action="store_true")
    parser.add_argument(
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
    parser.add_argument(
        "--scaling", help="scale to m (default unit is mm)", action="store_true"
    )
    parser.add_argument(
        "--lc",
        help="specify characteristic lengths (Magnet1, Magnet2, ..., Air (aka default))",
        type=float,
        nargs="+",
        metavar="LC",
    )

    parser.add_argument("--show", help="display gmsh windows", action="store_true")
    parser.add_argument("--verbose", help="activate debug mode", action="store_true")
    parser.add_argument("--debug", help="activate debug mode", action="store_true")

    args = parser.parse_args()

    print(f"Arguments: {args}")

    cwd = os.getcwd()
    if args.wd:
        os.chdir(args.wd)

    print(args.filename)

    AirData = ()
    if args.air:
        infty_Rratio = args.air[0]  # 1.5
        if infty_Rratio < 1:
            raise RuntimeError(f"Infty_Rratio={infty_Rratio} should be greater than 1")
        infty_Zratio = args.air[1]  # 2.
        if infty_Zratio < 1:
            raise RuntimeError(f"Infty_Zratio={infty_Zratio} should be greater than 1")
        AirData = (infty_Rratio, infty_Zratio)

    with open(args.filename, "r") as f:
        Object = yaml.load(f, Loader=yaml.FullLoader)
        print(f"Object={Object}, type={type(Object)}")

    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 1)
    gmsh.option.setNumber("General.Verbosity", 0)
    if args.debug or args.verbose:
        gmsh.option.setNumber("General.Verbosity", 2)

    gmsh.model.add(args.filename)
    gmsh.logger.start()

    import_dict = {
        Helix.Helix: ".Helix",
        Insert.Insert: ".Insert",
        Bitter.Bitter: ".Bitter",
        Supra.Supra: ".Supra",
        Supras.Supras: ".Supras",
        Bitters.Bitters: ".Bitters",
        MSite.MSite: ".MSite",
    }
    from importlib import import_module

    MyObject = import_module(import_dict[type(Object)], package="python_magnetgmsh")

    ids = MyObject.gmsh_ids(Object, AirData, args.debug)
    print(f"ids[{Object.name}]: {ids}")
    bcs = MyObject.gmsh_bcs(Object, "", ids, args.debug)

    # TODO set mesh characteristics here
    if args.mesh:
        print("msh:", type(args.mesh))
        boxes = []  # get bounding box per object
        air = False
        if AirData:
            air = True
        gmsh_msh(args.algo2d, boxes, args.lc, air, args.scaling)

        gmsh.model.mesh.generate(2)
        meshfilename = args.filename.replace(".yaml", "-Axi")
        if air:
            meshfilename += "_withAir"
        gmsh.write(meshfilename + ".msh")

    log = gmsh.logger.get()
    print("Logger has recorded " + str(len(log)) + " lines")
    gmsh.logger.stop()
    # Launch the GUI to see the results:
    if args.show:
        gmsh.fltk.run()
    gmsh.finalize()

    if args.wd:
        os.chdir(cwd)

    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
