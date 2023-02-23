#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
Provides definition for Site:

"""

import yaml

from python_magnetgeo import Insert
from python_magnetgeo import Bitter
from python_magnetgeo import Supra
from python_magnetgeo import Screen
from .mesh.bcs import create_bcs
from .utils.lists import flatten

import_dict = {
    Insert.Insert: ".Insert",
    Bitter.Bitter: ".Bitter",
    Supra.Supra: ".Supra",
}


def gmsh_ids(MSite, AirData: tuple, debug: bool = False) -> tuple:
    """
    create gmsh geometry
    """
    import gmsh

    gmsh_ids = []

    def magnet_ids(f):
        Magnet = yaml.load(f, Loader=yaml.FullLoader)
        from importlib import import_module

        MyMagnet = import_module(import_dict[type(Magnet)], package="python_magnetgmsh")
        ids = MyMagnet.gmsh_ids(Magnet, (), debug)
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
    if AirData:
        ([r_min, r_max], [z_min, z_max]) = MSite.boundingBox()
        r0_air = 0
        dr_air = abs(r_min - r_max) * AirData[0]
        z0_air = z_min * AirData[1]
        dz_air = abs(z_max - z_min) * AirData[1]
        A_id = gmsh.model.occ.addRectangle(r0_air, z0_air, 0, dr_air, dz_air)

        flat_list = []
        # print("list:", gmsh_ids)
        # print("flat_list:", len(gmsh_ids))
        for sublist in gmsh_ids:
            if not isinstance(sublist, tuple):
                raise Exception(
                    f"python_magnetgeo/gmsh: flat_list: expect a tuple got a {type(sublist)}"
                )
            for elem in sublist:
                # print("elem:", elem, type(elem))
                if isinstance(elem, list):
                    for item in elem:
                        # print("item:", elem, type(item))
                        if isinstance(item, list):
                            flat_list += flatten(item)
                        elif isinstance(item, int):
                            flat_list.append(item)

        start = 0
        end = len(flat_list)
        step = 10
        for i in range(start, end, step):
            x = i
            ov, ovv = gmsh.model.occ.fragment(
                [(2, A_id)], [(2, j) for j in flat_list[x : x + step]]
            )

        # need to account for changes
        gmsh.model.occ.synchronize()
        return (gmsh_ids, (A_id, dr_air, z0_air, dz_air))

    # need to account for changes
    gmsh.model.occ.synchronize()
    return (gmsh_ids, ())


def gmsh_bcs(MSite, mname: str, ids: tuple, debug: bool = False) -> dict:
    """
    retreive ids for bcs in gmsh geometry
    """
    import gmsh

    (gmsh_ids, Air_data) = ids
    # print("MSite/gmsh_bcs:", ids)

    defs = {}
    bcs_defs = {}

    def load_defs(Magnet, name, ids):
        from importlib import import_module

        MyMagnet = import_module(import_dict[type(Magnet)], package="python_magnetgmsh")
        tdefs = MyMagnet.gmsh_bcs(Magnet, name, ids, debug)
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
                print(f"gmsh_ids[{key}]: {gmsh_ids[i]}")
                # print(f"msite/gmsh/{MSite.magnets[key]} (dict/str)")
                with open(f"{MSite.magnets[key]}.yaml", "r") as f:
                    Object = yaml.load(f, Loader=yaml.FullLoader)
                pname = f"{key}"
                # if isinstance(Object, Insert.Insert):
                #    pname = ""
                defs.update(load_defs(Object, pname, gmsh_ids[num]))
                num += 1
            if isinstance(MSite.magnets[key], list):
                for j, mname in enumerate(MSite.magnets[key]):
                    print(f"msite/gmsh/{mname} (dict/list)")
                    # print(f"gmsh_ids[{key}]: {gmsh_ids[num]}")
                    with open(f"{mname}.yaml", "r") as f:
                        Object = yaml.load(f, Loader=yaml.FullLoader)
                    pname = f"{key}_{mname}"
                    # if isinstance(Object, Insert.Insert):
                    #     pname = ""
                    defs.update(load_defs(Object, pname, gmsh_ids[num]))
                    num += 1

    """
    for compound in [MSite.magnets, MSite.screens]:
        if isinstance(compound, str):
            with open(f"{compound}.yaml", "r") as f:
                Object = yaml.load(f, Loader=yaml.FullLoader)
            defs.update(load_defs(Object, "", ids))

        elif isinstance(compound, list):
            for i, mname in enumerate(compound):
                with open(f"{mname}.yaml", "r") as f:
                    Object = yaml.load(Object, Loader=yaml.FullLoader)
                defs.update(load_defs(f, "", gmsh_ids))

        elif isinstance(compound, dict):
            num = 0
            for i, key in enumerate(compound):
                if isinstance(compound[key], str):
                    with open(f"{compound[key]}.yaml", "r") as f:
                        Object = yaml.load(f, Loader=yaml.FullLoader)
                    defs.update(load_defs(Object, "", gmsh_ids))

                if isinstance(MSite.magnets[key], list):
                    for mname in MSite.magnets[key]:
                        with open(f"{mname}.yaml", "r") as f:
                            Object = yaml.load(f, Loader=yaml.FullLoader)
                        defs.update(load_defs(Object, key, gmsh_ids))

        else:
            raise Exception(f"magnets: unsupported type {type(compound)}")
        """

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

