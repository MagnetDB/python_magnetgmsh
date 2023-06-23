#!/usr/bin/env python3
# encoding: UTF-8

"""defines Insert structure"""
from typing import List

import yaml
from python_magnetgeo.Insert import Insert

import gmsh
from .Helix import gmsh_ids as helix_ids
from .Helix import gmsh_bcs as helix_bcs
from .Ring import gmsh_ids as ring_ids
from .Ring import gmsh_bcs as ring_bcs

from .mesh.bcs import create_bcs
from .utils.lists import flatten


def gmsh_ids(
    Insert: Insert, AirData: tuple, Thickslit: bool = False, debug: bool = False
) -> tuple:
    """
    create gmsh geometry
    """
    print(f"gmsh_ids: Insert={Insert.name}")

    gmsh_ids = ()

    # loop over Helices
    z = []
    H_ids = []
    for i, name in enumerate(Insert.Helices):
        with open(f"{name}.yaml", "r") as f:
            Helix = yaml.load(f, Loader=yaml.FullLoader)

        _ids = helix_ids(Helix, (), debug)
        if i % 2 == 0:
            z.append(Helix.z[1])
        else:
            z.append(Helix.z[0])
        H_ids.append(_ids[0])

    # loop over Rings
    R_ids = []
    for i, name in enumerate(Insert.Rings):
        with open(f"{name}.yaml", "r") as f:
            Ring = yaml.load(f, Loader=yaml.FullLoader)

        y = z[i]
        if i % 2 != 0:
            y -= Ring.z[-1] - Ring.z[0]

        _id = ring_ids(Ring, y, debug)
        R_ids.append(_id)
        # fragment
        if i % 2 != 0:
            ov, ovv = gmsh.model.occ.fragment(
                [(2, _id)], [(2, H_ids[i][0]), (2, H_ids[i + 1][0])]
            )
        else:
            ov, ovv = gmsh.model.occ.fragment(
                [(2, _id)], [(2, H_ids[i][-1]), (2, H_ids[i + 1][-1])]
            )
        gmsh.model.occ.synchronize()

        if debug:
            print(
                f"Insert/Ring[{i}]: R_id={_id}, fragment produced volumes: {len(ov)}, {len(ovv)}"
            )
            for e in ov:
                print(e)

    # Now create air
    Air_data = ()
    if AirData:
        (r, z) = Insert.boundingBox()
        # print(f"Insert: boundingbox= r={r}, z={z}")
        r0_air = 0
        dr_air = r[1] * AirData[0]
        z0_air = z[0] * AirData[1]
        dz_air = abs(z[1] - z[0]) * AirData[1]
        _id = gmsh.model.occ.addRectangle(r0_air, z0_air, 0, dr_air, dz_air)

        flat_list = flatten(H_ids)
        flat_list += R_ids

        ov, ovv = gmsh.model.occ.fragment([(2, _id)], [(2, i) for i in flat_list])

        # need to account for changes
        Air_data = (_id, dr_air, z0_air, dz_air)

    # TODO return ids
    # need to account for changes
    gmsh.model.occ.synchronize()
    return (H_ids, R_ids, Air_data)


def gmsh_bcs(
    Insert: Insert,
    mname: str,
    ids: tuple,
    thickslit: bool = False,
    skipR: bool = False,
    debug: bool = False,
) -> dict:
    """
    retreive ids for bcs in gmsh geometry
    """
    print(f"gmsh_bcs: Insert={Insert.name}")

    (H_ids, R_ids, AirData) = ids
    # print(f"Insert/gmsh_bcs: H_ids={H_ids}")

    defs = {}
    bcs_defs = {}

    prefix = ""
    if mname:
        prefix = f"{mname}_"
    psnames = Insert.get_names(mname, is2D=True, verbose=debug)

    # loop over Helices
    z = []
    H_Bc_ids = []
    NHelices = len(Insert.Helices)
    num = 0
    for i, name in enumerate(Insert.Helices):
        Helix = None
        with open(f"{name}.yaml", "r") as f:
            Helix = yaml.load(f, Loader=yaml.FullLoader)

        hname = psnames[num].replace("_Cu0", "")
        hdefs = helix_bcs(Helix, hname, (H_ids[i], ()), debug)
        if i % 2 == 0:
            z.append(Helix.z[1])
        else:
            z.append(Helix.z[0])
        defs.update(hdefs)

        if i == 0:
            bcs_defs[f"{hname}_BP"] = [
                Helix.r[0],
                Helix.z[0],
                Helix.r[1],
                Helix.z[0],
            ]
        if i == NHelices - 1:
            bcs_defs[f"{hname}_BP"] = [Helix.r[0], Helix.z[0], Helix.r[1], Helix.z[0]]

        num += len(Helix.axi.turns) + 2

    # loop over Rings
    R_Bc_ids = []
    NRings = len(Insert.Rings)
    for i, name in enumerate(Insert.Rings):
        Ring = None
        with open(f"{name}.yaml", "r") as f:
            Ring = yaml.load(f, Loader=yaml.FullLoader)

        y = z[i]
        if i % 2 != 0:
            y -= Ring.z[-1] - Ring.z[0]

        rname = psnames[num]
        rdefs = ring_bcs(Ring, rname, (i % 2 != 0), y, R_ids[i], debug)
        defs.update(rdefs)
        num += 1

    if AirData:
        (Air_id, dr_air, z0_air, dz_air) = AirData

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

    # Group bcs by Channels
    Channels = Insert.get_channels(mname, False, debug)
    for i, channel in enumerate(Channels):
        tags = []
        for bc in channel:
            if bc in defs:
                # print(f"{bc}: {defs[bc]}")
                vEntities = gmsh.model.getEntitiesForPhysicalGroup(1, defs[bc])
                # print(f"{bc}: vEntites={type(vEntities)}, tolist={vEntities.tolist()}")
                tags += vEntities.tolist()
        # print(f"{channel}: {tags}")
        ps = gmsh.model.addPhysicalGroup(1, tags)
        gmsh.model.setPhysicalName(1, ps, f"{prefix}Channel{i}")
        defs[f"{prefix}Channel{i}"] = ps

        for bc in channel:
            if bc in defs:
                gmsh.model.removePhysicalGroups([(1, defs[bc])])
                del defs[bc]

    return defs
