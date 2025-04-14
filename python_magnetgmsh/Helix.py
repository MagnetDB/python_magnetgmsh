#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
Provides definition for Helix:

* Geom data: r, z
* Model Axi: definition of helical cut (provided from MagnetTools)
* Model 3D: actual 3D CAD
* Shape: definition of Shape eventually added to the helical cut
"""
from python_magnetgeo.Chamfer import Chamfer
from python_magnetgeo.Helix import Helix

import gmsh
from .mesh.bcs import create_bcs

def gmsh_chamfer(r: float, z: float, chamfer: Chamfer, debug: bool = False) -> int:
    """
    create gmsh chamfer

    *___ *   *____*
    |   /     \   |
    |  /       \  |
    | /         \ |
    |/           \|
    *             *
    """

    side = chamfer.side # HP/BP
    rside = chamfer.rside # rint/rext
    alpha = chamfer.alpha
    L = float(chamfer.L)
    cradius = chamfer.getRadius()
    print(side, rside, alpha, L, cradius, r, z)
    
    contour = None
    if side == "BP": 
        P0 = gmsh.model.occ.addPoint(r, z, 0)
        P1 = gmsh.model.occ.addPoint(r, z -L, 0)
        if rside =="rext":
            P2 = gmsh.model.occ.addPoint(r - cradius, z, 0)
            P0P2 = gmsh.model.occ.addLine(P0, P2)
            P2P1 = gmsh.model.occ.addLine(P2, P1)
            P1P0 = gmsh.model.occ.addLine(P1, P0)
            contour = gmsh.model.occ.addCurveLoop([P0P2, P2P1, P1P0])
        else:
            P2 = gmsh.model.occ.addPoint(r + cradius, z, 0)
            P0P1 = gmsh.model.occ.addLine(P0, P1)
            P1P2 = gmsh.model.occ.addLine(P1, P2)
            P2P0 = gmsh.model.occ.addLine(P2, P0)
            contour = gmsh.model.occ.addCurveLoop([P0P1, P1P2, P2P0])    
    
    if side == "HP": 
        P0 = gmsh.model.occ.addPoint(r, z, 0)
        P1 = gmsh.model.occ.addPoint(r, z + L, 0)
        if rside == "rint":
            P2 = gmsh.model.occ.addPoint(r + cradius, z, 0)
            P0P1 = gmsh.model.occ.addLine(P0, P1)
            P1P2 = gmsh.model.occ.addLine(P1, P2)
            P2P0 = gmsh.model.occ.addLine(P2, P0)
            contour = gmsh.model.occ.addCurveLoop([P0P1, P1P2, P2P0])
        else:
            P2 = gmsh.model.occ.addPoint(r - cradius, z, 0)    
            P0P2 = gmsh.model.occ.addLine(P0, P2)
            P2P1 = gmsh.model.occ.addLine(P2, P1)
            P1P0 = gmsh.model.occ.addLine(P1, P0)
            contour = gmsh.model.occ.addCurveLoop([P0P2, P2P1, P1P0])
   
    gmsh.model.occ.synchronize()
    surf = gmsh.model.occ.addPlaneSurface([contour])
    print(f"gmsh_chamfer surf: {surf}", flush=True)
    return surf


def gmsh_ids(Helix: Helix, AirData: tuple, debug: bool = False) -> tuple:
    """
    create gmsh geometry
    """

    # TODO get axi model
    gmsh_ids = []
    x = Helix.r[0]
    dr = Helix.r[1] - Helix.r[0]
    y = -Helix.modelaxi.h

    # from Chamfers get HPChamfer and BPChamfer
    HPChamfers = [chamfer for chamfer in Helix.chamfers if chamfer.side == "HP"]
    BPChamfers = [chamfer for chamfer in Helix.chamfers if chamfer.side == "BP"]
    print(f"{Helix.name}: HPChamfers: {HPChamfers}")
    print(f"{Helix.name}: BPChamfers: {BPChamfers}")
    # Add chamfer on HP here
    if abs(y - Helix.z[0]) >= 0:
        _id = gmsh.model.occ.addRectangle(x, Helix.z[0], 0, dr, abs(y - Helix.z[0]))
        for chamfer in HPChamfers:
            if chamfer.rside == "rint":
                chamfer_id = gmsh_chamfer(Helix.r[0], Helix.z[0], chamfer, debug)
            else:
                chamfer_id = gmsh_chamfer(Helix.r[1], Helix.z[0], chamfer, debug)
            gmsh.model.occ.cut([(2, _id)], [(2, chamfer_id)], tag=-1, removeObject=True, removeTool=True)
            gmsh.model.occ.synchronize()
        gmsh_ids.append(_id)

    for i, (n, pitch) in enumerate(zip(Helix.modelaxi.turns, Helix.modelaxi.pitch)):
        dz = n * pitch
        _id = gmsh.model.occ.addRectangle(x, y, 0, dr, dz)
        gmsh_ids.append(_id)

        y += dz

    # Add chamfer on BP here
    if abs(Helix.z[1] - y) >= 0:
        _id = gmsh.model.occ.addRectangle(x, y, 0, dr, abs(Helix.z[1] - y))
        for chamfer in BPChamfers:
            if chamfer.rside == "rext":
                chamfer_id = gmsh_chamfer(Helix.r[1], Helix.z[1], chamfer, debug)
            else:
                chamfer_id = gmsh_chamfer(Helix.r[0], Helix.z[1], chamfer, debug)    
            gmsh.model.occ.cut([(2, _id)], [(2, chamfer_id)], tag=-1, removeObject=True, removeTool=True)
            gmsh.model.occ.synchronize()
        gmsh_ids.append(_id)
    if debug:
        gmsh.fltk.run()

    # Now create air
    if AirData:
        r0_air = 0
        dr_air = Helix.r[1] * AirData[0]
        z0_air = Helix.z[0] * AirData[1]
        dz_air = abs(Helix.z[0] - Helix.z[1]) * AirData[1]
        _id = gmsh.model.occ.addRectangle(r0_air, z0_air, 0, dr_air, dz_air)

        ov, ovv = gmsh.model.occ.fragment([(2, _id)], [(2, i) for i in gmsh_ids])
        gmsh.model.occ.synchronize()
        return (gmsh_ids, (_id, dr_air, z0_air, dz_air))

    if debug:
        print(f"Helix/gmsh_ids: {gmsh_ids} ({len(gmsh_ids)})")

    # need to account for changes
    gmsh.model.occ.synchronize()
    return (gmsh_ids, ())


def gmsh_bcs(Helix: Helix, mname: str, ids: tuple, debug: bool = False) -> dict:
    """
    retreive ids for bcs in gmsh geometry
    """
    # print(f"Helix/gmsh_ids: ids={ids}")
    defs = {}
    (H_ids, Air_data) = ids

    prefix = ""
    if mname:
        prefix = f"{mname}_"

    # set physical name
    for i, id in enumerate(H_ids):
        ps = gmsh.model.addPhysicalGroup(2, [id])
        gmsh.model.setPhysicalName(2, ps, f"{prefix}Cu{i}")
        defs[f"{prefix}Cu{i}"] = ps

    # get BC ids
    gmsh.option.setNumber("Geometry.OCCBoundsUseStl", 1)

    zmin = Helix.z[0]
    zmax = Helix.z[1]

    # add Constraints if Chamfers
    rint_range = [Helix.r[0], Helix.r[0]]
    rext_range = [Helix.r[1], Helix.r[1]]
    if Helix.chamfers:
        chamfer_rint = [Helix.r[0] + chamfer.getRadius() for chamfer in Helix.chamfers if chamfer.rside == "rint"]
        chamfer_rext = [Helix.r[1] - chamfer.getRadius() for chamfer in Helix.chamfers if chamfer.rside == "rext"]
        print(f"{Helix.name}: chamfer_rint: {chamfer_rint}")
        print(f"{Helix.name}: chamfer_rext: {chamfer_rext}")
    
        if chamfer_rint:
            rint_range = [Helix.r[0], max(chamfer_rint)]
        if chamfer_rext:
            rext_range = [min(chamfer_rext), Helix.r[1]]
    
    # if HPChamfer: r[0], r[0] + Chamfer.getRadius()
    # if BPChamfer: r[1] + Chamfer.getRadius(), r[1]
    bcs_defs = {
        f"{prefix}rInt": [rint_range[0], zmin, rint_range[1], zmax],
        f"{prefix}rExt": [rext_range[0], zmin, rext_range[1], zmax],
    }

    for key in bcs_defs:
        defs[key] = create_bcs(key, bcs_defs[key], 1)

    return defs
