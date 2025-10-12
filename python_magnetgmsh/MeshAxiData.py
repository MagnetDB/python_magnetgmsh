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

from python_magnetgeo.enums import DetailLevel
from python_magnetgeo.base import YAMLObjectBase

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
        mesh_dict: dict = {},
    ):
        """constructor"""
        self.name = name
        self.algosurf = algosurf

        # depending of geometry type
        self.mesh_dict = mesh_dict

    def __repr__(self):
        """representation"""
        return "%s(name=%r, algosurf=%r, mesh_dict=%r)" % (
            self.__class__.__name__,
            self.name,
            self.algosurf,
            self.mesh_dict,
        )

    def algo2d(self, algosurf):
        print("set surfacic mesh algo - not implemented yet")

    def part_default(self, H: Helix | Bitter | Supra | Screen | Ring, addname: str = ""):
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
            f"{__name__}: creating default MeshAxiData,  mname={mname}, Object.name={Object.name}, Air={Air}, wd={workingDir}"
        )
        mesh_dict = {}

        if isinstance(Object, MSite):
            print(f"Creating MeshAxiData for MSite {Object.name}, mname={mname}")
            for magnet in Object.magnets:
                _tmp = self.default(magnet.name, magnet, (), workingDir)
                mesh_dict.update(_tmp)
        elif isinstance(Object, Bitters):
            print(f"Creating MeshAxiData for Bitters {Object.name}, (mname={mname})")
            for magnet in Object.magnets:
                _tmp = self.default(magnet.name, magnet, (), workingDir)
                mesh_dict.update(_tmp)
        elif isinstance(Object, Supras):
            print(f"Creating MeshAxiData for Supras {Object.name}, mname={mname}")
            for magnet in Object.magnets:
                _tmp = self.default(magnet.name, magnet, (), workingDir)
                mesh_dict.update(_tmp)
        elif isinstance(Object, Screen):
            hypname = ""
            if mname:
                hypname = f"{mname}_"
            print(
                f"Creating MeshAxiData for Screen {Object.name}, mname={mname}, hypname={hypname}"
            )
            hypoths = self.part_default(Object, f"{hypname}{Object.name}_Screen")
            mesh_dict[f"{hypname}{Object.name}_Screen"] = {"lc": hypoths}

        elif isinstance(Object, Bitter):
            hypname = ""
            if mname:
                hypname = f"{mname}"
            print(
                f"Creating MeshAxiData for Bitter {Object.name}, mname={mname}, hypname={hypname}"
            )
            psnames = Object.get_names(hypname, is2D=True, verbose=debug)
            print(f"psnames={psnames}")
            hypoths_names = [re.sub(r"_Slit\d+", "", psname) for psname in psnames]
            hypoths_names = list(set(hypoths_names))
            hypoths = self.part_default(Object, hypoths_names[0])
            for psname in hypoths_names:
                print(f"\tpsname={psname}")
                mesh_dict[psname] = {"lc": hypoths}

        elif isinstance(Object, Supra):
            print(f"Creating MeshAxiData for Supra {Object.name}, mname={mname}")
            hypname = ""
            if mname:
                hypname = f"{mname}_"
            print(f"hypname/Object.name={hypname}{Object.name}")

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
                    mesh_dict[f"{hypname}{Object.name}_i{i}"] =  {"lc": hypoths}

            else:
                raise RuntimeError(
                    f"MeshAxiData: Unknow detail level ({Object.detail}) for Supra {Object.name}"
                )

        elif isinstance(Object, Insert):
            print(f"Creating MeshAxiData for Insert {Object.name}, mname={mname}")
            psnames = Object.get_names(mname, is2D=True, verbose=debug)
            print(f"psnames={psnames}")
            num = 0
            for i, H in enumerate(Object.helices):
                print(
                    f"MeshAxiData for H: {H.name}, nturns={len(H.modelaxi.turns)}, psname[{num}]={psnames[num]}"
                )

                psname = re.sub(r"_Cu\d+", "", psnames[num])
                hypoths = self.part_default(H, psname)
                for n in range(len(H.modelaxi.turns) + 2):
                    mesh_dict[psnames[num]] = {"lc": hypoths}
                    num += 1

            for i, R in enumerate(Object.rings):
                print(f"MeshAxiData for R: {R.name}")
                hypoths = self.part_default(R, psnames[i + num])
                mesh_dict[psnames[i + num]] = {"lc": hypoths}

        if Air:
            print("MeshAxiData for Air")
            [Air_, Biot_] = self.air_default(Air)
            mesh_dict["Air"] = {"lc": Air_}
            mesh_dict["Biot"] = {"lc": Biot_}
            # print "Creating MeshAxiData for Air... done"
        else:
            print("No Air defined")

        self.mesh_dict = mesh_dict
        return mesh_dict


    @classmethod
    def from_dict(cls, values: dict, debug: bool = False):
        name = values["name"]
        algosurf = values["algosurf"]
        mesh_dict = values["mesh_dict"]
        return cls(
            name,
            algosurf,
            mesh_dict,
        )

# add a wd args?
def createMeshAxiData(prefix: str, Object, AirData: tuple, filename: str, algo2d: str):
    import os
    from python_magnetgeo.utils import ObjectLoadError 

    print(f"createMeshAxiData: cwd: {os.getcwd()}, filename={filename}", flush=True)

    try:
        _MeshData = MeshAxiData.from_yaml(f"{filename}.yaml")
    
    # Catch all I/O and parsing errors raised by the library
    except ObjectLoadError as e:
        # Determine the specific cause based on the error message
        is_file_missing = "YAML file not found" in str(e)
        
        if is_file_missing:
            print(f"*** File missing: {filename}.yaml", flush=True)
        else:
            # Catches the converted YAMLError (Failed to parse YAML)
            raise RuntimeError(f"*** Failed to parse YAML in {filename}: {e}")
            
        print("*** trying to generate default gmshaxidata", flush=True)

        _MeshData = MeshAxiData(filename, algo2d)
        print("Meshdata created")

        _MeshData.default(prefix, Object, AirData)
        print("meshdata default")
        _MeshData.dump()
        print("mesh dump")
        

    except Exception as e:
        # Catch any *other* unexpected, non-loading errors
        raise RuntimeError(f"Failed to load MeshAxiData from {filename}: {e}")
    # add finaly section ??

    return _MeshData