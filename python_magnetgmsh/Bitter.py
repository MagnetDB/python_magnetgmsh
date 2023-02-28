#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from typing import List, Union

import gmsh
from python_magnetgeo.Bitter import Bitter
from .mesh.bcs import create_bcs


from .utils.lists import flatten


def gmsh_ids(Bitter: Bitter, AirData: tuple, debug: bool = False) -> tuple:
    """
    create gmsh geometry
    """
    print("Bitter/gmsh_ids")

    gmsh_ids = []
    gmsh_cracks = []

    coolingslit = False
    if len(Bitter.coolingslits) > 0:
        coolingslit = True

    x = Bitter.r[0]
    dr = Bitter.r[1] - Bitter.r[0]
    y = -Bitter.axi.h
    if Bitter.z[0] < y:
        _id = gmsh.model.occ.addRectangle(x, Bitter.z[0], 0, dr, abs(y - Bitter.z[0]))
        gmsh_ids.append(_id)

    for i, (n, pitch) in enumerate(zip(Bitter.axi.turns, Bitter.axi.pitch)):
        dz = n * pitch
        _id = gmsh.model.occ.addRectangle(x, y, 0, dr, dz)
        # print(f"B[{i}]={_id}")
        gmsh_ids.append(_id)
        y += dz

    if Bitter.z[1] > y:
        _id = gmsh.model.occ.addRectangle(x, y, 0, dr, abs(y - Bitter.z[1]))
        gmsh_ids.append(_id)

    # Cooling Channels
    if coolingslit:
        for i, slit in enumerate(Bitter.coolingslits):
            x = float(slit.r)
            pt1 = gmsh.model.occ.addPoint(x, Bitter.z[0], 0)
            pt2 = gmsh.model.occ.addPoint(x, Bitter.z[1], 0)
            _id = gmsh.model.occ.addLine(pt1, pt2)
            gmsh_cracks.append(_id)

        ngmsh_ids = []
        ngmsh_cracks = []
        domain = [(2, i) for i in gmsh_ids]
        cuts = [(1, i) for i in gmsh_cracks]
        o, m = gmsh.model.occ.fragment(domain, cuts)
        gmsh.model.occ.synchronize()

        for j, entries in enumerate(m):
            _ids = []
            _cracks = []
            for (dim, tag) in entries:
                if dim == 2:
                    _ids.append(tag)
                if dim == 1:
                    _cracks.append(tag)
            if _ids:
                ngmsh_ids.append(_ids)
            if _cracks:
                ngmsh_cracks.append(_cracks)

        gmsh_ids = ngmsh_ids
        gmsh_cracks = ngmsh_cracks

        # need to account for changes
        # gmsh.model.occ.synchronize()

    # if debug:
    print(f"gmsh_ids: {gmsh_ids}, gmsh_cracks: {gmsh_cracks}")

    # Now create air
    if AirData:
        from .Air import gmsh_air

        (r0_air, z0_air, dr_air, dz_air) = gmsh_air(Bitter, AirData)
        _id = gmsh.model.occ.addRectangle(r0_air, z0_air, 0, dr_air, dz_air)

        ov, ovv = gmsh.model.occ.fragment(
            [(2, _id)], [(2, i) for i in flatten(gmsh_ids)]
        )
        gmsh.model.occ.synchronize()
        return (gmsh_ids, gmsh_cracks, (_id, dr_air, z0_air, dz_air))

    # gmsh.model.occ.synchronize()
    return (gmsh_ids, gmsh_cracks, ())


def gmsh_bcs(Bitter: Bitter, mname: str, ids: tuple, debug: bool = False) -> dict:
    """
    retreive ids for bcs in gmsh geometry
    """

    defs = {}
    (B_ids, Cracks_ids, Air_data) = ids

    prefix = ""
    if mname:
        prefix = f"{mname}_"

    # set physical name
    if len(B_ids) == 1:
        print(B_ids)
        psname = f"{prefix[0:len(prefix)-1]}"
        if isinstance(B_ids[0], int):
            ps = gmsh.model.addPhysicalGroup(2, [B_ids[0]])
        else:
            ps = gmsh.model.addPhysicalGroup(2, B_ids[0])
        gmsh.model.setPhysicalName(2, ps, psname)
        defs[psname] = ps
    else:
        shift = 0
        if Bitter.z[0] != Bitter.axi.h:
            shift = 1
        for i, id in enumerate(B_ids):
            if isinstance(id, int):
                ps = gmsh.model.addPhysicalGroup(2, [id])
            else:
                ps = gmsh.model.addPhysicalGroup(2, id)
            psname = f"{prefix}B{i+shift}"
            gmsh.model.setPhysicalName(2, ps, psname)
            defs[psname] = ps

    # get BC ids
    gmsh.option.setNumber("Geometry.OCCBoundsUseStl", 1)

    bcs_defs = {
        f"{prefix}HP": [Bitter.r[0], Bitter.z[0], Bitter.r[-1], Bitter.z[0]],
        f"{prefix}BP": [Bitter.r[0], Bitter.z[-1], Bitter.r[-1], Bitter.z[-1]],
        f"{prefix}Rint": [Bitter.r[0], Bitter.z[0], Bitter.r[0], Bitter.z[1]],
        f"{prefix}Rext": [Bitter.r[1], Bitter.z[0], Bitter.r[1], Bitter.z[1]],
    }

    # Cooling Channels
    print(f"Cracks_ids={Cracks_ids}")
    if len(Cracks_ids) > 0:
        for i, id in enumerate(Cracks_ids):
            print(f"slit{i+1}: {id}")
            if isinstance(id, int):
                ps = gmsh.model.addPhysicalGroup(1, [id])
            else:
                ps = gmsh.model.addPhysicalGroup(1, id)
            psname = f"{prefix}slit{i+1}"
            gmsh.model.setPhysicalName(1, ps, psname)
            defs[psname] = ps

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

    return defs

