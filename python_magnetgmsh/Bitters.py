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


def gmsh_bcs(
    Bitters,
    mname: str,
    ids: tuple,
    thickslit: bool = False,
    skipR: bool = False,
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
        tdefs = MyMagnet.gmsh_bcs(Magnet, name, ids, thickslit, skipR, debug)
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

            Nslits = 0
            if Object.coolingslits:
                Nslits = len(Object.coolingslits)

            if i == 0:
                print(f"Bitters/gmsh/{mname} Bitter[{i}] rInt: {defs}")
                key = f"{prefix}{Object.name}_Slit0"
                bcs_def = [Object.r[0], Object.z[0], Object.r[0], Object.z[1]]
                defs[key] = create_bcs(key, bcs_def, 1)
                # print(f'{key}: bcs_def={defs[key]}')

                # print(f'Bitters rInt: defs={defs}')

            # add Bitter.magnets[i+1]_rInt + Bitter.magnets[i]_rExt -> Bitter.magnets[i]_slitN
            if i < len(Bitters.magnets) - 1:
                nmname = Bitters.magnets[i + 1]
                print(
                    f"Bitters/gmsh/{mname} Bitter[{i}] rExt {nmname} Bitter[{i+1}] rInt: {defs}"
                )
                with open(f"{nmname}.yaml", "r") as f:
                    nObject = yaml.load(f, Loader=yaml.FullLoader)
                    _nids = (gmsh_ids[num + 1], crack_ids[num + 1], ())

                    key = f"{prefix}{Object.name}_Slit{Nslits+1}"
                    bcs_def = [
                        [Object.r[1], Object.z[0], Object.r[1], Object.z[1]],
                        [nObject.r[0], nObject.z[0], nObject.r[0], nObject.z[1]],
                    ]
                    defs[key] = create_bcs(key, bcs_def, 1)
                    # print(f'{key}: bcs_def={defs[key]}')

                # print(f'Bitters rInt/rExt: defs={defs}')

            if i == len(Bitters.magnets) - 1:
                print(f"Bitters/gmsh/{mname} Bitter[{i}] rExt: {defs}")
                key = f"{prefix}{Object.name}_Slit{Nslits+1}"
                bcs_def = [Object.r[1], Object.z[0], Object.r[1], Object.z[1]]
                defs[key] = create_bcs(key, bcs_def, 1)
                # print(f'{key}: bcs_def={defs[key]}')
                # print(f'Bitters rExt: defs={defs}')

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
