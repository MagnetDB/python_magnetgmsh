#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
Provides definition for Supra:

* Geom data: r, z
* Model Axi: definition of helical cut (provided from MagnetTools)
* Model 3D: actual 3D CAD
"""

import gmsh

from python_magnetgeo.Supra import Supra
from python_magnetgeo.SupraStructure import HTSinsert

from .bcs import create_bcs
from .SupraStructure import insert_ids, insert_bcs


def gmsh_ids(Supra: Supra, AirData: tuple, debug: bool = False):
    """
    create gmsh geometry
    """

    # TODO: how to specify detail level to actually connect gmsh with struct data
    # print(f"Supra/gmsh_ids: Supra={Supra}")

    if not Supra.struct:
        _id = gmsh.model.occ.addRectangle(
            Supra.r[0], Supra.z[0], 0, Supra.r[1] - Supra.r[0], Supra.z[1] - Supra.z[0]
        )

        # Now create air
        if AirData:
            r0_air = 0
            dr_air = Supra.r[1] * AirData[0]
            z0_air = Supra.z[0] * AirData[1]
            dz_air = (Supra.z[1] - Supra.z[0]) * AirData[1]
            A_id = gmsh.model.occ.addRectangle(r0_air, z0_air, 0, dr_air, dz_air)

            ov, ovv = gmsh.model.occ.fragment([(2, A_id)], [(2, _id)])
            # need to account for changes
            gmsh.model.occ.synchronize()
            return (_id, (A_id, dr_air, z0_air, dz_air))

        # need to account for changes
        gmsh.model.occ.synchronize()
        return (_id, ())
    else:
        # load struct
        nougat = HTSinsert.fromcfg(Supra.struct)

        # call gmsh for struct
        gmsh_ids = insert_ids(nougat, Supra.detail, AirData, debug)
        # need to account for changes
        gmsh.model.occ.synchronize()
        return gmsh_ids


def gmsh_bcs(Supra: Supra, mname: str, ids: tuple, debug: bool = False) -> dict:
    """
    retreive ids for bcs in gmsh geometry
    """

    defs = {}
    bcs_defs = {}

    prefix = ""
    if mname:
        prefix = f"{mname}_"

    # print(f"Supra: name={Supra.name}, struct={Supra.struct}")
    if not Supra.struct:

        (id, Air_data) = ids

        # set physical name
        ps = gmsh.model.addPhysicalGroup(2, [id])
        gmsh.model.setPhysicalName(2, ps, f"{Supra.name}")
        defs[f"{Supra.name}"] = ps
        # print(f"{Supra.name}: {id}")

        # get BC ids
        gmsh.option.setNumber("Geometry.OCCBoundsUseStl", 1)

        eps = 1.0e-3

        # TODO: if z[xx] < 0 multiply by 1+eps to get a min by 1-eps to get a max

        bcs_defs[f"{prefix}HP"] = [
            Supra.r[0] * (1 - eps),
            Supra.z[0] * (1 + eps),
            Supra.r[-1] * (1 + eps),
            Supra.z[0] * (1 - eps),
        ]
        bcs_defs[f"{prefix}BP"] = [
            Supra.r[0] * (1 - eps),
            (Supra.z[-1]) * (1 - eps),
            Supra.r[-1] * (1 + eps),
            (Supra.z[-1]) * (1 + eps),
        ]
        bcs_defs[f"{prefix}Rint"] = [
            Supra.r[0] * (1 - eps),
            Supra.z[0] * (1 + eps),
            Supra.r[0] * (1 + eps),
            Supra.z[1] * (1 + eps),
        ]
        bcs_defs[f"{prefix}Rext"] = [
            Supra.r[1] * (1 - eps),
            Supra.z[0] * (1 + eps),
            Supra.r[1] * (1 + eps),
            Supra.z[1] * (1 + eps),
        ]

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

    else:
        # load struct
        nougat = HTSinsert.fromcfg(Supra.struct)

        # call gmsh for struct
        defs = insert_bcs(nougat, mname, Supra.detail, ids, debug)

    for key in bcs_defs:
        defs[key] = create_bcs(key, bcs_defs[key], 1)

    return defs
