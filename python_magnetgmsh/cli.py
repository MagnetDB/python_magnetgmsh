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
from python_magnetgeo import Screen
from python_magnetgeo import MSite

from .mesh.axi import get_allowed_algo, gmsh_msh, gmsh_cracks


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
    parser.add_argument("--lc", help="load mesh size from file", action="store_true")

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
        Screen.Screen: ".Screen",
        Supras.Supras: ".Supras",
        Bitters.Bitters: ".Bitters",
        MSite.MSite: ".MSite",
    }
    from importlib import import_module

    MyObject = import_module(import_dict[type(Object)], package="python_magnetgmsh")

    ids = MyObject.gmsh_ids(Object, AirData, args.debug)
    # print(f"ids[{Object.name}]: {ids}")
    prefix = ""
    bcs = MyObject.gmsh_bcs(Object, prefix, ids, args.debug)

    # TODO set mesh characteristics here
    if args.mesh:
        air = False
        if AirData:
            air = True
            # lcs["Air"] = 30

        from .MeshAxiData import MeshAxiData

        AirDAta = ()
        if air:
            from .Air import gmsh_air

            (r0_air, z0_air, dr_air, dz_air) = gmsh_air(Object, AirData)
            AirData = (z0_air, z0_air + dz_air, r0_air + dr_air, 10)

        meshAxiData = MeshAxiData(args.filename.replace(".yaml", ""), args.algo2d)
        if args.lc:
            meshAxiData.load(air)
        else:
            meshAxiData.default(prefix, Object, AirData)
            meshAxiData.dump(air)

        gmsh_msh(args.algo2d, meshAxiData, air, args.scaling)
        gmsh_cracks(args.debug)

        gmsh.option.setNumber("Mesh.SaveAll", 1)
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
