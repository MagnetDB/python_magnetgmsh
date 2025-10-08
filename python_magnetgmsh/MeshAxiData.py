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

ObjectType = MSite | Bitters | Supras | Insert | Bitter | Supra | Screen | Helix | Ring


class MeshAxiData(yaml.YAMLObject):
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
        hypoths: list = [],
        mesh_dict: dict = {},
    ):
        """constructor"""
        self.name = name
        self.algosurf = algosurf

        # depending of geometry type
        self.surfhypoths = hypoths
        self.mesh_dict = mesh_dict

    def __repr__(self):
        """representation"""
        return "%s(name=%r, algosurf=%r, surfhypoths=%r, mesh_dict=%r)" % (
            self.__class__.__name__,
            self.name,
            self.algosurf,
            self.surfhypoths,
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
            self.surfhypoths.append(self.part_default(Object, f"{hypname}{Object.name}_Screen"))
            mesh_dict[f"{hypname}{Object.name}_Screen"] = len(self.surfhypoths) - 1

        elif isinstance(Object, Bitter):
            hypname = ""
            if mname:
                hypname = f"{mname}"
            print(
                f"Creating MeshAxiData for Bitter {Object.name}, mname={mname}, hypname={hypname}"
            )
            psnames = Object.get_names(hypname, is2D=True, verbose=debug)
            print(f"psnames={psnames}")
            surfhypoths_names = [re.sub(r"_Slit\d+", "", psname) for psname in psnames]
            surfhypoths_names = list(set(surfhypoths_names))
            self.surfhypoths.append(self.part_default(Object, surfhypoths_names[0]))
            for psname in surfhypoths_names:
                print(f"\tpsname={psname}")
                mesh_dict[psname] = len(self.surfhypoths) - 1

        elif isinstance(Object, Supra):
            print(f"Creating MeshAxiData for Supra {Object.name}, mname={mname}")
            hypname = ""
            if mname:
                hypname = f"{mname}_"
            print(f"hypname/Object.name={hypname}{Object.name}")

            if Object.detail == DetailLevel.NONE:
                self.surfhypoths.append(self.part_default(Object, f"{hypname}{Object.name}"))
                mesh_dict[f"{hypname}{Object.name}"] = len(self.surfhypoths) - 1

            # (_i, _dp, _p, _i_dp, _Mandrin, _Sc, _Du)
            elif Object.detail == DetailLevel.DBLPANCAKE:
                self.surfhypoths.append(self.part_default(Object, f"{hypname}{Object.name}_dp"))
                n_dp = len(Object.get_magnet_struct().dblpancakes)
                for i in range(n_dp):
                    mesh_dict[f"{hypname}{Object.name}_dp{i}"] = (
                        len(self.surfhypoths) - 1,
                        1,
                    )
                self.surfhypoths.append(self.part_default(Object, f"{hypname}{Object.name}_i"))
                for i in range(n_dp - 1):
                    mesh_dict[f"{hypname}{Object.name}_i{i}"] = (
                        len(self.surfhypoths) - 1,
                        0,
                    )

            elif Object.detail == DetailLevel.PANCAKE:
                n_dp = len(Object.get_magnet_struct().dblpancakes)
                self.surfhypoths.append(self.part_default(Object, f"{hypname}{Object.name}_dp_p"))
                for i in range(n_dp):
                    mesh_dict[f"{hypname}{Object.name}_dp{i}_p0"] = (
                        len(self.surfhypoths) - 1,
                        2,
                    )
                    mesh_dict[f"{hypname}{Object.name}_dp{i}_p1"] = (
                        len(self.surfhypoths) - 1,
                        2,
                    )
                self.surfhypoths.append(self.part_default(Object, f"{hypname}{Object.name}_dp_i"))
                for i in range(n_dp):
                    mesh_dict[f"{hypname}{Object.name}_dp{i}_i"] = (
                        len(self.surfhypoths) - 1,
                        3,
                    )
                self.surfhypoths.append(self.part_default(Object, f"{hypname}{Object.name}_i"))
                for i in range(n_dp - 1):
                    mesh_dict[f"{hypname}{Object.name}_i{i}"] = (
                        len(self.surfhypoths) - 1,
                        0,
                    )

            elif Object.detail == DetailLevel.TAPE:
                n_dp = len(Object.get_magnet_struct().dblpancakes)
                self.surfhypoths.append(
                    self.part_default(Object, f"{hypname}{Object.name}_dp_p_Mandrin")
                )
                for i in range(n_dp):
                    mesh_dict[f"{hypname}{Object.name}_dp{i}_p0_Mandrin"] = (
                        len(self.surfhypoths) - 1,
                        4,
                    )
                    mesh_dict[f"{hypname}{Object.name}_dp{i}_p1_Mandrin"] = (
                        len(self.surfhypoths) - 1,
                        4,
                    )
                self.surfhypoths.append(
                    self.part_default(Object, f"{hypname}{Object.name}_dp_p_t_SC")
                )
                for i in range(n_dp):
                    n_dp_tape = Object.get_magnet_struct().dblpancakes[i].pancake.getN()
                    for j in range(n_dp_tape):
                        mesh_dict[f"{hypname}{Object.name}_dp{i}_p0_t{j}_SC"] = (
                            len(self.surfhypoths) - 1,
                            5,
                        )
                        mesh_dict[f"{hypname}{Object.name}_dp{i}_p1_t{j}_SC"] = (
                            len(self.surfhypoths) - 1,
                            5,
                        )
                self.surfhypoths.append(
                    self.part_default(Object, f"{hypname}{Object.name}_dp_p_t_Duromag")
                )
                for i in range(n_dp):
                    n_dp_tape = Object.get_magnet_struct().dblpancakes[i].pancake.getN()
                    for j in range(n_dp_tape):
                        mesh_dict[f"{hypname}{Object.name}_dp{i}_p0_t{j}_Duromag"] = (
                            len(self.surfhypoths) - 1,
                            6,
                        )
                        mesh_dict[f"{hypname}{Object.name}_dp{i}_p1_t{j}_Duromag"] = (
                            len(self.surfhypoths) - 1,
                            6,
                        )
                self.surfhypoths.append(self.part_default(Object, f"{hypname}{Object.name}_dp_i"))
                for i in range(n_dp):
                    mesh_dict[f"{hypname}{Object.name}_dp{i}_i"] = (
                        len(self.surfhypoths) - 1,
                        3,
                    )
                self.surfhypoths.append(self.part_default(Object, f"{hypname}{Object.name}_i"))
                for i in range(n_dp - 1):
                    mesh_dict[f"{hypname}{Object.name}_i{i}"] = (
                        len(self.surfhypoths) - 1,
                        0,
                    )
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
                self.surfhypoths.append(self.part_default(H, psname))
                for n in range(len(H.modelaxi.turns) + 2):
                    mesh_dict[psnames[num]] = len(self.surfhypoths) - 1
                    num += 1

            for i, R in enumerate(Object.rings):
                print(f"MeshAxiData for R: {R.name}")
                self.surfhypoths.append(self.part_default(R, psnames[i + num]))
                mesh_dict[psnames[i + num]] = len(self.surfhypoths) - 1

        if Air:
            print("MeshAxiData for Air")
            [Air_, Biot_] = self.air_default(Air)
            self.surfhypoths.append(Air_)
            mesh_dict["Air"] = len(self.surfhypoths) - 1
            self.surfhypoths.append(Biot_)
            mesh_dict["Biot"] = len(self.surfhypoths) - 1
            # print "Creating MeshAxiData for Air... done"
        else:
            print("No Air defined")
        if debug:
            print("---------------------------------------------------------")
            print("surfhypoths: ", len(self.surfhypoths), self.surfhypoths)
            for i, hypoth in enumerate(self.surfhypoths):
                print(f"hypoth[{i}]: {hypoth}")
            print("---------------------------------------------------------")

        self.mesh_dict = mesh_dict
        return mesh_dict

    def load(self, Air: bool = False, debug: bool = False):
        """
        Load Mesh params from yaml file
        """

        data = None
        filename = self.name
        if Air:
            filename += "_withAir"
        filename += "_gmshaxidata.yaml"

        with open(filename, "r") as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
            # print(f"data={data}")

        self.name = data.name
        self.algosurf = data.algosurf
        self.mesh_dict = data.mesh_dict
        self.surfhypoths = data.surfhypoths
        print(f"MeshAxiData/Load: {filename} (pwd={os.getcwd()})")
        print(f"MeshAxiData/Load: hypoths={self.surfhypoths})")
        if debug:
            print("---------------------------------------------------------")
            print("surfhypoths: ", len(self.surfhypoths), self.surfhypoths)
            for i, hypoth in enumerate(self.surfhypoths):
                print(f"hypoth[{i}]: {hypoth}")
            print("---------------------------------------------------------")

    def dump(self, Air: bool = False):
        """
        Dump Mesh params to yaml file
        """

        filename = self.name
        if Air:
            filename += "_withAir"
        filename += "_gmshaxidata.yaml"
        print(f"dump mesh hypothesys to {filename}")
        try:
            with open(filename, "w") as ostream:
                yaml.dump(self, stream=ostream)
        except:
            print("Failed to dump MeshAxiData")


def MeshAxiData_constructor(loader, node):
    values = loader.construct_mapping(node)
    name = values["name"]
    algosurf = values["algosurf"]
    surfhypoths = values["surfhypoths"]
    mesh_dict = values["mesh_dict"]
    return MeshAxiData(name, algosurf, surfhypoths, mesh_dict)


yaml.add_constructor("!MeshAxiData", MeshAxiData_constructor)
