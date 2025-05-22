import gmsh
import sys
from math import pi, cos, sin

# script showing how the coordinates of the nodes of a mesh can be transformed,
# here by setting all the z coordinates to 0; this is less general, but much
# simpler, than the approach followed in `flatten.py'

if len(sys.argv) < 2:
    print("Usage: " + sys.argv[0] + " file.msh")
    exit(0)

import argparse
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_meshfile")
    parser.add_argument("--wd", help="set a working directory", type=str, default="")
    parser.add_argument("--rotate", help="rotation angle vs Ox (deg)", default="10", type=float)
    parser.add_argument("--show", help="display mesh (requires X11)", action="store_true")

    args = parser.parse_args()
    if args.debug:
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
    gmsh.write(f'{basename}-rotate-{arg.rotate:f.1}deg.msh')

    gmsh.finalize()
    return 0


if __name__ == "__main__":
    main()
