#!/usr/bin/env python3
# encoding: UTF-8

"""Enable to define mesh hypothesis (aka params) for Gmsh surfacic and volumic meshes"""
from typing import Union

import os

import math
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

ObjectType = Union[
    MSite, 
    Bitters, 
    Supras, 
    Insert, 
    Bitter, 
    Supra, 
    Screen, 
    Helix, 
    Ring
    ]

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

    yaml_tag = u'MeshAxiData'

    def __init__(self, name: str, algosurf: str = "BLSURF"):
        """constructor"""
        self.name = name
        self.algosurf = algosurf

        # depending of geometry type
        self.surfhypoths = []
        self.mesh_dict = {}


    def __repr__(self):
        """representation"""
        return "%s(name=%r, algosurf=%r, surfhypoths=%r, mesh_dict=%r)" % \
               (self.__class__.__name__,
                self.name,
                self.algosurf,
                self.surfhypoths,
                self.mesh_dict)

    def algo2d(self, algosurf):
        print("set surfacic mesh algo - not implemented yet")

    def helix_default(self, H: Union[Helix, Bitter, Supra, Screen], addname: str = ""):
        """
        Define default mesh params for Helix
        """

        name = H.name
        if addname:
            name = addname

        # Retreive main characteristics
        r_int = H.r[0]
        r_ext = H.r[1]
        z_inf = H.z[0]
        z_sup = H.z[1]
        
        physsize = (r_ext - r_int)/3.
        minsize = (r_ext - r_int) / 10.
        maxsize = (r_ext - r_int) * 10
        
        # Params for current inputs
        inputs = [name, [2, 1, physsize, minsize, maxsize]]
        return inputs

    def ring_default(self, Ring: Ring, addname: str = ""):
        """
        Define default mesh params for Ring
        """

        name = Ring.name
        if addname:
            name = addname

        # Retreive main characteristics
        n = Ring.n
        angle = Ring.angle * math.pi/180.

        radius = Ring.r
        z_inf = Ring.z[0]
        z_sup = Ring.z[1]

        physsize = (radius[3] - radius[0])/ 10.
        minsize = (radius[3] - radius[0]) / 100.
        maxsize = (radius[3] - radius[0]) / 3.
        
        # Params for Surfaces
        H1 = [name, [2, 1, physsize, minsize, maxsize]]
        
        return H1

    def air_default(self, Data: tuple):
        """
        Define default mesh params for Air
        """

        # print("Define default mesh params for Air")
        name = "Air"

        # Retreive main characteristics
        width = (10 * Data[2]) / 5
        physsize = width/3.
        minsize = width / 100.
        maxsize = width * 10.
        
        # Params for InfR1
        infty = [name, [2, 1, physsize, minsize, maxsize]]

        # Params for BiotShell
        Biotshell = ["Biotshell", [2, 1, Data[3]/50., Data[3]/500., Data[3]/10.]]

        return [infty, Biotshell]

    def default(self, mname: str, Object: ObjectType, Air: tuple, workingDir: str = "", debug: bool = False):
        """
        Define default mesh params
        """

        print(f"{__name__}: creating default MeshAxiData,  Object.name={Object.name}, Air={Air}, wd={workingDir}")
        mesh_dict = {}

        if isinstance(Object, MSite):
            print (f"Creating MeshAxiData for MSite {Object.name} not implemented")
            if isinstance(Object.magnets, str):
                YAMLFile = os.path.join(workingDir, f"{Object.magnets}.yaml")
                with open(YAMLFile, 'r') as istream:
                    mObject = yaml.load(istream, Loader=yaml.FullLoader)
                    _tmp = self.default(Object.magnets, mObject, False, workingDir)
                    mesh_dict.update(_tmp)
            elif isinstance(Object.magnets, dict):
                for i,key in enumerate(Object.magnets):
                    if isinstance(Object.magnets[key], str):
                        YAMLFile = os.path.join(workingDir, f"{Object.magnets[key]}.yaml")
                        with open(YAMLFile, 'r') as istream:
                            mObject = yaml.load(istream, Loader=yaml.FullLoader)
                            _tmp = self.default(key, mObject, False, workingDir)
                            mesh_dict.update(_tmp)
                    elif isinstance(Object.magnets[key], list):
                        for j,mname in enumerate(Object.magnets[key]):
                            YAMLFile = os.path.join(workingDir, f"{mname}.yaml")
                            with open(YAMLFile, 'r') as istream:
                                mObject = yaml.load(istream, Loader=yaml.FullLoader)
                                _tmp = self.default(key, mObject, False, workingDir)
                                mesh_dict.update(_tmp)
                    else:
                        raise RuntimeError(f"magnets: unsupported type ({type(Object.magnets[key])})" )

        elif isinstance(Object, Bitters):
            print(f"Creating MeshAxiData for Bitters {Object.name}")
            for part in Object.magnets:
                YAMLFile = os.path.join(workingDir, f"{part}.yaml")
                with open(YAMLFile, 'r') as istream:
                    mObject = yaml.load(istream, Loader=yaml.FullLoader)
                    _tmp = self.default("", mObject, False, workingDir)
                    mesh_dict.update(_tmp)

        elif isinstance(Object, Supras):
            print(f"Creating MeshAxiData for Supras {Object.name}")
            for part in Object.magnets:
                YAMLFile = os.path.join(workingDir, f"{part}.yaml")
                with open(YAMLFile, 'r') as istream:
                    mObject = yaml.load(istream, Loader=yaml.FullLoader)
                    _tmp = self.default("", mObject, False, workingDir)
                    mesh_dict.update(_tmp)
                    
        elif isinstance(Object, Screen):
            print(f"Creating MeshAxiData for Screen {Object.name}")
            hypname = ""
            if mname:
                hypname = f'{mname}_'
            self.surfhypoths.append(self.helix_default(Object, f"{hypname}{Object.name}_Screen"))
            mesh_dict[f'{hypname}{Object.name}_Screen'] = len(self.surfhypoths)-1
            
        elif isinstance(Object, Bitter):
            print(f"Creating MeshAxiData for Bitter {Object.name}")
            hypname = ""
            if mname:
                hypname = f'{mname}_'
            for i in range(len(Object.axi.turns)):
                self.surfhypoths.append(self.helix_default(Object, f"{hypname}{Object.name}_B{i+1}"))
                mesh_dict[f'{hypname}{Object.name}_B{i+1}'] = len(self.surfhypoths)-1
                
        elif isinstance(Object, Supra):
            print(f"Creating MeshAxiData for Supra {Object.name}")
            hypname = ""
            if mname:
                hypname = f'{mname}_'
            print(f'hypname/Object.name={hypname}{Object.name}')

            if Object.detail == "None":
                self.surfhypoths.append(self.helix_default(Object, f"{hypname}{Object.name}"))
                mesh_dict[f'{hypname}{Object.name}'] = len(self.surfhypoths)-1
                
            elif Object.detail == "dblpancake":
                self.surfhypoths.append(self.helix_default(Object, f"{hypname}{Object.name}_dp"))
                for i in range(Object.get_magnet_struct().getN()):
                    mesh_dict[f'{hypname}{Object.name}_dp{i}'] = len(self.surfhypoths)-1
                self.surfhypoths.append(self.helix_default(Object, f"{hypname}{Object.name}_i"))
                for i in range(Object.get_magnet_struct().getN()-1):
                    mesh_dict[f'{hypname}{Object.name}_i{i}'] = len(self.surfhypoths)-1
                
            elif Object.detail == "pancake":
                n_dp = Object.get_magnet_struct().getN()
                self.surfhypoths.append(self.helix_default(Object, f"{hypname}{Object.name}_dp_p"))
                for i in range(n_dp):
                    mesh_dict[f'{hypname}{Object.name}_dp{i}_p0'] = len(self.surfhypoths)-1
                    mesh_dict[f'{hypname}{Object.name}_dp{i}_p1'] = len(self.surfhypoths)-1
                self.surfhypoths.append(self.helix_default(Object, f"{hypname}{Object.name}_dp_i"))
                for i in range(n_dp):
                    mesh_dict[f'{hypname}{Object.name}_dp{i}_i'] = len(self.surfhypoths)-1
                self.surfhypoths.append(self.helix_default(Object, f"{hypname}{Object.name}_i"))
                for i in range(n_dp-1):
                    mesh_dict[f'{hypname}{Object.name}_i{i}'] = len(self.surfhypoths)-1
                    
            elif Object.detail == "tape":
                n_dp = Object.get_magnet_struct().getN()
                self.surfhypoths.append(self.helix_default(Object, f"{hypname}{Object.name}_dp_p_Mandrin"))
                for i in range(n_dp):
                    mesh_dict[f'{hypname}{Object.name}_dp{i}_p0_Mandrin'] = len(self.surfhypoths)-1
                    mesh_dict[f'{hypname}{Object.name}_dp{i}_p1_Mandrin'] = len(self.surfhypoths)-1
                self.surfhypoths.append(self.helix_default(Object, f"{hypname}{Object.name}_dp_p_t_SC"))
                for i in range(n_dp):
                    n_dp_tape = Object.get_magnet_struct().dblpancakes[i].pancake.getN()
                    for j in range(n_dp_tape):
                        mesh_dict[f'{hypname}{Object.name}_dp{i}_p0_t{j}_SC'] = len(self.surfhypoths)-1
                        mesh_dict[f'{hypname}{Object.name}_dp{i}_p1_t{j}_SC'] = len(self.surfhypoths)-1
                self.surfhypoths.append(self.helix_default(Object, f"{hypname}{Object.name}_dp_p_t_Duromag"))
                for i in range(n_dp):
                    n_dp_tape = Object.get_magnet_struct().dblpancakes[i].pancake.getN()
                    for j in range(n_dp_tape):
                        mesh_dict[f'{hypname}{Object.name}_dp{i}_p0_t{j}_Duromag'] = len(self.surfhypoths)-1
                        mesh_dict[f'{hypname}{Object.name}_dp{i}_p1_t{j}_Duromag'] = len(self.surfhypoths)-1
                self.surfhypoths.append(self.helix_default(Object, f"{hypname}{Object.name}_dp_i"))
                for i in range(n_dp):
                    mesh_dict[f'{hypname}{Object.name}_dp{i}_i'] = len(self.surfhypoths)-1
                self.surfhypoths.append(self.helix_default(Object, f"{hypname}{Object.name}_i"))
                for i in range(n_dp-1):
                    mesh_dict[f'{hypname}{Object.name}_i{i}'] = len(self.surfhypoths)-1
            else:
                raise RuntimeError(f"MeshAxiData: Unknow detail level ({Object.detail}) for Supra {Object.name}")

        elif isinstance(Object, Insert):
            print(f"Creating MeshAxiData for Insert {Object.name}")
            hypname = ""
            if mname:
                hypname = f'{mname}_'
            theInsert = Object
            for i,H_cfg in enumerate(Object.Helices):
                print ("MeshAxiData for H:", H_cfg, "MeshType=")
                H = None
                with open(f"{H_cfg}.yaml", 'r') as f:
                    H = yaml.load(f, Loader=yaml.FullLoader)
                self.surfhypoths.append(self.helix_default(H, f"{hypname}H{i+1}"))
                mesh_dict[f'{hypname}H{i+1}_Cu0'] = len(self.surfhypoths)-1
                for j in range(len(H.axi.turns)):
                    mesh_dict[f'{hypname}H{i+1}_Cu{j+1}'] = len(self.surfhypoths)-1
                mesh_dict[f'{hypname}H{i+1}_Cu{len(H.axi.turns)+1}'] = len(self.surfhypoths)-1
            if Object.Rings:
                for i,R_cfg in enumerate(Object.Rings):
                    print (f"MeshAxiData for R: {R_cfg}")
                    R = None
                    with open(f"{R_cfg}.yaml", 'r') as f:
                        R = yaml.load(f, Loader=yaml.FullLoader)
                    self.surfhypoths.append(self.ring_default(R, f"{hypname}R{i+1}"))
                    mesh_dict[f'{hypname}R{i+1}'] = len(self.surfhypoths)-1

        if Air:
            print("MeshAxiData for Air")
            [Air_, Biot_] = self.air_default(Air)
            self.surfhypoths.append(Air_)
            mesh_dict['Air'] = len(self.surfhypoths)-1
            self.surfhypoths.append(Biot_)
            mesh_dict['Biot'] = len(self.surfhypoths)-1
            # print "Creating MeshAxiData for Air... done"
        else:
            print("No Air defined")
        if debug:
            print( "---------------------------------------------------------" )
            print( "surfhypoths: ", len(self.surfhypoths), self.surfhypoths)
            for i,hypoth in enumerate(self.surfhypoths):
                print(f"hypoth[{i}]: {hypoth}")
            print( "---------------------------------------------------------")
        
        self.mesh_dict = mesh_dict
        return mesh_dict

    def load(self, Air: bool = False, debug: bool = False):
        """
        Load Mesh params from yaml file
        """
        
        data = None
        filename = self.name
        if Air:
            filename += '_withAir'
        filename += '_meshaxidata.yaml'

        with open(filename, 'r') as f:
            data = yaml.load(f, Loader=yaml.FullLoader)

        self.name = data.name
        self.algosurf = data.algosurf
        self.mesh_dict = data.mesh_dict
        self.surfhypoths = data.surfhypoths
        print(f"MeshAxiData/Load: {filename}")
        if debug:
            print( "---------------------------------------------------------" )
            print( "surfhypoths: ", len(self.surfhypoths), self.surfhypoths)
            for i,hypoth in enumerate(self.surfhypoths):
                print(f"hypoth[{i}]: {hypoth}")
            print( "---------------------------------------------------------")

        
    def dump(self, Air: bool = False):
        """
        Dump Mesh params to yaml file
        """

        filename = self.name
        if Air:
            filename += '_withAir'
        filename += '_meshaxigmshdata.yaml'
        print (f"dump mesh hypothesys to {filename}")
        try:
            with open(filename, 'w') as ostream:
                yaml.dump(self, stream=ostream)
        except:
            print ("Failed to dump MeshAxiData")


def MeshAxiData_constructor(loader, node):
    values = loader.construct_mapping(node)
    name = values["name"]
    algosurf = values["algosurf"]
    surfhypoths = values["surfhypoths"]
    mesh_dict = values["mesh_dict"]
    return MeshAxiData(name, algosurf)

yaml.add_constructor(u'!MeshAxiData', MeshAxiData_constructor)

