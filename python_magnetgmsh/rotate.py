import gmsh
import os
from math import pi, cos, sin

# see `flatten.py' gmsh example


import argparse
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_meshfile")
    parser.add_argument("--wd", help="set a working directory", type=str, default="")
    parser.add_argument("--rotate", help="rotation angle vs Ox (deg)", default="10", type=float)
    parser.add_argument("--show", help="display mesh (requires X11)", action="store_true")

    args = parser.parse_args()
    print(args)

    cwd = os.getcwd()
    if args.wd:
        os.chdir(args.wd)

    basename = args.input_meshfile.split('.msh')[0]
    
    gmsh.initialize()
    gmsh.open(args.input_meshfile)

    gmsh.model.mesh.affineTransform([1, 0,                         0,                        0,
                                     0, cos(pi/180.*args.rotate), -sin(pi/180.*args.rotate), 0,
                                     0, sin(pi/180.*args.rotate),  cos(pi/180.*args.rotate), 0])

    if args.show:
        gmsh.fltk.run()
    gmsh.write(f'{basename}-rotate-{args.rotate:.1f}deg.msh')

    gmsh.finalize()
    return 0


if __name__ == "__main__":
    main()
