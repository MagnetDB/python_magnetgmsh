#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
Provides definition for Site:

"""

import gmsh
import yaml

from python_magnetgeo import Insert
from python_magnetgeo import Bitter
from python_magnetgeo import Bitters
from python_magnetgeo import Supra
from python_magnetgeo import Supras
from python_magnetgeo import Screen
from .mesh.bcs import create_bcs
from .utils.lists import flatten

import_dict = {
    Insert.Insert: ".Insert",
    Bitter.Bitter: ".Bitter",
    Bitters.Bitters: ".Bitters",
    Supra.Supra: ".Supra",
    Supras.Supras: ".Supras",
}


def gmsh_ids(
    MSite, AirData: tuple, thickslit: bool = False, debug: bool = False
) -> tuple:
    """
    create gmsh geometry
    """
    print(f"gmsh_ids: MSite={MSite.name}")

    gmsh_ids = []

    def magnet_ids(f):
        Magnet = yaml.load(f, Loader=yaml.FullLoader)
        print(f"Magnet  {Magnet}")
        from importlib import import_module

        MyMagnet = import_module(import_dict[type(Magnet)], package="python_magnetgmsh")
        ids = MyMagnet.gmsh_ids(Magnet, (), thickslit, debug)
        return ids

    if isinstance(MSite.magnets, str):
        # print(f"msite/gmsh/{MSite.magnets} (str)")
        with open(f"{MSite.magnets}.yaml", "r") as f:
            ids = magnet_ids(f)
            gmsh_ids.append(ids)

    elif isinstance(MSite.magnets, dict):
        for key in MSite.magnets:
            # print(f"msite/gmsh/{key} (dict)")
            if isinstance(MSite.magnets[key], str):
                # print(f"msite/gmsh/{MSite.magnets[key]} (dict/str)")
                with open(f"{MSite.magnets[key]}.yaml", "r") as f:
                    ids = magnet_ids(f)
                    gmsh_ids.append(ids)
                    # print(f"ids[{key}]: {ids} (type={type(ids)})")

            if isinstance(MSite.magnets[key], list):
                for mname in MSite.magnets[key]:
                    # print(f"msite/gmsh/{mname} (dict/list)")
                    with open(f"{mname}.yaml", "r") as f:
                        ids = magnet_ids(f)
                        gmsh_ids.append(ids)
                        # print(f"ids[{mname}]: {ids} (type={type(ids)})")

    else:
        raise Exception(f"magnets: unsupported type {type(MSite.magnets)}")

    # Now create air
    Air_data = ()
    if AirData:
        ([r_min, r_max], [z_min, z_max]) = MSite.boundingBox()
        r0_air = 0
        dr_air = r_max * AirData[0]
        z0_air = z_min * AirData[1]
        dz_air = abs(z_max - z_min) * AirData[1]
        A_id = gmsh.model.occ.addRectangle(r0_air, z0_air, 0, dr_air, dz_air)

        flat_list = []
        if debug:
            print("list:", gmsh_ids)
            print("flat_list:", len(gmsh_ids))
        for sublist in gmsh_ids:
            # print(f"sublist: {sublist}")
            if not isinstance(sublist, tuple):
                raise Exception(
                    f"python_magnetgeo/gmsh: flat_list: expect a tuple got a {type(sublist)}"
                )
            # CHECK THIS?? should be flatten(sublist[0]) only
            # since sublist[0] contains id for Face 
            # and sublist[1] ................. edge (aka cracks for Bitters with thin cooling slits)
            # but sublist[1] ................. Rings for insert !!!
            flat_list += flatten(sublist[0])
            flat_list += flatten(sublist[1])
            """
            for elem in flatten(sublist[0]) + flatten(sublist[1]):            
                # print("elem:", elem, type(elem))
                if isinstance(elem, list):
                    for item in elem:
                        # print("item:", item, type(item))
                        if isinstance(item, list):
                            flat_list += flatten(item)
                        elif isinstance(item, int):
                            flat_list.append(item)
                elif isinstance(elem, int):
                    flat_list.append(elem)
            """
            
        if debug:
            print(f"flat_list={flat_list}")

        ov, ovv = gmsh.model.occ.fragment([(2, A_id)], [(2, j) for j in flat_list])
        gmsh.model.occ.synchronize()

        Air_data = (A_id, dr_air, z0_air, dz_air)

    
    return (gmsh_ids, Air_data)


def gmsh_bcs(
    MSite,
    mname: str,
    ids: tuple,
    thickslit: bool = False,
    debug: bool = False,
) -> dict:
    """
    retreive ids for bcs in gmsh geometry
    """
    print(f"gmsh_ids: MSite={MSite.name}")

    (gmsh_ids, Air_data) = ids
    # print("MSite/gmsh_bcs:", ids)

    defs = {}
    bcs_defs = {}

    def load_defs(Magnet, name, ids):
        from importlib import import_module

        MyMagnet = import_module(import_dict[type(Magnet)], package="python_magnetgmsh")
        tdefs = MyMagnet.gmsh_bcs(Magnet, name, ids, thickslit, debug)
        return tdefs

    if isinstance(MSite.magnets, str):
        # print(f"msite/gmsh/{MSite.magnets} (str)")
        with open(f"{MSite.magnets}.yaml", "r") as f:
            Object = yaml.load(f, Loader=yaml.FullLoader)
        defs.update(load_defs(Object, "", gmsh_ids))

    elif isinstance(MSite.magnets, dict):
        num = 0
        for i, key in enumerate(MSite.magnets):
            # print(f"msite/gmsh/{key} (dict)")
            if isinstance(MSite.magnets[key], str):
                # print(f"msite/gmsh/{key} (dict/str)")
                with open(f"{MSite.magnets[key]}.yaml", "r") as f:
                    Object = yaml.load(f, Loader=yaml.FullLoader)
                pname = f"{key}"
                defs.update(load_defs(Object, pname, gmsh_ids[num]))
                num += 1
            if isinstance(MSite.magnets[key], list):
                # print(f"msite/gmsh/{key} (dict/list)")
                for j, mname in enumerate(MSite.magnets[key]):
                    with open(f"{mname}.yaml", "r") as f:
                        Object = yaml.load(f, Loader=yaml.FullLoader)
                    pname = f"{key}_{Object.name}"
                    defs.update(load_defs(Object, pname, gmsh_ids[num]))
                    num += 1

    # TODO: add screens

    # Air
    if Air_data:
        (Air_id, dr_air, z0_air, dz_air) = Air_data

        ps = gmsh.model.addPhysicalGroup(2, [Air_id])
        gmsh.model.setPhysicalName(2, ps, "Air")
        defs["Air"] = ps
        # TODO: Axis, Inf
        gmsh.option.setNumber("Geometry.OCCBoundsUseStl", 1)

        bcs_defs[f"ZAxis"] = [0, z0_air, 0, z0_air + dz_air]
        bcs_defs[f"Infty"] = [
            [0, z0_air, dr_air, z0_air],
            [dr_air, z0_air, dr_air, z0_air + dz_air],
            [0, z0_air + dz_air, dr_air, z0_air + dz_air],
        ]

    for key in bcs_defs:
        defs[key] = create_bcs(key, bcs_defs[key], 1)

    return defs
