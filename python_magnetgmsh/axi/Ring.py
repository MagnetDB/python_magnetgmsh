#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
Provides definition for Ring:

"""
from python_magnetgeo.Ring import Ring
import gmsh
from ..mesh.bcs import create_bcs


def gmsh_ids(Ring: Ring, y: float, debug: bool = False) -> int:
    """
    create gmsh geometry
    """

    _id = gmsh.model.occ.addRectangle(
        Ring.r[0], y + Ring.z[0], 0, Ring.r[-1] - Ring.r[0], Ring.z[-1] - Ring.z[0]
    )
    # print("gmsh/Ring:", _id, Ring.name, Ring.r, Ring.z)

    # need to account for changes
    gmsh.model.occ.synchronize()
    return _id


def gmsh_bcs(Ring: Ring, mname: str, hp: bool, y: float, id: int, debug: bool = False) -> dict:
    """
    create gmsh geometry
    """
    prefix = ""
    if mname:
        prefix = f"{mname}_"

    defs = {}
    ps = gmsh.model.addPhysicalGroup(2, [id])
    if mname:
        gmsh.model.setPhysicalName(2, ps, mname)
        defs[f"{mname}"] = ps
    else:
        gmsh.model.setPhysicalName(2, ps, Ring.name)
        defs[f"{Ring.name}"] = ps

    # get BC (TODO review to keep on BP or HP)
    gmsh.option.setNumber("Geometry.OCCBoundsUseStl", 1)

    bcs_defs = {}
    if hp:
        bcs_defs[f"{prefix}HP"] = [
            Ring.r[0],
            (y + Ring.z[0]),
            Ring.r[-1],
            (y + Ring.z[0]),
        ]
        bcs_defs[f"{prefix}R0n"] = [
            Ring.r[0],
            (y + Ring.z[0]),
            Ring.r[0],
            (y + Ring.z[1]),
        ]

        bcs_defs[f"{prefix}R1n"] = [
            Ring.r[-1],
            (y + Ring.z[0]),
            Ring.r[-1],
            (y + Ring.z[1]),
        ]

        # TODO cooling
        bcs_defs[f"{prefix}CoolingSlits"] = [
            Ring.r[1],
            (y + Ring.z[0]),
            Ring.r[2],
            (y + Ring.z[-1]),
        ]
    else:
        bcs_defs[f"{prefix}BP"] = [
            Ring.r[0],
            (y + Ring.z[1]),
            Ring.r[-1],
            (y + Ring.z[1]),
        ]

        bcs_defs[f"{prefix}R0n"] = [
            Ring.r[0],
            (y + Ring.z[0]),
            Ring.r[0],
            (y + Ring.z[1]),
        ]

        bcs_defs[f"{prefix}R1n"] = [
            Ring.r[-1],
            (y + Ring.z[0]),
            Ring.r[-1],
            (y + Ring.z[1]),
        ]

        # TODO cooling
        bcs_defs[f"{prefix}CoolingSlits"] = [
            Ring.r[1],
            (y + Ring.z[0]),
            Ring.r[2],
            (y + Ring.z[-1]),
        ]

    for key in bcs_defs:
        defs[key] = create_bcs(key, bcs_defs[key], 1)

    return defs
