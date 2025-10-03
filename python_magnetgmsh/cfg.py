import yaml

from python_magnetgeo.Helix import Helix
from python_magnetgeo.Insert import Insert
from python_magnetgeo.Bitter import Bitter
from python_magnetgeo.Supra import Supra
from python_magnetgeo.Bitters import Bitters
from python_magnetgeo.Supras import Supras
from python_magnetgeo.MSite import MSite
from python_magnetgeo.utils import getObject

from typing import NamedTuple

class GeometryLoadResult(NamedTuple):
    """Result from loading geometry configuration."""
    name: str| None = None
    solid_names: list[str] = []
    channels: dict | list | None = None
    isolants: dict | None = None

def Supra_Gmsh(
    mname: str, cad: Supra, gname: str, is2D: bool, verbose: bool = False
) -> GeometryLoadResult:
    """Load Supra cad"""
    print(f"Supra_Gmsh: mname={mname}, cad={cad.name}, gname={gname}")
    prefix = ""
    if mname:
        prefix = mname
    return GeometryLoadResult(solid_names=cad.get_names(prefix, is2D, verbose))


def Bitter_Gmsh(
    mname: str, cad: Bitter, gname: str, is2D: bool, verbose: bool = False
) -> GeometryLoadResult:
    """Load Bitter cad"""
    print(f"Bitter_Gmsh: mname={mname}, cad={cad.name}, gname={gname}")
    prefix = ""
    if mname:
        prefix = mname

    solid_names=cad.get_names(prefix, is2D, verbose)
    
    
    # why??
    channels = []
    if cad.has_tierod:
        channels.append("Tierod")

    return GeometryLoadResult(solid_names=solid_names, channels=channels)


def Helix_Gmsh(
    mname: str, cad: Helix, gname: str, is2D: bool, verbose: bool = False
) -> GeometryLoadResult:
    """Load Helix cad"""
    print(f"Helix_Gmsh: mname={mname}, cad={cad.name}, gname={gname}")
    prefix = ""
    if mname:
        prefix = mname
    return GeometryLoadResult(solid_names=cad.get_names(prefix, is2D, verbose))

def Insert_Gmsh(
    mname: str, cad: Insert, gname: str, is2D: bool, verbose: bool = False
) -> GeometryLoadResult:
    """Load Insert"""
    print(f"Insert_Gmsh: mname={mname}, cad={cad.name}, gname={gname}")
    return GeometryLoadResult(cad.get_names(mname, is2D, verbose))

def Bitters_Gmsh(
    mname: str, cad: Bitters, gname: str, is2D: bool, verbose: bool = False
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
    return GeometryLoadResult(solid_names=solid_names)


def Supras_Gmsh(
    mname: str, cad: Supras, gname: str, is2D: bool, verbose: bool = False
) -> GeometryLoadResult:
    """Load Supras"""
    print(f"Supras_Gmsh: mname={mname}, gname={gname}")
    solid_names = []
    prefix = ""
    if mname:
        prefix = f"{mname}"

    for magnet in cad.magnets:
        _res = Supra_Gmsh(f"{prefix}{magnet.name}", magnet, gname, is2D, verbose)
        solid_names += _res.solid_names
    return GeometryLoadResult(solid_names)


from python_magnetgeo.utils import getObject

def Magnet_Gmsh(
    mname: str, cad: str|Bitters|Supras|Insert, gname: str, is2D: bool, verbose: bool = False
) -> GeometryLoadResult:
    """Load Magnet cad"""
    if isinstance(cad, str):
        pcad = getObject(f"{cad}.yaml")
        
    pname = pcad.name
    print(f"Magnet_Gmsh: mname={mname}, cad={pname}, gname={gname}")
    solid_names = []

    # print('pcad: {pcad} type={type(pcad)}')
    _res = action_dict[type(pcad)]["run"](mname, pcad, pname, is2D, verbose)
    solid_names += _res.solid_names
    if verbose:
        print(f"Magnet_Gmsh: {cad} Done [solids {len(solid_names)}]")
    return GeometryLoadResult(name=pname, solid_names=solid_names)


def MSite_Gmsh(
    mname: str, cad: MSite, gname: str, is2D: bool, verbose: bool = False
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
    Bitter: {"run": Bitter_Gmsh, "msg": "Bitter"},
    Bitters: {"run": Bitters_Gmsh, "msg": "Bitters"},
    Supra: {"run": Supra_Gmsh, "msg": "Supra"},
    Supras: {"run": Supras_Gmsh, "msg": "Supras"},
    Helix: {"run": Helix_Gmsh, "msg": "Helix"},
    Insert: {"run": Insert_Gmsh, "msg": "Insert"},
    MSite: {"run": MSite_Gmsh, "msg": "MSite"},
}

def loadcfg(
    cfgfile: str, gname: str, is2D: bool, verbose: bool = False
) -> tuple[list[str], dict | list]:
    print(f"loadcfg: cfgfile={cfgfile}, gname={gname}, is2D={is2D}")

    solid_names = []
    Channels = None

    cad = getObject(cfgfile)
    print(f"cfgfile: {cad.name} type={type(cad)}")
    if verbose:
        print("load cfg {type(cad)}")

    mname = ""
    if type(cad) not in action_dict:
        raise ValueError(
            f"Unsupported geometry type: {type(cad).__name__}. "
            f"Supported types: {', '.join(cls.__name__ for cls in action_dict.keys())}"
        )
    result = action_dict[type(cad)]["run"](mname, cad, gname, is2D, verbose)
    
    # Extract channels, handle None case
    channels = result.channels if result.channels is not None else []
    
    print(f"cfg: solid_names={result.solid_names}, Channels={channels}")
    return (result.solid_names, channels)
