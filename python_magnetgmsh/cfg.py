import yaml

from python_magnetgeo.Helix import Helix
from python_magnetgeo.Insert import Insert
from python_magnetgeo.Bitter import Bitter
from python_magnetgeo.Supra import Supra
from python_magnetgeo.Bitters import Bitters
from python_magnetgeo.Supras import Supras
from python_magnetgeo.MSite import MSite
from python_magnetgeo.utils import getObject

def Supra_Gmsh(
    mname: str, cad: Supra, gname: str, is2D: bool, verbose: bool = False
) -> list[str]:
    """Load Supra cad"""
    print(f"Supra_Gmsh: mname={mname}, cad={cad.name}, gname={gname}")
    prefix = ""
    if mname:
        prefix = mname
    return cad.get_names(prefix, is2D, verbose)


def Bitter_Gmsh(
    mname: str, cad: Bitter, gname: str, is2D: bool, verbose: bool = False
) -> list[str]:
    """Load Bitter cad"""
    print(f"Bitter_Gmsh: mname={mname}, cad={cad.name}, gname={gname}")
    prefix = ""
    if mname:
        prefix = mname
    return cad.get_names(prefix, is2D, verbose)


def Helix_Gmsh(
    mname: str, cad: Helix, gname: str, is2D: bool, verbose: bool = False
) -> list[str]:
    """Load Helix cad"""
    print(f"Helix_Gmsh: mname={mname}, cad={cad.name}, gname={gname}")
    prefix = ""
    if mname:
        prefix = mname
    return cad.get_names(prefix, is2D, verbose)


def Bitters_Gmsh(
    mname: str, cad: Bitters, gname: str, is2D: bool, verbose: bool = False
) -> list[str]:
    """Load Bitters"""
    print(f"Bitters_Gmsh: mname={mname}, gname={gname}")
    solid_names = []
    prefix = ""
    if mname:
        prefix = f"{mname}"

    for magnet in cad.magnets:
        _names = Bitter_Gmsh(f"{prefix}{magnet.name}", magnet, gname, is2D, verbose)
        print(f"Bitter_Gmsh: _names={_names}")
        solid_names += _names
    return solid_names


def Supras_Gmsh(
    mname: str, cad: Supras, gname: str, is2D: bool, verbose: bool = False
) -> list[str]:
    """Load Supras"""
    print(f"Supras_Gmsh: mname={mname}, gname={gname}")
    solid_names = []
    prefix = ""
    if mname:
        prefix = f"{mname}"

    for magnet in cad.magnets:
        _names = Supra_Gmsh(f"{prefix}{magnet.name}", magnet, gname, is2D, verbose)
        solid_names += _names
    return solid_names


def Insert_Gmsh(
    mname: str, cad: Insert, gname: str, is2D: bool, verbose: bool = False
) -> list[str]:
    """Load Insert"""
    print(f"Insert_Gmsh: mname={mname}, cad={cad.name}, gname={gname}")
    return cad.get_names(mname, is2D, verbose)


action_dict = {
    Bitter: {"run": Bitter_Gmsh, "msg": "Bitter"},
    Bitters: {"run": Bitters_Gmsh, "msg": "Bitters"},
    Supra: {"run": Supra_Gmsh, "msg": "Supra"},
    Supras: {"run": Supras_Gmsh, "msg": "Supras"},
    Helix: {"run": Helix_Gmsh, "msg": "Helix"},
    Insert: {"run": Insert_Gmsh, "msg": "Insert"},
}

from python_magnetgeo.utils import getObject

def Magnet_Gmsh(
    mname: str, cad: str, gname: str, is2D: bool, verbose: bool = False
) -> tuple[str, list[str]]:
    """Load Magnet cad"""
    print(f"Magnet_Gmsh: mname={mname}, cad={cad}, gname={gname}")
    solid_names = []

    cfgfile = f"{cad}.yaml"
    pcad = getObject(cfgfile)
    pname = pcad.name

    # print('pcad: {pcad} type={type(pcad)}')
    _names = action_dict[type(pcad)]["run"](mname, pcad, pname, is2D, verbose)
    solid_names += _names
    if verbose:
        print(f"Magnet_Gmsh: {cad} Done [solids {len(solid_names)}]")
    return (pname, solid_names)


def MSite_Gmsh(
    mname: str, cad: MSite, gname: str, is2D: bool, verbose: bool = False
) -> tuple[list[str], dict, dict]:
    """
    Load MSite cad
    """

    print(f"MSite_Gmsh: gname={gname}, cad={cad}")
    # print("MSite_Gmsh Channels:", cad.get_channels())

    solid_names = []
    NHelices = []
    Channels = cad.get_channels("")
    Isolants = cad.get_isolants("")

    for magnet in cad.magnets:
        (pname, _names) = Magnet_Gmsh("", magnet, solid_names, is2D, verbose)
        solid_names += _names

    print(f"Channels: {Channels}")
    if verbose:
        print(f"MSite_Gmsh: {cad} Done [solids {len(solid_names)}]")
    return (solid_names, Channels, Isolants)


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
        if not isinstance(cad, MSite):
            raise Exception(f"unsupported type of cad {type(cad)}")
        else:
            (solid_names, Channels, Isolants) = MSite_Gmsh(
                mname, cad, gname, is2D, verbose
            )
    else:
        solid_names = action_dict[type(cad)]["run"](
            mname, cad, gname, is2D, verbose
        )
        Channels = cad.get_channels(mname)

        # quick hack for Biiter
        if isinstance(cad, Bitter):
            Channels.append("Tierod")

    print(f"cfg: solid_names={solid_names}, Channels={Channels}")
    return (solid_names, Channels)
