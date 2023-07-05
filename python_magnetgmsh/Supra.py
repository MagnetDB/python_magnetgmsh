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

from .mesh.bcs import create_bcs
from .SupraStructure import insert_ids, insert_bcs


def gmsh_ids(
    Supra: Supra, AirData: tuple, Thickslit: bool = False, debug: bool = False
):
    """
    create gmsh geometry
    """
    print(f"gmsh_ids: Supra={Supra.name}")

    # TODO: how to specify detail level to actually connect gmsh with struct data
    # print(f"Supra/gmsh_ids: Supra={Supra}")

    if not Supra.struct:
        _id = gmsh.model.occ.addRectangle(
            Supra.r[0], Supra.z[0], 0, Supra.r[1] - Supra.r[0], Supra.z[1] - Supra.z[0]
        )

        # Now create air
        Air_data = ()
        if AirData:
            from .Air import gmsh_air

            (r0_air, z0_air, dr_air, dz_air) = gmsh_air(Supra, AirData)
            A_id = gmsh.model.occ.addRectangle(r0_air, z0_air, 0, dr_air, dz_air)

            ov, ovv = gmsh.model.occ.fragment([(2, A_id)], [(2, _id)])
            # need to account for changes
            gmsh.model.occ.synchronize()
            Air_data = (A_id, dr_air, z0_air, dz_air)

        return (_id, Air_data)
    else:
        # load struct
        nougat = HTSinsert.fromcfg(Supra.struct)

        # call gmsh for struct
        gmsh_ids = insert_ids(nougat, Supra.detail, AirData, debug)
        # need to account for changes
        
        return gmsh_ids


def gmsh_bcs(
    Supra: Supra, mname: str, ids: tuple, thickslit: bool = False, debug: bool = False
) -> dict:
    """
    retreive ids for bcs in gmsh geometry
    """
    print(f"gmsh_bcs: Supra={Supra.name}")

    defs = {}
    bcs_defs = {}

    prefix = ""
    if mname:
        prefix = f"{mname}_"

    # print(f"Supra: name={Supra.name}, struct={Supra.struct}")
    if not Supra.struct:
        (id, Air_data) = ids

        # set physical name
        psname = f"{prefix[0:len(prefix)-1]}"
        ps = gmsh.model.addPhysicalGroup(2, [id])
        gmsh.model.setPhysicalName(2, ps, psname)
        defs[psname] = ps
        # print(f"{Supra.name}: {id}")

        # get BC ids
        gmsh.option.setNumber("Geometry.OCCBoundsUseStl", 1)

        bcs_defs[f"{prefix}HP"] = [Supra.r[0], Supra.z[0], Supra.r[-1], Supra.z[0]]
        bcs_defs[f"{prefix}BP"] = [
            Supra.r[0],
            (Supra.z[-1]),
            Supra.r[-1],
            (Supra.z[-1]),
        ]
        bcs_defs[f"{prefix}Rint"] = [Supra.r[0], Supra.z[0], Supra.r[0], Supra.z[1]]
        bcs_defs[f"{prefix}Rext"] = [Supra.r[1], Supra.z[0], Supra.r[1], Supra.z[1]]

        # Air
        if Air_data:
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

    else:
        # load struct
        nougat = HTSinsert.fromcfg(Supra.struct)

        # call gmsh for struct
        defs = insert_bcs(nougat, mname, Supra.detail, ids, debug)

    for key in bcs_defs:
        defs[key] = create_bcs(key, bcs_defs[key], 1)

    return defs
