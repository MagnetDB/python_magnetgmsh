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

import argparse
import logging
import os
from math import pi, cos, sin

import gmsh

from .argparse_utils import add_common_args, add_wd_arg, add_show_arg
from .logging_config import setup_logging

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_meshfile")
    add_wd_arg(parser)
    parser.add_argument("--rotate", help="rotation angle vs Ox (deg)", default="10", type=float)
    add_show_arg(parser)
    add_common_args(parser)

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

    basename = args.input_meshfile.split(".msh")[0]

    logger.info(f"Loading mesh: {args.input_meshfile}")
    gmsh.initialize()
    gmsh.open(args.input_meshfile)

    logger.info(f"Rotating mesh by {args.rotate}° around X-axis")
    gmsh.model.mesh.affineTransform(
        [
            1,
            0,
            0,
            0,
            0,
            cos(pi / 180.0 * args.rotate),
            -sin(pi / 180.0 * args.rotate),
            0,
            0,
            sin(pi / 180.0 * args.rotate),
            cos(pi / 180.0 * args.rotate),
            0,
        ]
    )

    output_file = f"{basename}-rotate-{args.rotate:.1f}deg.msh"

    if args.show:
        logger.info("Launching Gmsh GUI...")
        gmsh.fltk.run()

    gmsh.write(output_file)
    logger.info(f"Rotated mesh saved: {output_file}")

    gmsh.finalize()

    if args.wd:
        os.chdir(cwd)

    return 0


if __name__ == "__main__":
    main()
