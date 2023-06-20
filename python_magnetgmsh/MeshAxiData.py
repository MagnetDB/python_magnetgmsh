#!/usr/bin/env python3
# encoding: UTF-8

"""Enable to define mesh hypothesis (aka params) for Gmsh surfacic and volumic meshes"""
from typing import Union

import os

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

ObjectType = Union[MSite, Bitters, Supras, Insert, Bitter, Supra, Screen, Helix, Ring]


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

    def __init__(self, name: str, algosurf: str = "BLSURF"):
        """constructor"""
        self.name = name
        self.algosurf = algosurf

        # depending of geometry type
        self.surfhypoths = []
        self.mesh_dict = {}

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

    def part_default(
        self, H: Union[Helix, Bitter, Supra, Screen, Ring], addname: str = ""
    ):
        """
        Define default mesh params for Helix
        """
        # print(f"part_default: name={H.name}, lc={H.get_lc}")
        return H.get_lc()

    def air_default(self, Data: tuple):
        """
        Define default mesh params for Air
        """

        # print("Define default mesh params for Air")
        name = "Air"

        # Retreive main characteristics
        width = (10 * Data[2]) / 5
        physsize = min(width / 100.0, 40)

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
            if isinstance(Object.magnets, str):
                YAMLFile = os.path.join(workingDir, f"{Object.magnets}.yaml")
                with open(YAMLFile, "r") as istream:
                    mObject = yaml.load(istream, Loader=yaml.FullLoader)
                    _tmp = self.default(Object.magnets, mObject, (), workingDir)
                    mesh_dict.update(_tmp)
            elif isinstance(Object.magnets, dict):
                for i, key in enumerate(Object.magnets):
                    if isinstance(Object.magnets[key], str):
                        YAMLFile = os.path.join(
                            workingDir, f"{Object.magnets[key]}.yaml"
                        )
                        with open(YAMLFile, "r") as istream:
                            mObject = yaml.load(istream, Loader=yaml.FullLoader)
                            _tmp = self.default(key, mObject, (), workingDir)
                            mesh_dict.update(_tmp)
                    elif isinstance(Object.magnets[key], list):
                        for j, mname in enumerate(Object.magnets[key]):
                            YAMLFile = os.path.join(workingDir, f"{mname}.yaml")
                            with open(YAMLFile, "r") as istream:
                                mObject = yaml.load(istream, Loader=yaml.FullLoader)
                                _tmp = self.default(key, mObject, (), workingDir)
                                mesh_dict.update(_tmp)
                    else:
                        raise RuntimeError(
                            f"magnets: unsupported type ({type(Object.magnets[key])})"
                        )

        elif isinstance(Object, Bitters):
            print(f"Creating MeshAxiData for Bitters {Object.name}, mname={mname}")
            hypname = ""
            if mname:
                hypname = f"{mname}"
            for part in Object.magnets:
                YAMLFile = os.path.join(workingDir, f"{part}.yaml")
                with open(YAMLFile, "r") as istream:
                    mObject = yaml.load(istream, Loader=yaml.FullLoader)
                    _tmp = self.default(hypname, mObject, (), workingDir)
                    mesh_dict.update(_tmp)

        elif isinstance(Object, Supras):
            print(f"Creating MeshAxiData for Supras {Object.name}, mname={mname}")
            hypname = ""
            if mname:
                hypname = f"{mname}_"
            for part in Object.magnets:
                YAMLFile = os.path.join(workingDir, f"{part}.yaml")
                with open(YAMLFile, "r") as istream:
                    mObject = yaml.load(istream, Loader=yaml.FullLoader)
                    _tmp = self.default(hypname, mObject, (), workingDir)
                    mesh_dict.update(_tmp)

        elif isinstance(Object, Screen):
            print(f"Creating MeshAxiData for Screen {Object.name}, mname={mname}")
            hypname = ""
            if mname:
                hypname = f"{mname}_"
            self.surfhypoths.append(
                self.part_default(Object, f"{hypname}{Object.name}_Screen")
            )
            mesh_dict[f"{hypname}{Object.name}_Screen"] = len(self.surfhypoths) - 1

        elif isinstance(Object, Bitter):
            print(f"Creating MeshAxiData for Bitter {Object.name}, mname={mname}")
            hypname = Object.name
            if mname:
                hypname = f"{mname}_{Object.name}"
            if Object.z[0] < -Object.axi.h:
                self.surfhypoths.append(self.part_default(Object, f"{hypname}_B0"))
                mesh_dict[f"{hypname}_B0"] = len(self.surfhypoths) - 1
            for i in range(len(Object.axi.turns)):
                self.surfhypoths.append(self.part_default(Object, f"{hypname}_B{i+1}"))
                mesh_dict[f"{hypname}_B{i+1}"] = len(self.surfhypoths) - 1
            if Object.z[1] > Object.axi.h:
                self.surfhypoths.append(
                    self.part_default(Object, f"{hypname}_B{len(Object.axi.turns)+1}")
                )
                mesh_dict[f"{hypname}_B{len(Object.axi.turns)+1}"] = (
                    len(self.surfhypoths) - 1
                )

        elif isinstance(Object, Supra):
            print(f"Creating MeshAxiData for Supra {Object.name}, mname={mname}")
            hypname = ""
            if mname:
                hypname = f"{mname}_"
            print(f"hypname/Object.name={hypname}{Object.name}")

            if Object.detail == "None":
                self.surfhypoths.append(
                    self.part_default(Object, f"{hypname}{Object.name}")
                )
                mesh_dict[f"{hypname}{Object.name}"] = len(self.surfhypoths) - 1

            # (_i, _dp, _p, _i_dp, _Mandrin, _Sc, _Du)
            elif Object.detail == "dblpancake":
                self.surfhypoths.append(
                    self.part_default(Object, f"{hypname}{Object.name}_dp")
                )
                for i in range(Object.get_magnet_struct().getN()):
                    mesh_dict[f"{hypname}{Object.name}_dp{i}"] = (
                        len(self.surfhypoths) - 1,
                        1,
                    )
                self.surfhypoths.append(
                    self.part_default(Object, f"{hypname}{Object.name}_i")
                )
                for i in range(Object.get_magnet_struct().getN() - 1):
                    mesh_dict[f"{hypname}{Object.name}_i{i}"] = (
                        len(self.surfhypoths) - 1,
                        0,
                    )

            elif Object.detail == "pancake":
                n_dp = Object.get_magnet_struct().getN()
                self.surfhypoths.append(
                    self.part_default(Object, f"{hypname}{Object.name}_dp_p")
                )
                for i in range(n_dp):
                    mesh_dict[f"{hypname}{Object.name}_dp{i}_p0"] = (
                        len(self.surfhypoths) - 1,
                        2,
                    )
                    mesh_dict[f"{hypname}{Object.name}_dp{i}_p1"] = (
                        len(self.surfhypoths) - 1,
                        2,
                    )
                self.surfhypoths.append(
                    self.part_default(Object, f"{hypname}{Object.name}_dp_i")
                )
                for i in range(n_dp):
                    mesh_dict[f"{hypname}{Object.name}_dp{i}_i"] = (
                        len(self.surfhypoths) - 1,
                        3,
                    )
                self.surfhypoths.append(
                    self.part_default(Object, f"{hypname}{Object.name}_i")
                )
                for i in range(n_dp - 1):
                    mesh_dict[f"{hypname}{Object.name}_i{i}"] = (
                        len(self.surfhypoths) - 1,
                        0,
                    )

            elif Object.detail == "tape":
                n_dp = Object.get_magnet_struct().getN()
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
                self.surfhypoths.append(
                    self.part_default(Object, f"{hypname}{Object.name}_dp_i")
                )
                for i in range(n_dp):
                    mesh_dict[f"{hypname}{Object.name}_dp{i}_i"] = (
                        len(self.surfhypoths) - 1,
                        3,
                    )
                self.surfhypoths.append(
                    self.part_default(Object, f"{hypname}{Object.name}_i")
                )
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
            hypname = ""
            if mname:
                hypname = f"{mname}_"
            theInsert = Object
            for i, H_cfg in enumerate(Object.Helices):
                print("MeshAxiData for H:", H_cfg)
                H = None
                with open(f"{H_cfg}.yaml", "r") as f:
                    H = yaml.load(f, Loader=yaml.FullLoader)
                self.surfhypoths.append(self.part_default(H, f"{hypname}H{i+1}"))
                mesh_dict[f"{hypname}H{i+1}_Cu0"] = len(self.surfhypoths) - 1
                for j in range(len(H.axi.turns)):
                    mesh_dict[f"{hypname}H{i+1}_Cu{j+1}"] = len(self.surfhypoths) - 1
                mesh_dict[f"{hypname}H{i+1}_Cu{len(H.axi.turns)+1}"] = (
                    len(self.surfhypoths) - 1
                )
            if Object.Rings:
                for i, R_cfg in enumerate(Object.Rings):
                    print(f"MeshAxiData for R: {R_cfg}")
                    R = None
                    with open(f"{R_cfg}.yaml", "r") as f:
                        R = yaml.load(f, Loader=yaml.FullLoader)
                    self.surfhypoths.append(self.part_default(R, f"{hypname}R{i+1}"))
                    mesh_dict[f"{hypname}R{i+1}"] = len(self.surfhypoths) - 1

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
    return MeshAxiData(name, algosurf)


yaml.add_constructor("!MeshAxiData", MeshAxiData_constructor)
