#!/usr/bin/env python3
# encoding: UTF-8

"""defines Bitter Insert structure"""
import yaml

from python_magnetgeo.Bitter import Bitter
from python_magnetgeo.Bitters import Bitters
from .utils.lists import flatten

import_dict = {Bitter: ".Bitter"}


def gmsh_ids(Bitters: Bitters, AirData: tuple, debug: bool = False) -> tuple:
    """
    create gmsh geometry
    """
    import gmsh

    gmsh_ids = []
    crack_ids = []

    def magnet_ids(f):
        Magnet = yaml.load(f, Loader=yaml.FullLoader)
        from importlib import import_module

        MyMagnet = import_module(import_dict[type(Magnet)], package="python_magnetgmsh")
        ids = MyMagnet.gmsh_ids(Magnet, (), debug)
        return ids

    if isinstance(Bitters.magnets, str):
        # print(f"Bitters/gmsh/{Bitters.magnets} (str)")
        with open(f"{Bitters.magnets}.yaml", "r") as f:
            ids = magnet_ids(f)
            gmsh_ids.append(ids[0])
            crack_ids.append(ids[1])

    elif isinstance(Bitters.magnets, list):
        for mname in Bitters.magnets:
            # print(f"Bitters/gmsh/{mname} (dict/list)")
            with open(f"{mname}.yaml", "r") as f:
                ids = magnet_ids(f)
                gmsh_ids.append(ids[0])
                crack_ids.append(ids[1])
                # print(f"ids[{mname}]: {ids} (type={type(ids)})")

    else:
        raise Exception(f"magnets: unsupported type {type(Bitters.magnets)}")

    if debug:
        print(f"Bitters/gmsh_ids: gmsh_ids={gmsh_ids}")
        print(f"Bitters/gmsh_ids: cracks: {crack_ids}")
    # Now create air
    Air_data = ()
    if AirData:
        ([r_min, r_max], [z_min, z_max]) = Bitters.boundingBox()
        r0_air = 0
        dr_air = abs(r_min - r_max) * AirData[0]
        z0_air = z_min * AirData[1]
        dz_air = abs(z_max - z_min) * AirData[1]
        A_id = gmsh.model.occ.addRectangle(r0_air, z0_air, 0, dr_air, dz_air)

        flat_list = []
        if debug:
            print("list:", gmsh_ids)
            print("flat_list:", len(gmsh_ids))
        for sublist in gmsh_ids:
            if not isinstance(sublist, list):
                raise Exception(
                    f"Bitters python_magnetmsh/gmsh: flat_list: expect a tuple got a {type(sublist)}"
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
        Air_data = (A_id, dr_air, z0_air, dz_air)

    # need to account for changes
    gmsh.model.occ.synchronize()
    return (gmsh_ids, crack_ids, Air_data)


def gmsh_bcs(Bitters, mname: str, ids: tuple, debug: bool = False) -> dict:
    """
    retreive ids for bcs in gmsh geometry
    """
    import gmsh

    (gmsh_ids, crack_ids, Air_data) = ids
    print("Bitters/gmsh_bcs:", ids)

    defs = {}
    bcs_defs = {}

    def load_defs(Magnet, name, ids):
        from importlib import import_module

        MyMagnet = import_module(import_dict[type(Magnet)], package="python_magnetgmsh")
        tdefs = MyMagnet.gmsh_bcs(Magnet, name, ids, debug)
        return tdefs

    if isinstance(Bitters.magnets, str):
        # print(f"Bitters/gmsh/{Bitters.magnets} (str)")
        with open(f"{Bitters.magnets}.yaml", "r") as f:
            Object = yaml.load(f, Loader=yaml.FullLoader)
        defs.update(load_defs(Object, "", ids))

    elif isinstance(Bitters.magnets, list):
        num = 0
        for i, mname in enumerate(Bitters.magnets):
            # print(f"Bitters/gmsh/{mname} (dict/list)")
            # print(f"gmsh_ids[{key}]: {gmsh_ids[num]}")
            with open(f"{mname}.yaml", "r") as f:
                Object = yaml.load(f, Loader=yaml.FullLoader)
            _ids = (gmsh_ids[num], crack_ids[num], ())
            defs.update(load_defs(Object, mname, _ids))
            num += 1

    return defs

