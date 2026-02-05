#!/usr/bin/env python3
# encoding: UTF-8

"""Enable to define mesh hypothesis (aka params) for Gmsh surfacic and volumic meshes"""
import re

# Load Modules for geometrical Objects
from python_magnetgeo.Insert import Insert
from python_magnetgeo.MSite import MSite
from python_magnetgeo.Bitter import Bitter
from python_magnetgeo.Supra import Supra
from python_magnetgeo.Bitters import Bitters
from python_magnetgeo.Supras import Supras
from python_magnetgeo.Screen import Screen
from python_magnetgeo.Ring import Ring
from python_magnetgeo.Helix import Helix
from python_magnetgeo.base import YAMLObjectBase

from ..logging_config import get_logger

logger = get_logger(__name__)

ObjectType = MSite | Bitters | Supras | Insert | Bitter | Supra | Screen | Helix | Ring


class MeshData(YAMLObjectBase):
    """
    Name:
    Object: geometry (either Insert, Helix, Ring, Lead)

    AlgoSurf
    Algo3D

    Mesh hypothesys in Salome sens are stored by groups: Helices, Rings, Leads, Air, ...
    Each group consist of a list of:
       SurfName, SurfHypoth, SurfColor
       where SurfHypoth: Lc
    for AlgoSurface Hypoths.
    SurfName are taken from Object cfg file (Objects means either Helix, Ring or CurrentLead)

    Opts:
       MakeGroupsOfDomains,
       KeepFiles,
       RemoveLogOnSuccess,
       MaximumMemory,

    ATTENTION:
           The order of definition is also important?

    def Default(...): define Defaults Hypothesys
    def Load(...): load Hypothesys
    def Dump(...): save Hypothesys
    """

    yaml_tag = "MeshData"

    def __init__(
        self,
        name: str,
        algosurf: str = "BLSURF",
        algo3D: str = "BLSURF",
        mesh_dict: dict | None = None,
    ):
        """constructor"""
        self.name = name
        self.algosurf = algosurf
        self.algo3D = algo3D

        # depending of geometry type
        self.mesh_dict = mesh_dict if mesh_dict is not None else {}

    def __repr__(self):
        """representation"""
        return f"{self.__class__.__name__}(name={self.name!r}, algosurf={self.algosurf!r}, algo3D={self.algo3D!r}, mesh_dict={self.mesh_dict!r})"

    def algo2d(self, algosurf):
        logger.warning("Setting surfacic mesh algorithm not implemented yet")

    def algo3d(self, algo):
        logger.warning("Setting volumic mesh algorithm not implemented yet")

    def part_default(self, H: Helix | Bitter | Supra | Screen | Ring, addname: str = ""):
        """
        Define default mesh params for Helix
        """
        logger.debug(f"part_default: name={H.name}, lc={H.get_lc}")
        return H.get_lc()

    def air_default(self, Data: tuple):
        """
        Define default mesh params for Air
        """

        # Retreive main characteristics
        width = (10 * Data[2]) / 5
        physsize = min(width / 50.0, 80)

        # Params for InfR1
        infty = physsize

        # Params for BiotShell
        Biotshell = Data[3] / 50.0

        return [infty, Biotshell]

    def default(
        self,
        mname: str,
        Object: ObjectType,
        Air: tuple,
        workingDir: str = "",
        debug: bool = False,
    ):
        """
        Define default mesh params
        """

        logger.info(f"Creating default MeshData for {Object.name}")
        logger.debug(f"mname={mname}, Air={Air}, workingDir={workingDir}")
        mesh_dict = {}
        hypoths = []

        if isinstance(Object, MSite):
            logger.debug(f"Creating MeshData for MSite {Object.name}")
            for j, mObject in enumerate(Object.magnets):
                prefix = ""
                if mname:
                    prefix = f"{mname}_"
                _tmp = self.default(f"{prefix}{mObject.name}", mObject, (), workingDir)
                mesh_dict.update(_tmp)

        elif isinstance(Object, Bitters):
            logger.debug(f"Creating MeshData for Bitters {Object.name}")
            for mObject in Object.magnets:
                prefix = ""
                if mname:
                    prefix = f"{mname}_"
                _tmp = self.default(f"{prefix}{mObject.name}", mObject, (), workingDir)
                mesh_dict.update(_tmp)

        elif isinstance(Object, Supras):
            logger.debug(f"Creating MeshData for Supras {Object.name}")
            for mObject in Object.magnets:
                prefix = ""
                if mname:
                    prefix = f"{mname}_"
                _tmp = self.default(f"{prefix}{mObject.name}", mObject, (), workingDir)
                mesh_dict.update(_tmp)

        elif isinstance(Object, Screen):
            hypname = ""
            if mname:
                hypname = f"{mname}_"
            logger.debug(f"Creating MeshData for Screen {Object.name}, hypname={hypname}")
            surfhypoth = self.part_default(Object, f"{hypname}{Object.name}_Screen")
            mesh_dict[f"{hypname}{Object.name}_Screen"] = {"lc": hypoths}

        elif isinstance(Object, Bitter):
            hypname = ""
            if mname:
                hypname = f"{mname}"
            logger.debug(f"Creating MeshData for Bitter {Object.name}, hypname={hypname}")
            psnames = Object.get_names(hypname, is2D=True, verbose=debug)
            logger.debug(f"Bitter parts: {psnames}")
            hypoths_names = [re.sub(r"_Slit\d+", "", psname) for psname in psnames]
            hypoths_names = list(set(hypoths_names))
            surfhypoth = self.part_default(Object, hypoths_names[0])
            for psname in hypoths_names:
                logger.debug(f"  Setting mesh params for: {psname}")
                mesh_dict[psname] = {"lc": surfhypoth}

        elif isinstance(Object, Supra):
            logger.debug(f"Creating MeshData for Supra {Object.name}")
            hypname = ""
            if mname:
                hypname = f"{mname}_"
            logger.debug(f"Supra hypname: {hypname}{Object.name}")

            if Object.detail == "None":
                surfhypoth = self.part_default(Object, f"{hypname}{Object.name}")
                mesh_dict[f"{hypname}{Object.name}"] = {"lc": surfhypoth}

            # (_i, _dp, _p, _i_dp, _Mandrin, _Sc, _Du)
            elif Object.detail == "dblpancake":
                hypoths = self.part_default(Object, f"{hypname}{Object.name}_dp")
                for i in range(Object.get_magnet_struct().getNdbpancakes()):
                    mesh_dict[f"{hypname}{Object.name}_dp{i}"] = {"lc": hypoths}
                hypoths = self.part_default(Object, f"{hypname}{Object.name}_i")
                for i in range(Object.get_magnet_struct().getNisolations() - 1):
                    mesh_dict[f"{hypname}{Object.name}_i{i}"] = {"lc": hypoths}

            elif Object.detail == "pancake":
                n_dp = Object.get_magnet_struct().getNdbpancakes()
                hypoths = self.part_default(Object, f"{hypname}{Object.name}_dp_p")
                for i in range(n_dp):
                    mesh_dict[f"{hypname}{Object.name}_dp{i}_p0"] = {"lc": hypoths}
                    mesh_dict[f"{hypname}{Object.name}_dp{i}_p1"] = {"lc": hypoths}
                hypoths = self.part_default(Object, f"{hypname}{Object.name}_dp_i")
                for i in range(n_dp):
                    mesh_dict[f"{hypname}{Object.name}_dp{i}_i"] = {"lc": hypoths}
                hypoths = self.part_default(Object, f"{hypname}{Object.name}_i")
                for i in range(n_dp - 1):
                    mesh_dict[f"{hypname}{Object.name}_i{i}"] = {"lc": hypoths}

            elif Object.detail == "tape":
                n_dp = Object.get_magnet_struct().getNdbpancakes()
                hypoths = self.part_default(Object, f"{hypname}{Object.name}_dp_p_Mandrin")
                for i in range(n_dp):
                    mesh_dict[f"{hypname}{Object.name}_dp{i}_p0_Mandrin"] = {"lc": hypoths}
                    mesh_dict[f"{hypname}{Object.name}_dp{i}_p1_Mandrin"] = {"lc": hypoths}
                hypoths = self.part_default(Object, f"{hypname}{Object.name}_dp_p_t_SC")
                for i in range(n_dp):
                    n_dp_tape = Object.get_magnet_struct().dblpancakes[i].pancake.getN()
                    for j in range(n_dp_tape):
                        mesh_dict[f"{hypname}{Object.name}_dp{i}_p0_t{j}_SC"] = {"lc": hypoths}
                        mesh_dict[f"{hypname}{Object.name}_dp{i}_p1_t{j}_SC"] = {"lc": hypoths}
                hypoths = self.part_default(Object, f"{hypname}{Object.name}_dp_p_t_Duromag")
                for i in range(n_dp):
                    n_dp_tape = Object.get_magnet_struct().dblpancakes[i].pancake.getN()
                    for j in range(n_dp_tape):
                        mesh_dict[f"{hypname}{Object.name}_dp{i}_p0_t{j}_Duromag"] = {"lc": hypoths}
                        mesh_dict[f"{hypname}{Object.name}_dp{i}_p1_t{j}_Duromag"] = {"lc": hypoths}
                hypoths = self.part_default(Object, f"{hypname}{Object.name}_dp_i")
                for i in range(n_dp):
                    mesh_dict[f"{hypname}{Object.name}_dp{i}_i"] = {"lc": hypoths}
                hypoths = self.part_default(Object, f"{hypname}{Object.name}_i")
                for i in range(n_dp - 1):
                    mesh_dict[f"{hypname}{Object.name}_i{i}"] = {"lc": hypoths}
            else:
                raise RuntimeError(
                    f"MeshData: Unknow detail level ({Object.detail}) for Supra {Object.name}"
                )

        elif isinstance(Object, Insert):
            hypname = ""
            if mname:
                hypname = f"{mname}"
            logger.debug(f"Creating MeshData for Insert {Object.name}, hypname={hypname}")
            psnames = Object.get_names(hypname, is2D=True, verbose=debug)
            logger.debug(f"Insert parts: {psnames}")
            num = 0
            for i, H in enumerate(Object.helices):
                logger.debug(f"MeshData for Helix: {H.name}, nturns={len(H.modelaxi.turns)}")

                psname = re.sub(r"_Cu\d+", "", psnames[num])
                for n in range(len(H.modelaxi.turns) + 2):
                    mesh_dict[psnames[num]] = {"lc": self.part_default(H, psname)}
                    num += 1

            for i, R in enumerate(Object.rings):
                mesh_dict[psnames[i + num]] = {"lc": self.part_default(R, psnames[i + num])}
                num += 1

        if Air:
            logger.debug("Creating MeshData for Air domain")
            [Air_, Biot_] = self.air_default(Air)
            mesh_dict["Air"] = {"lc": Air_}
            mesh_dict["Biot"] = {"lc": Biot_}
        else:
            logger.debug("No Air domain defined")

        self.mesh_dict = mesh_dict
        return mesh_dict

    @classmethod
    def from_dict(cls, values):
        name = values.get("name", "")
        mesh_dict = values.get("mesh_dict", {})
        algosurf = values.get("algosurf", "BLSURF")
        algo3D = values.get("algo3D", "BLSURF")
        return cls(
            name,
            algosurf,
            algo3D,
            mesh_dict,
        )

    def dump(self, filename: str | None = None):
        """
        Save mesh_dict to YAML file using proper YAML serialization with tags
        """
        from pathlib import Path
        import yaml

        if filename is None:
            filename = f"{self.name}.yaml"

        path = Path(filename)
        if path.exists():
            raise FileExistsError(f"{filename} already exists")

        # Use yaml.dump(self) to include the YAML tag for proper deserialization
        path.write_text(yaml.dump(self, default_flow_style=False, sort_keys=False))

        logger.info(f"MeshData saved: {filename}")


def createMeshData(prefix: str, Object, filename: str, AirData: tuple, algo2d: str, algo3d: str):
    import os
    from python_magnetgeo.utils import ObjectLoadError

    logger.info(f"Loading/creating MeshData: {filename}")
    logger.debug(f"Working directory: {os.getcwd()}")

    try:
        _MeshData = MeshData.from_yaml(f"{filename}.yaml")
        logger.info(f"Loaded existing MeshData from {filename}.yaml")
    # Catch all I/O and parsing errors raised by the library
    except ObjectLoadError as e:
        # Determine the specific cause based on the error message
        is_file_missing = "YAML file not found" in str(e)

        if is_file_missing:
            logger.info(f"MeshData file not found, creating default: {filename}.yaml")
        else:
            # Catches the converted YAMLError (Failed to parse YAML)
            raise RuntimeError(f"*** Failed to parse YAML in {filename}: {e}")

        logger.debug("Generating default meshdata")
        _MeshData = MeshData(filename)
        _MeshData.default(prefix, Object, AirData)
        _MeshData.dump()
    except Exception as e:
        raise RuntimeError(f"Failed to load MeshData from {filename}: {e}")

    return _MeshData
