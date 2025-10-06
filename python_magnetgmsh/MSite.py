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


def gmsh_box(MSite, debug: bool = False) -> list:
    """
    get boundingbox for each channel
    """
    print(f"gmsh_box: MSite={MSite.name}")
    from importlib import import_module

    boxes = []

    
    for magnet in MSite.magnets:
        MyMagnet = import_module(import_dict[type(magnet)], package="python_magnetgmsh")
        box = MyMagnet.gmsh_box(magnet, debug)
        boxes.append(box)

    return boxes


def gmsh_ids(
    MSite, AirData: tuple, thickslit: bool = False, debug: bool = False
) -> tuple:
    """
    create gmsh geometry
    """
    from importlib import import_module
    print(f"gmsh_ids: MSite={MSite.name}")

    gmsh_ids = []

    
    for magnet in MSite.magnets:
        # print(f"msite/gmsh/{mname} (dict/list)")
        MyMagnet = import_module(import_dict[type(magnet)], package="python_magnetgmsh")
        ids = MyMagnet.gmsh_ids(magnet, (), thickslit, debug)
        gmsh_ids.append(ids)
        # print(f"ids[{mname}]: {ids} (type={type(ids)})")

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
    from importlib import import_module
    print(f"gmsh_ids: MSite={MSite.name}")

    (gmsh_ids, Air_data) = ids
    # print("MSite/gmsh_bcs:", ids)

    defs = {}
    bcs_defs = {}

    
    num = 0
    
    for j, magnet in enumerate(MSite.magnets):
        MyMagnet = import_module(import_dict[type(magnet)], package="python_magnetgmsh")
        tdefs = MyMagnet.gmsh_bcs(magnet, f"{magnet.name}", gmsh_ids[num], thickslit, debug)
        defs.update(tdefs)
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

        bcs_defs["ZAxis"] = [0, z0_air, 0, z0_air + dz_air]
        bcs_defs["Infty"] = [
            [0, z0_air, dr_air, z0_air],
            [dr_air, z0_air, dr_air, z0_air + dz_air],
            [0, z0_air + dz_air, dr_air, z0_air + dz_air],
        ]

    for key in bcs_defs:
        defs[key] = create_bcs(key, bcs_defs[key], 1)

    return defs
