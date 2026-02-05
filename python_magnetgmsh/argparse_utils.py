"""
Shared argparse utilities for python_magnetgmsh CLI tools.

This module provides common argument definitions and helper functions to ensure
consistency across different command-line interfaces (xao2msh.py, cli.py, rotate.py).

The module defines argument groups that can be added to any ArgumentParser:
    - Common arguments: debug, verbose, logging
    - Working directory arguments
    - Gmsh display arguments
    - Mesh generation arguments
    - Algorithm selection arguments

Typical Usage:
    from .argparse_utils import add_common_args, add_wd_arg, add_show_arg
    
    parser = argparse.ArgumentParser()
    add_common_args(parser)
    add_wd_arg(parser)
    add_show_arg(parser)
    args = parser.parse_args()

Benefits:
    - Consistency: Same argument names and help text across all tools
    - Maintainability: Single source of truth for common arguments
    - Extensibility: Easy to add new common arguments

See Also:
    - xao2msh.py: XAO to mesh converter CLI
    - cli.py: Main magnetgmsh CLI
    - rotate.py: Mesh rotation utility CLI
"""

import argparse
from typing import Optional


def add_common_args(parser: argparse.ArgumentParser) -> None:
    """
    Add common debugging and logging arguments to an ArgumentParser.
    
    Adds:
        --debug: Activate debug mode (maximum verbosity)
        --verbose: Activate verbose mode (detailed output)
        --log: Save log output to specified file
    
    Args:
        parser: ArgumentParser instance to add arguments to
    
    Example:
        >>> parser = argparse.ArgumentParser()
        >>> add_common_args(parser)
        >>> args = parser.parse_args(['--debug', '--log', 'output.log'])
        >>> args.debug
        True
    """
    parser.add_argument(
        "--debug",
        help="activate debug mode (maximum verbosity)",
        action="store_true"
    )
    parser.add_argument(
        "--verbose",
        help="activate verbose mode (detailed output)",
        action="store_true"
    )
    parser.add_argument(
        "--log",
        help="save log output to specified file",
        type=str,
        metavar="LOGFILE"
    )


def add_wd_arg(parser: argparse.ArgumentParser) -> None:
    """
    Add working directory argument to an ArgumentParser.
    
    Adds:
        --wd: Set a working directory for input/output operations
    
    Args:
        parser: ArgumentParser instance to add arguments to
    
    Example:
        >>> parser = argparse.ArgumentParser()
        >>> add_wd_arg(parser)
        >>> args = parser.parse_args(['--wd', '/data/meshes'])
        >>> args.wd
        '/data/meshes'
    """
    parser.add_argument(
        "--wd",
        help="set a working directory",
        type=str,
        default=""
    )


def add_show_arg(parser: argparse.ArgumentParser) -> None:
    """
    Add Gmsh GUI display argument to an ArgumentParser.
    
    Adds:
        --show: Display Gmsh GUI (requires X11 or display server)
    
    Args:
        parser: ArgumentParser instance to add arguments to
    
    Example:
        >>> parser = argparse.ArgumentParser()
        >>> add_show_arg(parser)
        >>> args = parser.parse_args(['--show'])
        >>> args.show
        True
    """
    parser.add_argument(
        "--show",
        help="display Gmsh GUI (requires X11 or display server)",
        action="store_true"
    )


def add_scaling_arg(parser: argparse.ArgumentParser) -> None:
    """
    Add geometry scaling argument to an ArgumentParser.
    
    Adds:
        --scaling: Scale to meters (default unit is millimeters)
    
    Args:
        parser: ArgumentParser instance to add arguments to
    
    Example:
        >>> parser = argparse.ArgumentParser()
        >>> add_scaling_arg(parser)
        >>> args = parser.parse_args(['--scaling'])
        >>> args.scaling
        True
    """
    parser.add_argument(
        "--scaling",
        help="scale to m (default unit is mm)",
        action="store_true"
    )


def add_lc_arg(parser: argparse.ArgumentParser) -> None:
    """
    Add mesh size loading argument to an ArgumentParser.
    
    Adds:
        --lc: Load mesh characteristic length from file
    
    Args:
        parser: ArgumentParser instance to add arguments to
    
    Example:
        >>> parser = argparse.ArgumentParser()
        >>> add_lc_arg(parser)
        >>> args = parser.parse_args(['--lc'])
        >>> args.lc
        True
    """
    parser.add_argument(
        "--lc",
        help="load mesh size from file",
        action="store_true"
    )


def add_algo2d_arg(parser: argparse.ArgumentParser, choices: list, default: str = "Delaunay") -> None:
    """
    Add 2D meshing algorithm argument to an ArgumentParser.
    
    Adds:
        --algo2d: Select an algorithm for 2D mesh generation
    
    Args:
        parser: ArgumentParser instance to add arguments to
        choices: List of allowed algorithm names
        default: Default algorithm (default: "Delaunay")
    
    Example:
        >>> from .mesh.axi import get_allowed_algo
        >>> parser = argparse.ArgumentParser()
        >>> add_algo2d_arg(parser, get_allowed_algo())
        >>> args = parser.parse_args(['--algo2d', 'MeshAdapt'])
        >>> args.algo2d
        'MeshAdapt'
    """
    parser.add_argument(
        "--algo2d",
        help="select an algorithm for 2d mesh",
        type=str,
        choices=choices,
        default=default
    )


def add_algo3d_arg(parser: argparse.ArgumentParser, choices: list, default: str = "HXT") -> None:
    """
    Add 3D meshing algorithm argument to an ArgumentParser.
    
    Adds:
        --algo3d: Select an algorithm for 3D mesh generation
    
    Args:
        parser: ArgumentParser instance to add arguments to
        choices: List of allowed algorithm names
        default: Default algorithm (default: "HXT")
    
    Example:
        >>> from .mesh.m3d import get_allowed_algo
        >>> parser = argparse.ArgumentParser()
        >>> add_algo3d_arg(parser, get_allowed_algo())
        >>> args = parser.parse_args(['--algo3d', 'Delaunay'])
        >>> args.algo3d
        'Delaunay'
    """
    parser.add_argument(
        "--algo3d",
        help="select an algorithm for 3d mesh",
        type=str,
        choices=choices,
        default=default
    )


def add_mesh_args(parser: argparse.ArgumentParser, 
                  algo2d_choices: Optional[list] = None, 
                  algo3d_choices: Optional[list] = None,
                  include_algo2d: bool = True,
                  include_algo3d: bool = False) -> None:
    """
    Add common mesh generation arguments to an ArgumentParser.
    
    Adds a group of mesh-related arguments:
        --scaling: Scale to meters
        --lc: Load mesh size from file
        --algo2d: 2D meshing algorithm (if include_algo2d=True)
        --algo3d: 3D meshing algorithm (if include_algo3d=True)
    
    Args:
        parser: ArgumentParser instance to add arguments to
        algo2d_choices: List of allowed 2D algorithms (required if include_algo2d=True)
        algo3d_choices: List of allowed 3D algorithms (required if include_algo3d=True)
        include_algo2d: Whether to include --algo2d argument
        include_algo3d: Whether to include --algo3d argument
    
    Example:
        >>> from .mesh.axi import get_allowed_algo as get_2d_algos
        >>> parser = argparse.ArgumentParser()
        >>> add_mesh_args(parser, algo2d_choices=get_2d_algos())
        >>> args = parser.parse_args(['--scaling', '--lc', '--algo2d', 'Delaunay'])
    """
    add_scaling_arg(parser)
    add_lc_arg(parser)
    
    if include_algo2d:
        if algo2d_choices is None:
            raise ValueError("algo2d_choices must be provided when include_algo2d=True")
        add_algo2d_arg(parser, algo2d_choices)
    
    if include_algo3d:
        if algo3d_choices is None:
            raise ValueError("algo3d_choices must be provided when include_algo3d=True")
        add_algo3d_arg(parser, algo3d_choices)


def add_all_common_args(parser: argparse.ArgumentParser) -> None:
    """
    Add all common arguments (debug, verbose, log, wd, show) to an ArgumentParser.
    
    This is a convenience function that adds the most frequently used arguments
    across all python_magnetgmsh CLI tools.
    
    Adds:
        --debug: Debug mode
        --verbose: Verbose mode
        --log: Log file
        --wd: Working directory
        --show: Display Gmsh GUI
    
    Args:
        parser: ArgumentParser instance to add arguments to
    
    Example:
        >>> parser = argparse.ArgumentParser()
        >>> add_all_common_args(parser)
        >>> args = parser.parse_args(['--debug', '--wd', '/data', '--show'])
    """
    add_common_args(parser)
    add_wd_arg(parser)
    add_show_arg(parser)
