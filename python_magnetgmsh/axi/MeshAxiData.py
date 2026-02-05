#!/usr/bin/env python3
# encoding: UTF-8

"""Enable to define mesh hypothesis (aka params) for Gmsh surfacic and volumic meshes"""
import os
import re
import yaml
import logging
from pathlib import Path

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

from python_magnetgeo.enums import DetailLevel
from python_magnetgeo.base import YAMLObjectBase

logger = logging.getLogger(__name__)

ObjectType = MSite | Bitters | Supras | Insert | Bitter | Supra | Screen | Helix | Ring


class MeshAxiData(YAMLObjectBase):
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

    yaml_tag = "MeshAxiData"

    def __init__(
        self,
        name: str,
        algosurf: str = "BLSURF",
        mesh_dict: dict | None = None,
    ):
        """constructor"""
        self.name = name
        self.algosurf = algosurf

        # depending of geometry type
        self.mesh_dict = mesh_dict if mesh_dict is not None else {}

    def __repr__(self):
        """representation"""
        return f"{self.__class__.__name__}(name={self.name!r}, algosurf={self.algosurf!r}, mesh_dict={self.mesh_dict!r})"

    def algo2d(self, algosurf):
        logger.warning("Setting surfacic mesh algorithm not implemented yet")

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

        logger.info(f"Creating default MeshAxiData for {Object.name}")
        logger.debug(f"mname={mname}, Air={Air}, workingDir={workingDir}")
        mesh_dict = {}

        if isinstance(Object, MSite):
            logger.debug(f"Creating MeshAxiData for MSite {Object.name}")
            for magnet in Object.magnets:
                _tmp = self.default(magnet.name, magnet, (), workingDir)
                mesh_dict.update(_tmp)
        elif isinstance(Object, Bitters):
            logger.debug(f"Creating MeshAxiData for Bitters {Object.name}")
            for magnet in Object.magnets:
                _tmp = self.default(magnet.name, magnet, (), workingDir)
                mesh_dict.update(_tmp)
        elif isinstance(Object, Supras):
            logger.debug(f"Creating MeshAxiData for Supras {Object.name}")
            for magnet in Object.magnets:
                _tmp = self.default(magnet.name, magnet, (), workingDir)
                mesh_dict.update(_tmp)
        elif isinstance(Object, Screen):
            hypname = ""
            if mname:
                hypname = f"{mname}_"
            logger.debug(f"Creating MeshAxiData for Screen {Object.name}, hypname={hypname}")
            hypoths = self.part_default(Object, f"{hypname}{Object.name}_Screen")
            mesh_dict[f"{hypname}{Object.name}_Screen"] = {"lc": hypoths}

        elif isinstance(Object, Bitter):
            hypname = ""
            if mname:
                hypname = f"{mname}"
            logger.debug(f"Creating MeshAxiData for Bitter {Object.name}, hypname={hypname}")
            psnames = Object.get_names(hypname, is2D=True, verbose=debug)
            logger.debug(f"Bitter parts: {psnames}")
            hypoths_names = [re.sub(r"_Slit\d+", "", psname) for psname in psnames]
            hypoths_names = list(set(hypoths_names))
            hypoths = self.part_default(Object, hypoths_names[0])
            for psname in hypoths_names:
                logger.debug(f"  Setting mesh params for: {psname}")
                mesh_dict[psname] = {"lc": hypoths}

        elif isinstance(Object, Supra):
            logger.debug(f"Creating MeshAxiData for Supra {Object.name}")
            hypname = ""
            if mname:
                hypname = f"{mname}_"
            logger.debug(f"Supra hypname: {hypname}{Object.name}")

            if Object.detail == DetailLevel.NONE:
                hypoths = self.part_default(Object, f"{hypname}{Object.name}")
                mesh_dict[f"{hypname}{Object.name}"] = {"lc": hypoths}

            # (_i, _dp, _p, _i_dp, _Mandrin, _Sc, _Du)
            elif Object.detail == DetailLevel.DBLPANCAKE:
                hypoths = self.part_default(Object, f"{hypname}{Object.name}_dp")
                n_dp = len(Object.get_magnet_struct().dblpancakes)
                for i in range(n_dp):
                    mesh_dict[f"{hypname}{Object.name}_dp{i}"] = {"lc": hypoths}
                hypoths = self.part_default(Object, f"{hypname}{Object.name}_i")
                for i in range(n_dp - 1):
                    mesh_dict[f"{hypname}{Object.name}_i{i}"] = {"lc": hypoths}

            elif Object.detail == DetailLevel.PANCAKE:
                n_dp = len(Object.get_magnet_struct().dblpancakes)
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

            elif Object.detail == DetailLevel.TAPE:
                n_dp = len(Object.get_magnet_struct().dblpancakes)
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
                    f"MeshAxiData: Unknow detail level ({Object.detail}) for Supra {Object.name}"
                )

        elif isinstance(Object, Insert):
            logger.debug(f"Creating MeshAxiData for Insert {Object.name}")
            psnames = Object.get_names(mname, is2D=True, verbose=debug)
            logger.debug(f"Insert parts: {psnames}")
            num = 0
            for i, H in enumerate(Object.helices):
                logger.debug(f"MeshAxiData for Helix: {H.name}, nturns={len(H.modelaxi.turns)}")

                psname = re.sub(r"_Cu\d+", "", psnames[num])
                hypoths = self.part_default(H, psname)
                for n in range(len(H.modelaxi.turns) + 2):
                    mesh_dict[psnames[num]] = {"lc": hypoths}
                    num += 1

            for i, R in enumerate(Object.rings):
                logger.debug(f"MeshAxiData for Ring: {R.name}")
                hypoths = self.part_default(R, psnames[i + num])
                mesh_dict[psnames[i + num]] = {"lc": hypoths}

        if Air:
            logger.debug("Creating MeshAxiData for Air domain")
            [Air_, Biot_] = self.air_default(Air)
            mesh_dict["Air"] = {"lc": Air_}
            mesh_dict["Biot"] = {"lc": Biot_}
        else:
            logger.debug("No Air domain defined")

        self.mesh_dict = mesh_dict
        return mesh_dict

    @classmethod
    def from_dict(cls, values: dict, debug: bool = False):
        name = values.get("name", "")
        algosurf = values.get("algosurf", "BLSURF")
        mesh_dict = values.get("mesh_dict", {})
        return cls(
            name,
            algosurf,
            mesh_dict,
        )

    def dump(self, filename: str | None = None):
        """
        Save mesh_dict to YAML file using proper YAML serialization with tags
        """
        if filename is None:
            filename = f"{self.name}.yaml"

        path = Path(filename)
        if path.exists():
            raise FileExistsError(f"{filename} already exists")
        
        # Use yaml.dump(self) to include the YAML tag for proper deserialization
        path.write_text(yaml.dump(self, default_flow_style=False, sort_keys=False))

        logger.info(f"MeshAxiData saved: {filename}")


# add a wd args?
def createMeshAxiData(prefix: str, Object, AirData: tuple, filename: str, algo2d: str):
    from python_magnetgeo.utils import ObjectLoadError

    logger.info(f"Loading/creating MeshAxiData: {filename}")
    logger.debug(f"Working directory: {os.getcwd()}")

    try:
        _MeshData = MeshAxiData.from_yaml(f"{filename}.yaml")
        logger.info(f"Loaded existing MeshAxiData from {filename}.yaml")

    # Catch all I/O and parsing errors raised by the library
    except ObjectLoadError as e:
        # Determine the specific cause based on the error message
        is_file_missing = "YAML file not found" in str(e)

        if is_file_missing:
            logger.info(f"MeshAxiData file not found, creating default: {filename}.yaml")
        else:
            # Catches the converted YAMLError (Failed to parse YAML)
            raise RuntimeError(f"*** Failed to parse YAML in {filename}: {e}")

        logger.debug("Generating default gmshaxidata")

        _MeshData = MeshAxiData(filename, algo2d)
        logger.debug("MeshAxiData instance created")

        _MeshData.default(prefix, Object, AirData)
        logger.debug("MeshAxiData defaults set")
        _MeshData.dump()
        logger.debug("MeshAxiData saved")

    except Exception as e:
        # Catch any *other* unexpected, non-loading errors
        raise RuntimeError(f"Failed to load MeshAxiData from {filename}: {e}")
    # add finaly section ??

    return _MeshData
