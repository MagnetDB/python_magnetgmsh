"""Console script for python_magnetgeo."""
from typing import List, Optional

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

from .mesh.axi import get_allowed_algo, gmsh_msh


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
        choices=get_allowed_algo(),
        default="Delaunay",
    )
    parser.add_argument(
        "--scaling", help="scale to m (default unit is mm)", action="store_true"
    )
    parser.add_argument(
        "--lc", help="specify characteristic length", type=float, default=5
    )

    parser.add_argument("--show", help="display gmsh windows", action="store_true")
    parser.add_argument("--verbose", help="activate debug mode", action="store_true")
    parser.add_argument("--debug", help="activate debug mode", action="store_true")

    args = parser.parse_args()
    print(f"Arguments: {args}")

    cwd = os.getcwd()
    if args.wd:
        os.chdir(args.wd)

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
        gmsh.option.setNumber("General.Verbosity", 5)

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
    # print(f"ids[{Object.name}]: {ids}")
    bcs = MyObject.gmsh_bcs(Object, "", ids, args.debug)
    """
    for key in bcs:
        print(f"key={key}, bcs[{key}]={bcs[key]}")
    
    print("List VGroups")
    vGroups = gmsh.model.getPhysicalGroups(-1)
    for iGroup in vGroups:
        dimGroup = iGroup[0]  # 1D, 2D or 3D
        tagGroup = iGroup[1]
        nameGroup = gmsh.model.getPhysicalName(dimGroup, tagGroup)
        print(f"{nameGroup}: dim={dimGroup}, tag={tagGroup}")
        vEntities = gmsh.model.getEntitiesForPhysicalGroup(dimGroup, tagGroup)
        for tagEntity in vEntities:
            print(f"{nameGroup}: {tagEntity}")
    """

    # TODO set mesh characteristics here
    if args.mesh:
        boxes = []  # get bounding box per object
        air = False
        if AirData:
            air = True
        gmsh_msh(args.algo2d, args.lc, air, args.scaling)

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
    sys.exit(main())
