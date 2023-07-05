#!/usr/bin/env python3
# encoding: UTF-8

"""defines Bitter Insert structure"""
import yaml

from python_magnetgeo.Bitter import Bitter
from python_magnetgeo.Bitters import Bitters
from .utils.lists import flatten
from .mesh.bcs import create_bcs

import_dict = {Bitter: ".Bitter"}


def gmsh_ids(
    Bitters: Bitters, AirData: tuple, thickslit: bool = False, debug: bool = False
) -> tuple:
    """
    create gmsh geometry
    """
    import gmsh

    print(f"gmsh_ids: Bitters={Bitters.name}, thickslit={thickslit}")
    gmsh_ids = []
    crack_ids = []

    def magnet_ids(f):
        Magnet = yaml.load(f, Loader=yaml.FullLoader)
        from importlib import import_module

        MyMagnet = import_module(import_dict[type(Magnet)], package="python_magnetgmsh")
        ids = MyMagnet.gmsh_ids(Magnet, (), thickslit, debug)
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
        dr_air = r_max * AirData[0]
        z0_air = z_min * AirData[1]
        dz_air = abs(z_max - z_min) * AirData[1]
        A_id = gmsh.model.occ.addRectangle(r0_air, z0_air, 0, dr_air, dz_air)

        flat_list = flatten(gmsh_ids)
        print(f'flat_list: {flat_list}')

        ov, ovv = gmsh.model.occ.fragment(
            [(2, A_id)], [(2, j) for j in flat_list]
        )
        """
        print(f'Air fragment map: A_id={A_id}')
        print("fragment produced surfaces:")
        for e in ov:
            print(e)
        # ovv contains the parent-child relationships for all the input entities:
        print("before/after fragment relations:")
        for e in zip([(2, A_id)] + [(2, j) for j in flat_list], ovv):
            print("parent " + str(e[0]) + " -> child " + str(e[1]))
        """
        
        gmsh.model.occ.synchronize()
        Air_data = (A_id, dr_air, z0_air, dz_air)

    return (gmsh_ids, crack_ids, Air_data)


def gmsh_bcs(
    Bitters,
    mname: str,
    ids: tuple,
    thickslit: bool = False,
    debug: bool = False,
) -> dict:
    """
    retreive ids for bcs in gmsh geometry
    """
    import gmsh

    print(f"gmsh_bcs: Bitters={Bitters.name}, mname={mname}, thickslit={thickslit}")
    (gmsh_ids, crack_ids, Air_data) = ids
    # print("Bitters/gmsh_bcs:", ids)

    prefix = ""
    if mname:
        prefix = f"{mname}_"

    defs = {}
    bcs_defs = {}

    def load_defs(Magnet, name, ids):
        from importlib import import_module

        MyMagnet = import_module(import_dict[type(Magnet)], package="python_magnetgmsh")
        tdefs = MyMagnet.gmsh_bcs(Magnet, name, ids, thickslit, debug)
        return tdefs

    if isinstance(Bitters.magnets, str):
        print(f"Bitters/gmsh/{Bitters.magnets} (str)")
        with open(f"{Bitters.magnets}.yaml", "r") as f:
            Object = yaml.load(f, Loader=yaml.FullLoader)
        defs.update(load_defs(Object, f"{prefix}{Object.name}", ids))

    elif isinstance(Bitters.magnets, list):
        print(f"Bitters/gmsh/{Bitters.magnets} (list)")
        num = 0
        for i, mname in enumerate(Bitters.magnets):
            print(f"Bitters/gmsh/{mname} Bitter[{i}]: {gmsh_ids[num]}")
            with open(f"{mname}.yaml", "r") as f:
                Object = yaml.load(f, Loader=yaml.FullLoader)
            _ids = (gmsh_ids[num], crack_ids[num], ())
            defs.update(load_defs(Object, f"{prefix}{Object.name}", _ids))

            num += 1

    print(f"Bitters: defs={defs.keys()}")

    # Air
    if Air_data:
        if debug:
            print(f"Air_data={Air_data}")
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

    gmsh.model.occ.synchronize()

    return defs
