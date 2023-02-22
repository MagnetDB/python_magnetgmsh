#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
Provides definition for Screen:

* Geom data: r, z
"""
from python_magnetgeo.Screen import Screen

import gmsh
from .mesh.bcs import create_bcs


def gmsh_ids(Screen: Screen, AirData: tuple, debug: bool = False) -> tuple:
    """
    create gmsh geometry
    """

    _id = gmsh.model.occ.addRectangle(
        Screen.r[0],
        Screen.z[0],
        0,
        Screen.r[1] - Screen.r[0],
        Screen.z[1] - Screen.z[0],
    )

    # Now create air
    if AirData:
        r0_air = 0
        dr_air = Screen.r[1] * AirData[0]
        z0_air = Screen.z[0] * AirData[1]
        dz_air = (Screen.z[1] - Screen.z[0]) * AirData[1]
        A_id = gmsh.model.occ.addRectangle(r0_air, z0_air, 0, dr_air, dz_air)

        ov, ovv = gmsh.model.occ.fragment([(2, A_id)], [(2, _id)])
        # need to account for changes
        gmsh.model.occ.synchronize()
        return (_id, (A_id, dr_air, z0_air, dz_air))

    # need to account for changes
    gmsh.model.occ.synchronize()
    return (_id, None)


def gmsh_bcs(Screen: Screen, ids: tuple, debug: bool = False) -> dict:
    """
    retreive ids for bcs in gmsh geometry
    """

    defs = {}

    (id, Air_data) = ids

    # set physical name
    ps = gmsh.model.addPhysicalGroup(2, [id])
    gmsh.model.setPhysicalName(2, ps, "%s_S" % Screen.name)
    defs["%s_S" % Screen.name] = ps

    # get BC ids
    gmsh.option.setNumber("Geometry.OCCBoundsUseStl", 1)

    eps = 1.0e-3

    # TODO: if z[xx] < 0 multiply by 1+eps to get a min by 1-eps to get a max
    bcs_defs = {
        f"{Screen.name}_HP": [
            Screen.r[0] * (1 - eps),
            Screen.z[0] * (1 + eps),
            Screen.r[-1] * (1 + eps),
            Screen.z[0] * (1 - eps),
        ],
        f"{Screen.name}_BP": [
            Screen.r[0] * (1 - eps),
            Screen.z[-1] * (1 - eps),
            Screen.r[-1] * (1 + eps),
            Screen.z[-1] * (1 + eps),
        ],
        f"{Screen.name}_Rint": [
            Screen.r[0] * (1 - eps),
            Screen.z[0] * (1 + eps),
            Screen.r[0] * (1 + eps),
            Screen.z[1] * (1 + eps),
        ],
        f"{Screen.name}_Rext": [
            Screen.r[1] * (1 - eps),
            Screen.z[0] * (1 + eps),
            Screen.r[1] * (1 + eps),
            Screen.z[1] * (1 + eps),
        ],
    }

    # Air
    if Air_data:
        (Air_id, dr_air, z0_air, dz_air) = Air_data

        ps = gmsh.model.addPhysicalGroup(2, [Air_id])
        gmsh.model.setPhysicalName(2, ps, "Air")
        defs["Air"] = ps
        # TODO: Axis, Inf
        gmsh.option.setNumber("Geometry.OCCBoundsUseStl", 1)

        eps = 1.0e-6

        bcs_defs[f"ZAxis"] = [-eps, z0_air - eps, +eps, z0_air + dz_air + eps]
        bcs_defs[f"Infty"] = [
            [-eps, z0_air - eps, dr_air + eps, z0_air + eps],
            [dr_air - eps, z0_air - eps, dr_air + eps, z0_air + dz_air + eps],
            [-eps, z0_air + dz_air - eps, dr_air + eps, z0_air + dz_air + eps],
        ]

    for key in bcs_defs:
        defs[key] = create_bcs(key, bcs_defs[key], 1)

    return defs
