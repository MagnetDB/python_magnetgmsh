from typing import Union

# Lazy loading import - automatically detects geometry type
from python_magnetgeo.utils import getObject
from python_magnetgeo.validation import ValidationError
from python_magnetgeo import Insert, Helix, Bitter, Bitters, Supra, Supras, Screen, MSite  # For type checking only


from typing import NamedTuple

class GeometryLoadResult(NamedTuple):
    """Result from loading geometry configuration."""
    name: str| None = None
    solid_names: list[str] = []
    channels: dict | list | None = None
    isolants: dict | None = None

def Supra_Gmsh(
    mname: str, cad: Supra.Supra, gname: str, is2D: bool, verbose: bool = False
) -> GeometryLoadResult:
    """Load Supra cad"""
    print(f"Supra_Gmsh: mname={mname}, cad={cad.name}, gname={gname}")
    prefix = ""
    if mname:
        prefix = mname
    
    solid_names=cad.get_names(prefix, is2D, verbose)
    print('supra: solid_names:', solid_names, flush=True)
    channels = cad.get_channels(mname)
    isolants = cad.get_isolants(mname)
    return GeometryLoadResult(solid_names=solid_names, channels=channels, isolants=isolants)


def Bitter_Gmsh(
    mname: str, cad: Bitter.Bitter, gname: str, is2D: bool, verbose: bool = False
) -> GeometryLoadResult:
    """Load Bitter cad"""
    print(f"Bitter_Gmsh: mname={mname}, cad={cad.name}, gname={gname}")
    prefix = ""
    if mname:
        prefix = mname

    solid_names=cad.get_names(prefix, is2D, verbose)
    channels = cad.get_channels(mname)
    isolants = cad.get_isolants(mname)
    
    # why??
    if cad.tierod is not None:
        channels.append(f"{cad.name}_Tierod")

    return GeometryLoadResult(solid_names=solid_names, channels=channels, isolants=isolants)


def Helix_Gmsh(
    mname: str, cad: Helix.Helix, gname: str, is2D: bool, verbose: bool = False
) -> GeometryLoadResult:
    """Load Helix cad"""
    print(f"Helix_Gmsh: mname={mname}, cad={cad.name}, gname={gname}")
    prefix = ""
    if mname:
        prefix = mname
    return GeometryLoadResult(solid_names=cad.get_names(prefix, is2D, verbose))

def Insert_Gmsh(
    mname: str, cad: Insert.Insert, gname: str, is2D: bool, verbose: bool = False
) -> GeometryLoadResult:
    """Load Insert"""
    print(f"Insert_Gmsh: mname={mname}, cad={cad.name}, gname={gname}")
    print('cad.get_names: ', cad.get_names(mname, is2D, verbose))
    
    solid_names=cad.get_names(mname, is2D, verbose)
    channels = cad.get_channels(mname)
    isolants = cad.get_isolants(mname)
    return GeometryLoadResult(solid_names=solid_names, channels=channels, isolants=isolants)

def Bitters_Gmsh(
    mname: str, cad: Bitters.Bitters, gname: str, is2D: bool, verbose: bool = False
) -> GeometryLoadResult:
    """Load Bitters"""
    print(f"Bitters_Gmsh: mname={mname}, gname={gname}")
    solid_names = []
    prefix = ""
    if mname:
        prefix = f"{mname}"

    for magnet in cad.magnets:
        _res = Bitter_Gmsh(f"{prefix}{magnet.name}", magnet, gname, is2D, verbose)
        print(f"Bitter_Gmsh: _names={_res.solid_names}")
        solid_names += _res.solid_names
        
    channels = cad.get_channels(mname)
    isolants = cad.get_isolants(mname)
    return GeometryLoadResult(solid_names=solid_names, channels=channels, isolants=isolants)


def Supras_Gmsh(
    mname: str, cad: Supras.Supras, gname: str, is2D: bool, verbose: bool = False
) -> GeometryLoadResult:
    """Load Supras"""
    print(f"Supras_Gmsh: mname={mname}, gname={gname}")
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
    """Load Magnet cad"""
        
    pname = cad.name
    print(f"Magnet_Gmsh: mname={mname}, cad={pname}, gname={gname}")
    solid_names = []
    channels = []
    isolants = []

    # print('pcad: {pcad} type={type(pcad)}')
    _res = action_dict[type(cad)]["run"](mname, cad, pname, is2D, verbose)
    solid_names += _res.solid_names
    channels += _res.channels
    isolants += _res.isolants
    if verbose:
        print(f"Magnet_Gmsh: {cad} Done [solids {len(solid_names)}]")
    return GeometryLoadResult(name=pname, solid_names=solid_names, channels=channels, isolants=isolants)


def MSite_Gmsh(
    mname: str, cad: MSite.MSite, gname: str, is2D: bool, verbose: bool = False
) -> GeometryLoadResult:
    """
    Load MSite cad
    """

    print(f"MSite_Gmsh: gname={gname}, cad={cad}")
    # print("MSite_Gmsh Channels:", cad.get_channels())

    solid_names = []
    Channels = cad.get_channels("")
    Isolants = cad.get_isolants("")

    for magnet in cad.magnets:
        _res = Magnet_Gmsh("", magnet, solid_names, is2D, verbose)
        solid_names += _res.solid_names

    print(f"Channels: {Channels}")
    if verbose:
        print(f"MSite_Gmsh: {cad} Done [solids {len(solid_names)}]")
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
    print(f"loadcfg: cfgfile={cfgfile}, gname={gname}, is2D={is2D}")

    solid_names = []
    Channels = None

    try:
        cad = getObject(cfgfile)
    except ValidationError as e:
        # Handle validation errors from python_magnetgeo
        print(f"Validation error: {e}")
    
    print(f"cfgfile: {cad.name} type={type(cad)}", flush=True)
    if verbose:
        print("load cfg {type(cad)}")

    mname = ""
    if type(cad) not in action_dict:
        raise ValueError(
            f"Unsupported geometry type: {type(cad).__name__}. "
            f"Supported types: {', '.join(cls.__name__ for cls in action_dict.keys())}"
        )
    result = action_dict[type(cad)]["run"](mname, cad, gname, is2D, verbose)
    print("results:", result, flush=True)
    
    # Extract channels, handle None case
    channels = result.channels if result.channels is not None else []
    
    print(f"cfg: solid_names={result.solid_names}, Channels={channels}", flush=True)
    return (result.solid_names, channels)
