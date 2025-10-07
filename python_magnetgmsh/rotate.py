"""
Mesh Rotation Utility for Gmsh Files.

This module provides functionality to rotate existing Gmsh mesh files around
the X-axis (Ox). Useful for creating rotated mesh configurations for
electromagnetic analysis, structural simulations, or assembly positioning.

The rotation uses affine transformations to rotate all nodes in the mesh
while preserving element connectivity and physical groups. The original
mesh file is not modified; output is saved to a new file.

Typical Usage:
    # Rotate mesh 45 degrees around X-axis
    python -m python_magnetgmsh.rotate mesh.msh --rotate 45 --show
    
    # With working directory
    python -m python_magnetgmsh.rotate HL-31_H1.msh --wd /data/meshes --rotate 90
    
    # Output: HL-31_H1-rotate-90.0deg.msh

Mathematical Details:
    Rotation around X-axis (Ox) by angle θ:
    ┌   ┐   ┌ 1    0       0    0 ┐ ┌ x ┐
    │ x'│   │ 0  cos(θ) -sin(θ) 0 │ │ y │
    │ y'│ = │ 0  sin(θ)  cos(θ) 0 │ │ z │
    │ z'│   │ 0    0       0    1 │ │ 1 │
    └   ┘   └                    ┘ └   ┘
    
    This preserves distances and angles, making it suitable for mesh reuse
    in different orientations.

Command-Line Arguments:
    input_meshfile: Gmsh mesh file to rotate (.msh format)
    --wd: Working directory for input/output
    --rotate: Rotation angle in degrees (default: 10°)
    --show: Display result in Gmsh GUI

Dependencies:
    - gmsh >= 4.13.1: Mesh processing and transformation
    - Python >= 3.9: Math functions (pi, cos, sin)

See Also:
    - gmsh.model.mesh.affineTransform: Underlying transformation function
    - Gmsh flatten.py example: Similar mesh transformation operations

Author: Christophe Trophime <christophe.trophime@lncmi.cnrs.fr>
"""

import gmsh
import os
from math import pi, cos, sin


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
