#!/usr/bin/env python3
# encoding: UTF-8

"""defines Supra Insert structure"""
import yaml
import logging

from python_magnetgeo.Supra import Supra
from python_magnetgeo.Supras import Supras
from ..utils.lists import flatten

logger = logging.getLogger(__name__)

import_dict = {Supra: ".axi.Supra"}


def gmsh_box(Supras: Supras, debug: bool = False) -> list:
    """
    get boundingbox for each slit
    """
    logger.debug("Creating bounding boxes for Supras")
    from importlib import import_module

    boxes = []

    for magnet in Supras.magnets:
        MyMagnet = import_module(import_dict[type(magnet)], package="python_magnetgmsh")
        box = MyMagnet.gmsh_box(magnet, debug)
        logger.debug(f"Supras {magnet.name} bounding box: {box}")
        boxes.append(box)

    return boxes


def gmsh_ids(Supras: Supras, AirData: tuple, thickslit: bool = False, debug: bool = False) -> tuple:
    """
    create gmsh geometry
    """
    import gmsh
    from importlib import import_module

    gmsh_ids = []

    for magnet in Supras.magnets:
        MyMagnet = import_module(import_dict[type(magnet)], package="python_magnetgmsh")
        ids = MyMagnet.gmsh_ids(magnet, (), thickslit, debug)
        gmsh_ids.append(ids)

    # Now create air
    Air_data = ()
    if AirData:
        ([r_min, r_max], [z_min, z_max]) = Supras.boundingBox()
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
            if isinstance(sublist[0], list):
                flat_list += flatten(sublist[0])
            else:
                flat_list.append(sublist[0])

            """    
            for elem in sublist:
                # print("elem:", elem, type(elem))
                if isinstance(elem, list):
                    for item in elem:
                        # print("item:", elem, type(item))
                        if isinstance(item, list):
                            flat_list += flatten(item)
                        elif isinstance(item, int):
                            flat_list.append(item)
            """

        ov, ovv = gmsh.model.occ.fragment([(2, A_id)], [(2, j) for j in flat_list])
        gmsh.model.occ.synchronize()
        Air_data = (A_id, dr_air, z0_air, dz_air)

    return (gmsh_ids, (), Air_data)


def gmsh_bcs(Supras, mname: str, ids: tuple, thickslit: bool = False, debug: bool = False) -> dict:
    """
    retreive ids for bcs in gmsh geometry
    """
    import gmsh
    from importlib import import_module

    logger.debug(f"Creating boundary conditions for Supras: {Supras.name}")
    (gmsh_ids, gmsh_bc_ids, Air_data) = ids
    # logger.debug("Supras/gmsh_bcs:", ids)

    defs = {}
    bcs_defs = {}

    num = 0
    for i, magnet in enumerate(Supras.magnets):
        # print(f"Supras/gmsh/{mname} (dict/list)")
        # print(f"gmsh_ids[{key}]: {gmsh_ids[num]}")
        MyMagnet = import_module(import_dict[type(magnet)], package="python_magnetgmsh")
        tdefs = MyMagnet.gmsh_bcs(
            magnet, f"{Supras.name}_{magnet.name}", gmsh_ids[num], thickslit, debug
        )
        defs.update(tdefs)
        num += 1

    return defs
