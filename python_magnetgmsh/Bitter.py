#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from typing import List, Union

import re
import gmsh
from python_magnetgeo.Bitter import Bitter
from .mesh.bcs import create_bcs


from .utils.lists import flatten


def gmsh_ids(
    Bitter: Bitter, AirData: tuple, thickslit: bool = False, debug: bool = False
) -> tuple:
    """
    create gmsh geometry

    thickslit: boolean, True for Thickslit else False

    """
    print(f"gmsh_ids: Bitter={Bitter.name}, thickslit={thickslit}")

    gmsh_ids = []
    gmsh_cracks = []

    coolingslit = False
    if not Bitter.coolingslits is None:
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
        ngmsh_ids = []
        ngmsh_cracks = []

        if not thickslit:
            for i, slit in enumerate(Bitter.coolingslits):
                x = float(slit.r)
                pt1 = gmsh.model.occ.addPoint(x, Bitter.z[0], 0)
                pt2 = gmsh.model.occ.addPoint(x, Bitter.z[1], 0)
                _id = gmsh.model.occ.addLine(pt1, pt2)
                gmsh_cracks.append(_id)

            domain = [(2, i) for i in gmsh_ids]
            cuts = [(1, i) for i in gmsh_cracks]
            o, m = gmsh.model.occ.fragment(domain, cuts)
            gmsh.model.occ.synchronize()

        else:
            gmsh_slits = []
            for i, slit in enumerate(Bitter.coolingslits):
                # eps: thickness of annular ring equivalent to n * coolingslit surface
                x = slit.r
                eps = Bitter.equivalent_eps(i)
                print(f"slit[{i}]: eps={eps}")

                _id = gmsh.model.occ.addRectangle(
                    x - eps / 2.0, Bitter.z[0], 0, eps, abs(Bitter.z[1] - Bitter.z[0])
                )
                gmsh_slits.append(_id)

            o, m = gmsh.model.occ.cut(
                [(2, _id) for _id in gmsh_ids],
                [(2, _id) for _id in gmsh_slits],
                removeTool=True,
            )

        for j, entries in enumerate(m):
            _ids = []
            _cracks = []
            for dim, tag in entries:
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

        # gmsh_ids: shall become a list of list
        # replace: for each id in gmsh_ids: id by a list from cad output

        gmsh.model.occ.synchronize()
        # gmsh.fltk.run()
        # raise RuntimeError("finite thickness not implemented")

        # need to account for changes
        # gmsh.model.occ.synchronize()

    if debug:
        print(f"gmsh_ids: {gmsh_ids}, gmsh_cracks: {gmsh_cracks}")

    # Now create air
    Air_data = ()
    if AirData:
        from .Air import gmsh_air

        (r0_air, z0_air, dr_air, dz_air) = gmsh_air(Bitter, AirData)
        _id = gmsh.model.occ.addRectangle(r0_air, z0_air, 0, dr_air, dz_air)

        ov, ovv = gmsh.model.occ.fragment(
            [(2, _id)], [(2, i) for i in flatten(gmsh_ids)]
        )
        Air_data = (_id, dr_air, z0_air, dz_air)

    # gmsh.model.occ.synchronize()
    gmsh.model.occ.synchronize()
    return (gmsh_ids, gmsh_cracks, Air_data)


def gmsh_bcs(
    Bitter: Bitter,
    mname: str,
    ids: tuple,
    thickslit: bool = False,
    skipR: bool = False,
    debug: bool = False,
) -> dict:
    """
    retreive ids for bcs in gmsh geometry
    """
    print(f"gmsh_bcs: Bitter={Bitter.name}, mname={mname}, thickslit={thickslit}")

    coolingslit = False
    if Bitter.coolingslits:
        coolingslit = True

    defs = {}
    (B_ids, Cracks_ids, Air_data) = ids

    psnames = Bitter.get_names(mname, is2D=True, verbose=debug)
    print(f"Bitter: mname={mname}, psnames={psnames}")
    prefix = ""
    if mname:
        prefix = f"{mname}_"

    # set physical name
    num = 0
    for i, id in enumerate(B_ids):
        if isinstance(id, int):
            ps = gmsh.model.addPhysicalGroup(2, [id])
        else:
            ps = gmsh.model.addPhysicalGroup(2, id)

        psname = re.sub(r"_Slit\d+", "", psnames[num])
        print(
            f"Bitter[{i}]: id={id}, mname={mname}, psnames[{num}]={psnames[num]}, psname={psname} / {len(B_ids)}"
        )
        gmsh.model.setPhysicalName(2, ps, psname)
        defs[psname] = ps

        if isinstance(id, int):
            num += 1
        else:
            num += len(id) - 1

    # get BC ids
    gmsh.option.setNumber("Geometry.OCCBoundsUseStl", 1)

    bcs_defs = {
        f"{prefix}HP": [Bitter.r[0], Bitter.z[0], Bitter.r[-1], Bitter.z[0]],
        f"{prefix}BP": [Bitter.r[0], Bitter.z[-1], Bitter.r[-1], Bitter.z[-1]],
    }

    n_slits = 0
    if not Bitter.coolingslits is None:
        n_slits = len(Bitter.coolingslits)

    bcs_defs[f"{prefix}Slit0"] = [Bitter.r[0], Bitter.z[0], Bitter.r[0], Bitter.z[1]]

    # Cooling Channels
    if not Bitter.coolingslits is None:
        print(f"Cracks_ids={Cracks_ids}")
        if len(Cracks_ids) > 0:
            for i, id in enumerate(Cracks_ids):
                print(f"Slit{i+1}: {id}")
                if isinstance(id, int):
                    ps = gmsh.model.addPhysicalGroup(1, [id])
                else:
                    ps = gmsh.model.addPhysicalGroup(1, id)
                psname = f"{prefix}Slit{i+1}"
                gmsh.model.setPhysicalName(1, ps, psname)
                defs[psname] = ps
        else:
            for i, slit in enumerate(Bitter.coolingslits):
                sname = f"{prefix}Slit{i+1}"
                x = slit.r
                eps = Bitter.equivalent_eps(i)
                bcs_defs[sname] = [
                    [x - eps / 2.0, Bitter.z[0], x + eps / 2.0, Bitter.z[1]]
                ]
                print(f"add {sname} to bcs_defs")

    bcs_defs[f"{prefix}Slit{n_slits+1}"] = [
        Bitter.r[1],
        Bitter.z[0],
        Bitter.r[1],
        Bitter.z[1],
    ]

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
