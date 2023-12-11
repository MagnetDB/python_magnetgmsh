#!/usr/bin/env python3
# encoding: UTF-8

"""defines Supra Insert structure"""
import yaml

from python_magnetgeo.Supra import Supra
from python_magnetgeo.Supras import Supras
from .utils.lists import flatten

import_dict = {Supra: ".Supra"}


def gmsh_box(Supras: Supras, debug: bool = False) -> list:
    """
    get boundingbox for each slit
    """

    boxes = []

    def magnet_box(f):
        Magnet = yaml.load(f, Loader=yaml.FullLoader)
        print(f"Magnet  {Magnet}")
        from importlib import import_module

        MyMagnet = import_module(import_dict[type(Magnet)], package="python_magnetgmsh")
        box = MyMagnet.gmsh_box(Magnet, debug)
        return boxes

    if isinstance(Supras.magnets, str):
        # print(f"Bitters/gmsh/{Bitters.magnets} (str)")
        with open(f"{Supras.magnets}.yaml", "r") as f:
            boxes.append(magnet_box(f))

    elif isinstance(Supras.magnets, list):
        for mname in Supras.magnets:
            # print(f"Bitters/gmsh/{mname} (dict/list)")
            with open(f"{mname}.yaml", "r") as f:
                boxes.append(magnet_box(f))

    else:
        raise Exception(f"magnets: unsupported type {type(Supras.magnets)}")

    return boxes


def gmsh_ids(
    Supras: Supras, AirData: tuple, thickslit: bool = False, debug: bool = False
) -> tuple:
    """
    create gmsh geometry
    """
    import gmsh

    gmsh_ids = []

    def magnet_ids(f):
        Magnet = yaml.load(f, Loader=yaml.FullLoader)
        from importlib import import_module

        MyMagnet = import_module(import_dict[type(Magnet)], package="python_magnetgmsh")
        ids = MyMagnet.gmsh_ids(Magnet, (), thickslit, debug)
        return ids

    if isinstance(Supras.magnets, str):
        # print(f"Supras/gmsh/{Supras.magnets} (str)")
        with open(f"{Supras.magnets}.yaml", "r") as f:
            ids = magnet_ids(f)
            gmsh_ids.append(ids)

    elif isinstance(Supras.magnets, list):
        for mname in Supras.magnets:
            # print(f"Supras/gmsh/{mname} (dict/list)")
            with open(f"{mname}.yaml", "r") as f:
                ids = magnet_ids(f)
                gmsh_ids.append(ids)
                # print(f"ids[{mname}]: {ids} (type={type(ids)})")

    else:
        raise Exception(f"magnets: unsupported type {type(Supras.magnets)}")

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


def gmsh_bcs(
    Supras, mname: str, ids: tuple, thickslit: bool = False, debug: bool = False
) -> dict:
    """
    retreive ids for bcs in gmsh geometry
    """
    import gmsh

    print(f"gmsh_bcs: Supras={Supras.name}, mname={mname}, thickslit={thickslit}")
    (gmsh_ids, gmsh_bc_ids, Air_data) = ids
    # print("Supras/gmsh_bcs:", ids)

    defs = {}
    bcs_defs = {}

    def load_defs(Magnet, name, ids):
        from importlib import import_module

        MyMagnet = import_module(import_dict[type(Magnet)], package="python_magnetgmsh")
        tdefs = MyMagnet.gmsh_bcs(Magnet, name, ids, thickslit, debug)
        return tdefs

    if isinstance(Supras.magnets, str):
        # print(f"Supras/gmsh/{Supras.magnets} (str)")
        with open(f"{Supras.magnets}.yaml", "r") as f:
            Object = yaml.load(f, Loader=yaml.FullLoader)
        defs.update(load_defs(Object, f"{Supras.name}_{Object.name}", gmsh_ids))

    elif isinstance(Supras.magnets, list):
        num = 0
        for i, mname in enumerate(Supras.magnets):
            # print(f"Supras/gmsh/{mname} (dict/list)")
            # print(f"gmsh_ids[{key}]: {gmsh_ids[num]}")
            with open(f"{mname}.yaml", "r") as f:
                Object = yaml.load(f, Loader=yaml.FullLoader)
            defs.update(
                load_defs(Object, f"{Supras.name}_{Object.name}", gmsh_ids[num])
            )
            num += 1

    return defs
