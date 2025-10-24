"""
Command-Line Interface for Gmsh Mesh Generation from Magnet Geometries.

This module provides the main command-line interface for python_magnetgmsh,
allowing users to generate CAD models and meshes from magnetgeo YAML
configuration files using the Gmsh API.

The CLI supports:
    - Loading geometry configurations from YAML files
    - Generating 2D axisymmetric or 3D CAD representations
    - Creating surrounding air domains for field calculations
    - Mesh generation with customizable algorithms
    - Thick cooling slit modeling for detailed thermal analysis
    - Unit scaling and mesh size control
    - Interactive visualization with Gmsh GUI

Typical Usage:
    # Generate mesh from YAML configuration
    python -m python_magnetgmsh.cli test.yaml --wd /data/geometries --mesh --show

    # With air domain and thick slits
    python -m python_magnetgmsh.cli M9_Bitters.yaml --thickslit --air 10 6 --mesh

    # As installed command
    python_magnetgmsh test.yaml --mesh --lc --verbose

Command-Line Arguments:
    filename: YAML geometry configuration file (required)
    --wd: Working directory for input/output files
    --air: Add surrounding air domain (ratios for R and Z)
    --thickslit: Model cooling slits with thickness (not just cuts)
    --mesh: Generate mesh after CAD creation
    --algo2d: 2D meshing algorithm (Delaunay, MeshAdapt, etc.)
    --scaling: Scale geometry to meters (default: millimeters)
    --lc: Load mesh size specifications from file
    --show: Display Gmsh GUI for interactive viewing
    --verbose: Enable detailed output
    --debug: Enable maximum verbosity for debugging

Dependencies:
    - gmsh >= 4.13.1: Mesh generation engine
    - python_magnetgeo >= 1.0.0: Geometry definitions
    - pyyaml >= 6.0: YAML configuration parsing

Exit Codes:
    0: Success
    1: Geometry loading error
    2: Mesh generation error

See Also:
    - python_magnetgmsh.cfg: Geometry loading functions
    - python_magnetgmsh.mesh.axi: Axisymmetric meshing utilities
    - python_magnetgeo: Geometry configuration format

Author: Christophe Trophime <christophe.trophime@lncmi.cnrs.fr>
"""

import argparse
import sys
import os

import gmsh

# Lazy loading import - automatically detects geometry type
from python_magnetgeo.utils import getObject
from python_magnetgeo.validation import ValidationError
from python_magnetgeo import (
    Insert,
    Helix,
    Bitter,
    Bitters,
    Supra,
    Supras,
    Screen,
    MSite,
)  # For type checking only

from .mesh.axi import get_allowed_algo, gmsh_msh, gmsh_cracks


def main():
    """
    Main entry point for python_magnetgmsh command-line interface.

    Parses command-line arguments, loads geometry configuration, generates
    CAD model in Gmsh, and optionally creates mesh. Provides comprehensive
    error handling and user feedback.

    The function performs the following steps:
        1. Parse command-line arguments
        2. Change to working directory if specified
        3. Load geometry from YAML configuration file
        4. Process air domain parameters if requested
        5. Generate CAD model using Gmsh API
        6. Optionally generate mesh with specified algorithm
        7. Save output files and display GUI if requested

    Returns:
        int: Exit code (0 for success, 1 for error)

    Raises:
        SystemExit: With exit code 1 on geometry loading or mesh generation errors

    Example Usage:
        >>> # As a module
        >>> import sys
        >>> sys.argv = ['cli.py', 'test.yaml', '--mesh', '--show']
        >>> from python_magnetgmsh.cli import main
        >>> main()
        0

        >>> # From command line
        >>> python -m python_magnetgmsh.cli test.yaml --wd /data --mesh

        >>> # As installed command
        >>> python_magnetgmsh M9_Bitters.yaml --thickslit --air 10 6 --mesh --verbose

    Command-Line Arguments:
        filename (str):
            Path to YAML geometry configuration file. Must be valid
            python_magnetgeo format with type annotation.

        --wd (str):
            Working directory for input/output files. If specified, changes
            to this directory before processing. Default: current directory.

        --air (float float):
            Generate surrounding air domain for field calculations. Takes two
            arguments: infty_Rratio and infty_Zratio.
            - infty_Rratio: Radial extent as ratio of geometry max radius
            - infty_Zratio: Axial extent as ratio of geometry height
            Example: --air 1.5 2.0 creates air domain 1.5× wider, 2× taller

        --thickslit:
            Model cooling slits with actual thickness rather than zero-width
            cuts. Provides more accurate thermal and flow simulations but
            increases mesh complexity.

        --mesh:
            Generate mesh after creating CAD model. Without this flag, only
            CAD geometry is created and saved.

        --algo2d (str):
            Select 2D meshing algorithm. Choices: Delaunay, MeshAdapt,
            Automatic, Initial2D, Packing, Frontal, DelQuad, PackParallelograms.
            Default: Delaunay. See gmsh documentation for algorithm details.

        --scaling:
            Scale geometry from millimeters to meters. Default unit is mm
            as used in magnet engineering. Use this flag for SI unit output.

        --lc:
            Load mesh size (characteristic length) from external file. File
            should contain mesh size specifications for different regions.
            If not set, default mesh sizes are used.

        --show:
            Display Gmsh GUI after processing. Requires X11/display server.
            Useful for interactive inspection and manual mesh refinement.

        --verbose:
            Enable detailed output showing geometry processing steps, mesh
            statistics, and timing information.

        --debug:
            Enable maximum Gmsh verbosity (level 5) for debugging. Shows
            all internal Gmsh operations, useful for troubleshooting errors.

    Output Files:
        - {filename}.geo_unrolled: Gmsh geometry script (if saved)
        - {filename}.msh: Gmsh mesh file (if --mesh specified)
        - Additional mesh statistics in console output

    Error Handling:
        - ValidationError: Caught and reported with file context
        - FileNotFoundError: Reported if YAML file not found
        - Gmsh errors: Logged via Gmsh logger, reported in console
        - Other exceptions: Caught, logged, and converted to exit code 1

    Notes:
        - Geometry type automatically detected from YAML
        - Supports all types in action_dict (Bitter, Supra, Insert, etc.)
        - Air domain generation modifies geometry in-place
        - Mesh quality depends on geometry complexity and algorithm choice
        - GUI requires graphical environment (use --no-show for batch processing)

    See Also:
        gmsh_msh: Main meshing function
        loadcfg: Geometry loading from YAML
        get_allowed_algo: Available meshing algorithms

    Version History:
        0.1.0: Added ValidationError handling, improved error messages
        0.0.x: Initial implementation with basic functionality
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("filename", help="name of the model to be loaded (yaml file)", type=str)
    parser.add_argument("--wd", help="set a working directory", type=str, default="")
    parser.add_argument(
        "--air",
        help="activate air generation",
        nargs=2,
        type=float,
        metavar=("infty_Rratio", "infty_Zratio"),
    )
    parser.add_argument("--thickslit", help="model thick cooling slits", action="store_true")
    parser.add_argument("--mesh", help="activate mesh", action="store_true")
    parser.add_argument(
        "--algo2d",
        help="select an algorithm for 2d mesh",
        type=str,
        choices=get_allowed_algo(),
        default="Delaunay",
    )
    parser.add_argument("--scaling", help="scale to m (default unit is mm)", action="store_true")
    parser.add_argument("--lc", help="load mesh size from file", action="store_true")

    parser.add_argument("--show", help="display gmsh windows", action="store_true")
    parser.add_argument("--verbose", help="activate debug mode", action="store_true")
    parser.add_argument("--debug", help="activate debug mode", action="store_true")

    args = parser.parse_args()
    print(f"Arguments: {args}, type={type(args)}")

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
    print(f"AirData={AirData}, args.air={args.air}")

    try:
        Object = getObject(args.filename)
    except ValidationError as e:
        # Handle validation errors from python_magnetgeo
        print(f"Validation error: {e}")

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

    # get BoudingBox for slit/channel
    boxes = []
    if args.thickslit:
        print("gmsh_box")
        boxes = MyObject.gmsh_box(Object, args.debug)

    # TODO: add args.thickness as optional param
    # or only for Bitter(s)
    ids = MyObject.gmsh_ids(Object, AirData, args.thickslit, args.debug)
    # print(f"ids[{Object.name}]: {ids}")

    prefix = ""
    bcs = MyObject.gmsh_bcs(Object, prefix, ids, args.thickslit, args.debug)

    # TODO set mesh characteristics here
    if args.mesh:
        air = False
        if AirData:
            air = True
            # lcs["Air"] = 30

        from .axi.MeshAxiData import createMeshAxiData

        if air:
            from .axi.Air import gmsh_air

            (r0_air, z0_air, dr_air, dz_air) = gmsh_air(Object, AirData)
            AirData = (z0_air, z0_air + dz_air, r0_air + dr_air, 10)

        yamlfile = args.filename.replace(".yaml", "")
        if air:
            yamlfile += "_Air"
        yamlfile += "_gmshaxidata"
        meshAxiData = createMeshAxiData(prefix, Object, AirData, yamlfile, args.algo2d)

        gmsh_msh(args.algo2d, meshAxiData, boxes, air, args.scaling)
        if not args.thickslit:
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
