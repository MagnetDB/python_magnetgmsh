#!/usr/bin/env python3
# encoding: UTF-8

"""Enable to define mesh hypothesis (aka params) for Gmsh surfacic and volumic meshes"""
import os
import re
import yaml

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
        mesh_dict: dict = {},
    ):
        """constructor"""
        self.name = name
        self.algosurf = algosurf
        self.algo3D = algo3D

        # depending of geometry type
        self.mesh_dict = mesh_dict

    def __repr__(self):
        """representation"""
        return "%s(name=%r, algosurf=%r, algo3D=%r, surfhypoths=%r, mesh_dict=%r)" % (
            self.__class__.__name__,
            self.name,
            self.algosurf,
            self.surfhypoths,
            self.mesh_dict,
        )

    def algo2d(self, algosurf):
        print("set surfacic mesh algo - not implemented yet")

    def algo3d(self, algo):
        print("set volumic mesh algo - not implemented yet")

    def part_default(
        self, H: Helix | Bitter | Supra | Screen | Ring, addname: str = ""
    ):
        """
        Define default mesh params for Helix
        """
        print(f"part_default: name={H.name}, lc={H.get_lc}")
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

        print(
            f"{__name__}: creating default MeshData,  mname={mname}, Object.name={Object.name}, Air={Air}, wd={workingDir}"
        )
        mesh_dict = {}
        surfhypoths = []

        if isinstance(Object, MSite):
            print(f"Creating MeshData for MSite {Object.name}, mname={mname}")
            for j, mObject in enumerate(Object.magnets):
                prefix = ""
                if mname:
                    prefix = f"{mname}_"
                _tmp = self.default(
                    f"{prefix}{mObject.name}", mObject, (), workingDir
                )
                mesh_dict.update(_tmp)

        elif isinstance(Object, Bitters):
            print(f"Creating MeshData for Bitters {Object.name}, (mname={mname})")
            for mObject in Object.magnets:
                prefix = ""
                if mname:
                    prefix = f"{mname}_"
                _tmp = self.default(
                    f"{prefix}{mObject.name}", mObject, (), workingDir
                )
                mesh_dict.update(_tmp)

        elif isinstance(Object, Supras):
            print(f"Creating MeshData for Supras {Object.name}, mname={mname}")
            for mObject in Object.magnets:
                prefix = ""
                if mname:
                    prefix = f"{mname}_"
                _tmp = self.default(
                    f"{prefix}{mObject.name}", mObject, (), workingDir
                )
                mesh_dict.update(_tmp)

        elif isinstance(Object, Screen):
            hypname = ""
            if mname:
                hypname = f"{mname}_"
            print(
                f"Creating MeshData for Screen {Object.name}, mname={mname}, hypname={hypname}"
            )
            surfhypoth =self.part_default(Object, f"{hypname}{Object.name}_Screen")
            mesh_dict[f"{hypname}{Object.name}_Screen"] = {"lc": surfhypoths}

        elif isinstance(Object, Bitter):
            hypname = ""
            if mname:
                hypname = f"{mname}"
            print(
                f"Creating MeshData for Bitter {Object.name}, mname={mname}, hypname={hypname}"
            )
            psnames = Object.get_names(hypname, is2D=True, verbose=debug)
            print(f"psnames={psnames}")
            surfhypoths_names = [re.sub(r"_Slit\d+", "", psname) for psname in psnames]
            surfhypoths_names = list(set(surfhypoths_names))
            surfhypoth = self.part_default(Object, surfhypoths_names[0])
            for psname in surfhypoths_names:
                print(f"\tpsname={psname}")
                mesh_dict[psname] = {"lc": surfhypoth}

        elif isinstance(Object, Supra):
            print(f"Creating MeshData for Supra {Object.name}, mname={mname}")
            hypname = ""
            if mname:
                hypname = f"{mname}_"
            print(f"hypname/Object.name={hypname}{Object.name}")

            if Object.detail == "None":
                surfhypoth = self.part_default(Object, f"{hypname}{Object.name}")
                mesh_dict[f"{hypname}{Object.name}"] = {"lc": surfhypoth}

            # (_i, _dp, _p, _i_dp, _Mandrin, _Sc, _Du)
            elif Object.detail == "dblpancake":
                surfhypoths = self.part_default(Object, f"{hypname}{Object.name}_dp")
                for i in range(Object.get_magnet_struct().getN()):
                    mesh_dict[f"{hypname}{Object.name}_dp{i}"] = {"lc": surfhypoths}
                surfhypoths = self.part_default(Object, f"{hypname}{Object.name}_i")
                for i in range(Object.get_magnet_struct().getN() - 1):
                    mesh_dict[f"{hypname}{Object.name}_i{i}"] = {"lc": surfhypoths}

            elif Object.detail == "pancake":
                n_dp = Object.get_magnet_struct().getN()
                surfhypoths = self.part_default(Object, f"{hypname}{Object.name}_dp_p")
                for i in range(n_dp):
                    mesh_dict[f"{hypname}{Object.name}_dp{i}_p0"] = {"lc": surfhypoths}
                    mesh_dict[f"{hypname}{Object.name}_dp{i}_p1"] = {"lc": surfhypoths}
                surfhypoths.append(
                    self.part_default(Object, f"{hypname}{Object.name}_dp_i")
                )
                for i in range(n_dp):
                    mesh_dict[f"{hypname}{Object.name}_dp{i}_i"] = {"lc": surfhypoths}
                surfhypoths =self.part_default(Object, f"{hypname}{Object.name}_i")
                for i in range(n_dp - 1):
                    mesh_dict[f"{hypname}{Object.name}_i{i}"] = {"lc": surfhypoths}

            elif Object.detail == "tape":
                n_dp = Object.get_magnet_struct().getN()
                surfhypoths = self.part_default(Object, f"{hypname}{Object.name}_dp_p_Mandrin")
                for i in range(n_dp):
                    mesh_dict[f"{hypname}{Object.name}_dp{i}_p0_Mandrin"] =  {"lc": surfhypoths}
                    mesh_dict[f"{hypname}{Object.name}_dp{i}_p1_Mandrin"] =  {"lc": surfhypoths}
                surfhypoths = self.part_default(Object, f"{hypname}{Object.name}_dp_p_t_SC")
                for i in range(n_dp):
                    n_dp_tape = Object.get_magnet_struct().dblpancakes[i].pancake.getN()
                    for j in range(n_dp_tape):
                        mesh_dict[f"{hypname}{Object.name}_dp{i}_p0_t{j}_SC"] =  {"lc": surfhypoths}
                        mesh_dict[f"{hypname}{Object.name}_dp{i}_p1_t{j}_SC"] =  {"lc": surfhypoths}
                surfhypoths =self.part_default(Object, f"{hypname}{Object.name}_dp_p_t_Duromag")
                for i in range(n_dp):
                    n_dp_tape = Object.get_magnet_struct().dblpancakes[i].pancake.getN()
                    for j in range(n_dp_tape):
                        mesh_dict[f"{hypname}{Object.name}_dp{i}_p0_t{j}_Duromag"] =  {"lc": surfhypoths}
                        mesh_dict[f"{hypname}{Object.name}_dp{i}_p1_t{j}_Duromag"] =  {"lc": surfhypoths}
                surfhypoths= self.part_default(Object, f"{hypname}{Object.name}_dp_i")
                for i in range(n_dp):
                    mesh_dict[f"{hypname}{Object.name}_dp{i}_i"] =  {"lc": surfhypoths}
                surfhypoths = self.part_default(Object, f"{hypname}{Object.name}_i")
                for i in range(n_dp - 1):
                    mesh_dict[f"{hypname}{Object.name}_i{i}"] =  {"lc": surfhypoths}
            else:
                raise RuntimeError(
                    f"MeshData: Unknow detail level ({Object.detail}) for Supra {Object.name}"
                )

        elif isinstance(Object, Insert):
            hypname = ""
            if mname:
                hypname = f"{mname}"
            print(
                f"Creating MeshData for Insert {Object.name}, mname={mname}, hypname={hypname}"
            )
            psnames = Object.get_names(hypname, is2D=True, verbose=debug)
            print(
                f"Creating MeshData for Insert {Object.name}, mname={mname}, psnames={psnames}"
            )
            num = 0
            for i, H in enumerate(Object.helices):
                print(
                    f"MeshData for H: {H.name}, nturns={len(H.modelaxi.turns)}, psname[{num}]={psnames[num]}"
                )

                psname = re.sub(r"_Cu\d+", "", psnames[num])
                for n in range(len(H.modelaxi.turns) + 2):
                    mesh_dict[psnames[num]] = {"lc": self.part_default(H, psname)}
                    num += 1

            for i, R in enumerate(Object.rings):
                mesh_dict[psnames[i + num]] = {"lc": self.part_default(R, psnames[i + num])}
                num += 1

        if Air:
            print("MeshData for Air")
            [Air_, Biot_] = self.air_default(Air)
            mesh_dict["Air"] = {"lc": Air_}
            mesh_dict["Biot"] = {"lc": Biot_}
            # print "Creating MeshData for Air... done"
        else:
            print("No Air defined")
        if debug:
            print("---------------------------------------------------------")
            print("surfhypoths: ", len(surfhypoths), surfhypoths)
            for i, hypoth in enumerate(surfhypoths):
                print(f"hypoth[{i}]: {hypoth}")
            print("---------------------------------------------------------")

        self.mesh_dict = mesh_dict
        return mesh_dict

    @classmethod
    def from_dict(cls, values):
        name = values["name"]
        mesh_dict = values["mesh_dict"]
        algosurf = values["algosurf"]
        algo3D = values["algo3D"]
        return cls(
            name,
            algosurf,
            algo3D,
            mesh_dict,
        )


def createMeshData(prefix: str, Object, filename: str, AirData: tuple, algo2d: str, algo3d: str):
    from yaml import YAMLError

    try:
        _MeshData = MeshData.from_yaml(f"{filename}.yaml", algo2d, algo3d)
    except FileNotFoundError:
        print("*** failed to load meshdata")
        print("*** trying to generate default gmshdata")
        _MeshData = MeshData(filename)
        _MeshData.default(prefix, Object, AirData)
        _MeshData.dump()
    except YAMLError as e:
        raise RuntimeError(f"Failed to parse YAML in {filename}: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to load MeshData from {filename}: {e}")

    return _MeshData
