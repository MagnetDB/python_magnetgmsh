"""
Geometry Configuration Loading for Gmsh.

This module provides functions to load magnet geometry configurations from
python_magnetgeo objects and convert them to Gmsh-compatible representations.
It handles multiple geometry types including Bitter plates, superconducting
magnets, helices, inserts, and complete magnet sites.

The module uses a dispatch pattern (action_dict) to route different geometry
types to their appropriate loader functions. All loaders return standardized
GeometryLoadResult objects containing solid names, cooling channels, and
electrical isolant definitions.

Typical Usage:
    from python_magnetgmsh.cfg import loadcfg
    
    # Load any supported geometry type
    solid_names, channels = loadcfg("magnet.yaml", "gmsh_model", is2D=True)
    
    # Or use type-specific loaders directly
    from python_magnetgmsh.cfg import Bitter_Gmsh
    result = Bitter_Gmsh("", bitter_geometry, "model", is2D=True)

Supported Geometry Types:
    - Bitter: Single Bitter plate with cooling slits
    - Bitters: Collection of multiple Bitter plates
    - Supra: Single superconducting coil
    - Supras: Collection of superconducting coils
    - Helix: Helical conductor geometry
    - Insert: Complete magnet insert assembly
    - MSite: Measurement site with multiple magnets

Dependencies:
    - python_magnetgeo >= 1.0.0: Geometry definitions
    - gmsh >= 4.13.1: Mesh generation

See Also:
    - python_magnetgeo.Bitter: Bitter plate geometry definitions
    - python_magnetgeo.Supra: Superconducting coil definitions
    - python_magnetgeo.Insert: Insert assembly definitions
"""

from dataclasses import dataclass, field
from typing import List, Dict, Union, Optional
import logging


# Lazy loading import - automatically detects geometry type
from python_magnetgeo.utils import getObject
from python_magnetgeo.validation import ValidationError
from python_magnetgeo import Insert, Helix, Bitter, Bitters, Supra, Supras, Screen, MSite  # For type checking only

logger = logging.getLogger(__name__)

@dataclass
class GeometryLoadResult:
    """
    Result from loading and processing geometry configuration.
    
    This standardized result structure is returned by all geometry loader
    functions to provide consistent access to generated Gmsh objects and
    associated metadata.
    
    Attributes:
        name: Optional name identifier for the loaded geometry. Used primarily
            for MSite and composite geometries. None for simple geometries.
        solid_names: List of Gmsh solid object names created during loading.
            These correspond to physical volumes in the Gmsh model.
        channels: Cooling channel definitions. Can be:
            - dict: For MSite geometries with complex channel mappings
            - list: For simple geometries with named channels
            - None: If geometry has no cooling channels
        isolants: Electrical isolant region definitions. Typically a dict
            mapping isolant names to their properties. None if no isolants.
    
    Example:
        >>> result = Bitter_Gmsh("B1", bitter_geom, "model", is2D=True)
        >>> print(result.solid_names)
        ['B1_Conductor', 'B1_Insulation']
        >>> print(result.channels)
        ['B1_CoolingSlits', 'B1_Tierod']
    """
    name: Optional[str] = None
    solid_names: List[str] = field(default_factory=list)
    channels: Optional[Union[Dict, List]] = None
    isolants: Optional[Union[Dict, List]] = None

def Supra_Gmsh(
    mname: str, cad: Supra.Supra, gname: str, is2D: bool, verbose: bool = False
) -> GeometryLoadResult:
    """
    Load superconducting coil geometry and convert to Gmsh representation.
    
    Processes a Supra (superconducting coil) geometry object and extracts
    solid names, cooling channels, and electrical isolants for Gmsh mesh
    generation. Handles both 2D axisymmetric and 3D representations.
    
    Args:
        mname: Name prefix for Gmsh objects. If non-empty, prepended to all
            generated object names (e.g., "Insert1_" → "Insert1_SupraCoil").
            Pass empty string for no prefix.
        cad: Superconducting coil geometry object from python_magnetgeo.
            Must be a valid Supra instance with required geometric parameters.
        gname: Gmsh model name. Used for internal Gmsh model identification
            and potential error reporting.
        is2D: Geometry dimensionality flag.
            - True: Generate 2D axisymmetric representation
            - False: Generate full 3D geometry
        verbose: Enable detailed console output for debugging. When True,
            prints intermediate processing steps and object names.
    
    Returns:
        GeometryLoadResult containing:
            - solid_names: Tuple of created Gmsh solid object names
            - channels: List of cooling channel identifiers
            - isolants: Dict of electrical isolant definitions
    
    Raises:
        ValidationError: If cad geometry fails validation checks from
            python_magnetgeo (e.g., invalid dimensions, missing required fields)
        AttributeError: If cad object missing required methods or attributes
    
    Example:
        >>> from python_magnetgeo import Supra
        >>> supra = Supra(name="SC1", r=[50, 100], z=[0, 200])
        >>> result = Supra_Gmsh("", supra, "model", is2D=True, verbose=True)
        >>> print(result.solid_names)
        ('SC1_Conductor', 'SC1_Insulation', 'SC1_Mandrin')
        >>> print(result.channels)
        ['SC1_CoolingChannel']
    
    Notes:
        - Delegates to cad.get_names() for solid name generation
        - Cooling channels extracted via cad.get_channels()
        - Isolants extracted via cad.get_isolants()
        - All extraction methods respect is2D and verbose flags
    
    See Also:
        Supras_Gmsh: For loading collections of superconducting coils
        python_magnetgeo.Supra: Source geometry class definition
    """
    logger.info(f"Loading Supra geometry: {cad.name}")
    logger.debug(f"Supra_Gmsh: mname={mname}, gname={gname}, is2D={is2D}")
    prefix = ""
    if mname:
        prefix = mname
    
    solid_names=cad.get_names(prefix, is2D, verbose)
    logger.debug(f"Created {len(solid_names)} solid objects: {solid_names}")
    channels = cad.get_channels(mname)
    isolants = cad.get_isolants(mname)
    return GeometryLoadResult(solid_names=solid_names, channels=channels, isolants=isolants)


def Bitter_Gmsh(
    mname: str, cad: Bitter.Bitter, gname: str, is2D: bool, verbose: bool = False
) -> GeometryLoadResult:
    """
    Load Bitter plate geometry and convert to Gmsh representation.
    
    Processes a Bitter plate geometry object including conductor geometry,
    cooling slits, and optional tie rods. Extracts all components needed
    for Gmsh mesh generation with proper physical group definitions.
    
    Args:
        mname: Name prefix for Gmsh objects. Prepended to all generated
            names to maintain unique identifiers in complex assemblies.
            Use empty string for standalone geometries.
        cad: Bitter plate geometry object from python_magnetgeo. Must
            contain valid radial bounds, height, and optional cooling
            slit and tie rod definitions.
        gname: Gmsh model name for internal tracking and error reporting.
        is2D: Geometry dimensionality flag.
            - True: Generate 2D axisymmetric sector
            - False: Generate full 3D geometry with angular periodicity
        verbose: Enable detailed debug output including intermediate
            geometry creation steps and physical group assignments.
    
    Returns:
        GeometryLoadResult containing:
            - solid_names: Tuple of Gmsh solid names for conductors and
                supporting structures
            - channels: List of cooling channel names including slits and
                optional tie rod channels
            - isolants: Dict of electrical isolant region definitions
    
    Raises:
        ValidationError: If Bitter geometry invalid (e.g., inner radius
            greater than outer radius, invalid cooling slit definitions)
        AttributeError: If cad missing required geometry methods
    
    Example:
        >>> from python_magnetgeo import Bitter
        >>> bitter = Bitter(
        ...     name="B1",
        ...     r=[100, 200],
        ...     z=[0, 50],
        ...     coolingslits=[...]
        ... )
        >>> result = Bitter_Gmsh("Insert_", bitter, "model", is2D=True)
        >>> print(result.solid_names)
        ('Insert_B1_Conductor',)
        >>> print(result.channels)
        ['Insert_B1_CoolingSlit1', 'Insert_B1_CoolingSlit2', 'Insert_B1_Tierod']
    
    Notes:
        - Automatically includes tie rod in channels if present
        - Cooling slits processed individually for independent mesh control
        - Channel names follow pattern: {prefix}{name}_{ChannelType}
        - 2D mode generates sector geometry based on tie rod count
    
    See Also:
        Bitters_Gmsh: For loading multiple Bitter plates
        python_magnetgeo.Bitter: Source geometry class
    """
    logger.info(f"Loading Bitter geometry: {cad.name}")
    logger.debug(f"Bitter_Gmsh: mname={mname}, gname={gname}, is2D={is2D}")
    prefix = ""
    if mname:
        prefix = mname

    solid_names=cad.get_names(prefix, is2D, verbose)
    channels = cad.get_channels(mname)
    isolants = cad.get_isolants(mname)
    
    # Add tierod as a channel if present for boundary condition definition
    if cad.tierod is not None:
        channels.append(f"{cad.name}_Tierod")

    return GeometryLoadResult(solid_names=solid_names, channels=channels, isolants=isolants)


def Helix_Gmsh(
    mname: str, cad: Helix.Helix, gname: str, is2D: bool, verbose: bool = False
) -> GeometryLoadResult:
    """
    Load helical coil geometry and convert to Gmsh representation.
    
    Processes a Helix (helical conductor) geometry for Gmsh mesh generation.
    Handles both simple helices and complex multi-layer wound conductors.
    
    Args:
        mname: Name prefix for generated Gmsh objects. Used to maintain
            unique identifiers in assemblies with multiple helices.
        cad: Helix geometry object from python_magnetgeo containing
            conductor path, cross-section, and winding parameters.
        gname: Gmsh model name for internal reference.
        is2D: Geometry dimensionality.
            - True: 2D axisymmetric representation (simplified cross-section)
            - False: Full 3D helical geometry
        verbose: Enable detailed processing output for debugging.
    
    Returns:
        GeometryLoadResult with solid_names tuple. Channels and isolants
        are None for simple helix geometries unless explicitly defined.
    
    Raises:
        ValidationError: If helix geometry invalid (e.g., negative pitch,
            invalid cross-section dimensions)
    
    Example:
        >>> from python_magnetgeo import Helix
        >>> helix = Helix(
        ...     name="H1",
        ...     r=[50, 60],
        ...     z=[0, 300],
        ...     cutwidth=5.0
        ... )
        >>> result = Helix_Gmsh("Coil_", helix, "model", is2D=False)
        >>> print(result.solid_names)
        ('Coil_H1_Conductor',)
    
    Notes:
        - 2D mode projects helix onto r-z plane
        - 3D mode generates full helical path
        - Conductor cross-section handled by cad.get_names()
    
    See Also:
        python_magnetgeo.Helix: Source geometry class
    """
    logger.info(f"Loading Helix geometry: {cad.name}")
    logger.debug(f"Helix_Gmsh: mname={mname}, gname={gname}, is2D={is2D}")
    prefix = ""
    if mname:
        prefix = mname
    return GeometryLoadResult(solid_names=cad.get_names(prefix, is2D, verbose))

def Insert_Gmsh(
    mname: str, cad: Insert.Insert, gname: str, is2D: bool, verbose: bool = False
) -> GeometryLoadResult:
    """
    Load complete magnet insert assembly and convert to Gmsh representation.
    
    Processes a full Insert assembly which may contain multiple helices,
    rings, current leads, and other components. Aggregates all components
    into a unified Gmsh representation with proper physical groups.
    
    Args:
        mname: Name prefix for all generated objects. Important for
            distinguishing multiple inserts in a magnet site.
        cad: Insert assembly geometry from python_magnetgeo. Contains
            collections of helices, rings, screens, and other components.
        gname: Gmsh model name for tracking.
        is2D: Geometry dimensionality.
            - True: Generate 2D axisymmetric model (faster, suitable for
                axisymmetric problems)
            - False: Generate full 3D geometry (required for non-axisymmetric
                features like current leads)
        verbose: Enable detailed output showing each component as processed.
    
    Returns:
        GeometryLoadResult containing:
            - solid_names: Tuple of all solid names from all components
            - channels: Aggregated list of cooling channels from all parts
            - isolants: Combined dict of all electrical isolants
    
    Raises:
        ValidationError: If Insert assembly invalid or contains invalid
            component geometries
        ValueError: If Insert contains unsupported component types
    
    Example:
        >>> from python_magnetgeo import Insert
        >>> insert = Insert.from_yaml("HL-31.yaml")
        >>> result = Insert_Gmsh("", insert, "HL31_model", is2D=True, verbose=True)
        >>> print(len(result.solid_names))
        15  # H1-H10 helices + 2 rings + leads + screens
        >>> print(result.channels)
        ['H1_Cooling', 'H2_Cooling', ..., 'Ring1_Channel']
    
    Notes:
        - Processes all helices sequentially
        - Handles rings, current leads, and screens
        - Aggregates channels and isolants from all components
        - Maintains component hierarchy in naming
    
    See Also:
        python_magnetgeo.Insert: Source assembly class
        Helix_Gmsh: Individual helix processing
    """
    logger.info(f"Loading Insert geometry: {cad.name}")
    logger.debug(f"Insert_Gmsh: mname={mname}, gname={gname}, is2D={is2D}")
    logger.debug(f"cad.get_names: {cad.get_names(mname, is2D, verbose)}")
    
    solid_names=cad.get_names(mname, is2D, verbose)
    channels = cad.get_channels(mname)
    isolants = cad.get_isolants(mname)
    return GeometryLoadResult(solid_names=solid_names, channels=channels, isolants=isolants)

def Bitters_Gmsh(
    mname: str, cad: Bitters.Bitters, gname: str, is2D: bool, verbose: bool = False
) -> GeometryLoadResult:
    """
    Load collection of Bitter plates and convert to Gmsh representation.
    
    Processes multiple Bitter plates as a unified assembly, typically
    representing a resistive magnet stack. Maintains individual plate
    identities while aggregating results.
    
    Args:
        mname: Name prefix for the entire Bitters assembly. Individual
            plates get additional suffixes.
        cad: Bitters collection from python_magnetgeo containing list
            of individual Bitter plate geometries.
        gname: Gmsh model name.
        is2D: Geometry dimensionality flag passed to each plate.
        verbose: Enable detailed output for each plate processing.
    
    Returns:
        GeometryLoadResult with:
            - solid_names: Concatenated tuple of solids from all plates
            - channels: Combined list of all cooling channels
            - isolants: Merged dict of isolants from all plates
    
    Raises:
        ValidationError: If any Bitter plate in collection is invalid
    
    Example:
        >>> from python_magnetgeo import Bitters
        >>> bitters = Bitters(magnets=[bitter1, bitter2, bitter3])
        >>> result = Bitters_Gmsh("Stack_", bitters, "model", is2D=True)
        >>> print(result.solid_names)
        ('Stack_B1_Conductor', 'Stack_B2_Conductor', 'Stack_B3_Conductor')
    
    Notes:
        - Processes plates sequentially
        - Preserves individual plate names
        - Aggregates channels and isolants across all plates
    
    See Also:
        Bitter_Gmsh: Individual plate processing
        python_magnetgeo.Bitters: Source collection class
    """
    logger.info(f"Loading Bitters geometry collection")
    logger.debug(f"Bitters_Gmsh: mname={mname}, gname={gname}, is2D={is2D}")
    solid_names = []
    prefix = ""
    if mname:
        prefix = f"{mname}"

    for magnet in cad.magnets:
        _res = Bitter_Gmsh(f"{prefix}{magnet.name}", magnet, gname, is2D, verbose)
        logger.debug(f"Bitter_Gmsh result: {len(_res.solid_names)} solids")
        solid_names += _res.solid_names
        
    channels = cad.get_channels(mname)
    isolants = cad.get_isolants(mname)
    return GeometryLoadResult(solid_names=solid_names, channels=channels, isolants=isolants)


def Supras_Gmsh(
    mname: str, cad: Supras.Supras, gname: str, is2D: bool, verbose: bool = False
) -> GeometryLoadResult:
    """
    Load collection of superconducting coils and convert to Gmsh representation.
    
    Processes multiple Supra coils as unified assembly, typically representing
    a superconducting magnet system with multiple coil sections.
    
    Args:
        mname: Name prefix for the Supras assembly.
        cad: Supras collection from python_magnetgeo containing multiple
            Supra coil geometries.
        gname: Gmsh model name.
        is2D: Geometry dimensionality flag.
        verbose: Enable detailed output for each coil.
    
    Returns:
        GeometryLoadResult with aggregated data from all coils.
    
    Example:
        >>> from python_magnetgeo import Supras
        >>> supras = Supras(magnets=[supra1, supra2])
        >>> result = Supras_Gmsh("SC_", supras, "model", is2D=True)
        >>> print(result.solid_names)
        ('SC_Supra1_Conductor', 'SC_Supra2_Conductor')
    
    See Also:
        Supra_Gmsh: Individual coil processing
    """
    logger.info(f"Loading Supras geometry collection")
    logger.debug(f"Supras_Gmsh: mname={mname}, gname={gname}, is2D={is2D}")
    solid_names = []
    channels = []
    isolants = []

    prefix = ""
    if mname:
        prefix = f"{mname}"

    for magnet in cad.magnets:
        _res = Supra_Gmsh(f"{prefix}{magnet.name}", magnet, gname, is2D, verbose)
        solid_names += _res.solid_names
    return GeometryLoadResult(solid_names=solid_names, channels=channels, isolants=isolants)


from python_magnetgeo.utils import getObject

def Magnet_Gmsh(
    mname: str, cad: Union[Bitters.Bitters, Supras.Supras, Insert.Insert], gname: str, is2D: bool, verbose: bool = False
) -> GeometryLoadResult:
    """
    Generic magnet loader using dispatch pattern.
    
    Routes different magnet types to appropriate specialized loaders using
    the action_dict dispatch table. Provides unified interface for loading
    any supported magnet geometry type.
    
    Args:
        mname: Name prefix for generated objects.
        cad: Magnet geometry object. Type automatically detected and routed
            to correct loader function.
        gname: Gmsh model name.
        is2D: Geometry dimensionality flag.
        verbose: Enable detailed output.
    
    Returns:
        GeometryLoadResult from the appropriate type-specific loader.
    
    Raises:
        ValueError: If cad type not in action_dict (unsupported geometry)
        ValidationError: If geometry validation fails
    
    Example:
        >>> from python_magnetgeo.utils import getObject
        >>> magnet = getObject("magnet_config.yaml")  # Auto-detects type
        >>> result = Magnet_Gmsh("", magnet, "model", is2D=True)
    
    Notes:
        - Uses type-based dispatch via action_dict
        - Automatically selects correct loader function
        - Supports: Bitter, Bitters, Supra, Supras, Helix, Insert, MSite
    
    See Also:
        action_dict: Dispatch table mapping types to loaders
    """
        
    pname = cad.name
    logger.info(f"Loading magnet: {pname}")
    logger.debug(f"Magnet_Gmsh: mname={mname}, gname={gname}, type={type(cad).__name__}")
    solid_names = []
    channels = []
    isolants = []

    # logger.debug(f'cad: {cad}, type={type(cad)}')
    _res = action_dict[type(cad)]["run"](mname, cad, pname, is2D, verbose)
    solid_names += _res.solid_names
    channels += _res.channels
    isolants += _res.isolants
    logger.debug(f"Magnet_Gmsh: {cad.name} processed [{len(solid_names)} solids]")
    return GeometryLoadResult(name=pname, solid_names=solid_names, channels=channels, isolants=isolants)


def MSite_Gmsh(
    mname: str, cad: MSite.MSite, gname: str, is2D: bool, verbose: bool = False
) -> GeometryLoadResult:
    """
    Load complete measurement site with multiple magnets.
    
    Processes an MSite (Measurement Site) containing multiple magnet
    assemblies positioned in space. Represents complete experimental
    setup with field generation and measurement equipment.
    
    Args:
        mname: Name prefix (typically empty for top-level MSite).
        cad: MSite geometry from python_magnetgeo containing positioned
            magnet assemblies and measurement probes.
        gname: Gmsh model name.
        is2D: Geometry dimensionality. MSites can be complex, so 2D mode
            may have limitations for non-axisymmetric arrangements.
        verbose: Enable detailed output showing each magnet processed.
    
    Returns:
        GeometryLoadResult with:
            - solid_names: All solids from all magnets in site
            - channels: Dict mapping magnet names to their channels
            - isolants: Dict of all isolants in site
    
    Raises:
        ValidationError: If MSite configuration invalid
        ValueError: If MSite contains unsupported magnet types
    
    Example:
        >>> from python_magnetgeo import MSite
        >>> site = MSite.from_yaml("site_config.yaml")
        >>> result = MSite_Gmsh("", site, "facility_model", is2D=False)
        >>> print(result.channels)
        {
            'Bitter_Stack': ['B1_Cooling', 'B2_Cooling'],
            'SC_Coil': ['SC1_Channel'],
            'Insert': ['H1_Cooling', ...]
        }
    
    Notes:
        - Processes each magnet via Magnet_Gmsh()
        - Maintains spatial relationships between magnets
        - channels returned as dict for complex site structure
        - Suitable for multi-magnet facilities
    
    See Also:
        Magnet_Gmsh: Individual magnet processing
        python_magnetgeo.MSite: Source site class
    """

    logger.info(f"Loading MSite geometry: {cad.name}")
    logger.debug(f"MSite_Gmsh: gname={gname}, is2D={is2D}")
    # logger.debug("MSite Channels:", cad.get_channels())

    solid_names = []
    Channels = cad.get_channels("")
    Isolants = cad.get_isolants("")

    for magnet in cad.magnets:
        _res = Magnet_Gmsh("", magnet, solid_names, is2D, verbose)
        solid_names += _res.solid_names

    logger.debug(f"Channels: {Channels}")
    logger.debug(f"MSite_Gmsh: {cad.name} processed [{len(solid_names)} solids]")
    return GeometryLoadResult(solid_names=solid_names, channels=Channels, isolants=Isolants)

action_dict = {
    Bitter.Bitter: {"run": Bitter_Gmsh, "msg": "Bitter"},
    Bitters.Bitters: {"run": Bitters_Gmsh, "msg": "Bitters"},
    Supra.Supra: {"run": Supra_Gmsh, "msg": "Supra"},
    Supras.Supras: {"run": Supras_Gmsh, "msg": "Supras"},
    Helix.Helix: {"run": Helix_Gmsh, "msg": "Helix"},
    Insert.Insert: {"run": Insert_Gmsh, "msg": "Insert"},
    MSite.MSite: {"run": MSite_Gmsh, "msg": "MSite"},
}

def loadcfg(
    cfgfile: str, gname: str, is2D: bool, verbose: bool = False
) -> tuple[list[str], dict | list]:
    """
    Main entry point for loading any geometry configuration file.
    
    Loads a YAML geometry configuration file, automatically detects the
    geometry type, routes to appropriate loader, and returns standardized
    results. This is the primary function users should call for loading
    geometries.
    
    Args:
        cfgfile: Path to YAML geometry configuration file. Must be valid
            python_magnetgeo format with type annotation (e.g., !<Insert>).
        gname: Gmsh model name to use for this geometry.
        is2D: Geometry dimensionality.
            - True: Generate 2D axisymmetric model
            - False: Generate full 3D geometry
        verbose: Enable detailed processing output showing each step of
            geometry loading and conversion.
    
    Returns:
        Tuple containing:
            - solid_names (list[str]): List of all Gmsh solid object names
                created from the geometry
            - channels (dict | list): Cooling channel definitions. Format
                depends on geometry type:
                - list: For simple geometries (Bitter, Supra, Insert, Helix)
                - dict: For complex assemblies (MSite)
                - []: Empty list if geometry has no channels
    
    Raises:
        ValidationError: If geometry file contains invalid data or fails
            python_magnetgeo validation checks
        ValueError: If geometry type not supported (not in action_dict)
        FileNotFoundError: If cfgfile path does not exist
        yaml.YAMLError: If cfgfile is not valid YAML
    
    Example:
        >>> # Load a simple Insert geometry
        >>> solids, channels = loadcfg("HL-31.yaml", "HL31_model", is2D=True)
        >>> print(f"Created {len(solids)} solids")
        Created 15 solids
        >>> print(f"Cooling channels: {channels}")
        Cooling channels: ['H1_Cooling', 'H2_Cooling', ..., 'Ring1_Channel']
        
        >>> # Load a complex MSite
        >>> solids, channels = loadcfg("facility.yaml", "facility", is2D=False, verbose=True)
        >>> print(type(channels))
        <class 'dict'>
        >>> print(channels.keys())
        dict_keys(['Bitter_Stack', 'SC_Coil', 'Insert'])
    
    Notes:
        - Automatically detects geometry type from YAML type annotation
        - Converts None channels to empty list for consistency
        - Prints processing information to stdout (for verbose or debugging)
        - Type detection uses python_magnetgeo.utils.getObject()
        - All geometry classes must be registered in action_dict
    
    See Also:
        getObject: Geometry file loader with automatic type detection
        action_dict: Supported geometry types and their loaders
        GeometryLoadResult: Internal result structure
    
    Version History:
        - 0.1.0: Added ValidationError handling and improved error messages
        - 0.0.x: Initial implementation with basic type dispatch
    """
    logger.info(f"Loading configuration: {cfgfile}")
    logger.debug(f"loadcfg: gname={gname}, is2D={is2D}")

    solid_names = []
    Channels = None

    try:
        cad = getObject(cfgfile)
        logger.info(f"Loaded {type(cad).__name__}: {cad.name}")
    except ValidationError as e:
        # Handle validation errors from python_magnetgeo
        logger.error(f"Validation error in {cfgfile}: {e}")
        raise
    
    logger.debug(f"Geometry type: {type(cad).__name__}")

    mname = ""
    if type(cad) not in action_dict:
        raise ValueError(
            f"Unsupported geometry type: {type(cad).__name__}. "
            f"Supported types: {', '.join(cls.__name__ for cls in action_dict.keys())}"
        )
    result = action_dict[type(cad)]["run"](mname, cad, gname, is2D, verbose)
    logger.debug(f"Loader results: {len(result.solid_names)} solids, {len(result.channels) if result.channels else 0} channels")
    
    # Extract channels, handle None case
    channels = result.channels if result.channels is not None else []
    
    logger.info(f"Configuration loaded: {len(result.solid_names)} solids, {len(channels) if isinstance(channels, list) else 'dict'} channels")
    return (result.solid_names, channels)
