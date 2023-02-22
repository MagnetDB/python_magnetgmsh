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

    gmsh_ids = []
    x = Bitter.r[0]
    dr = Bitter.r[1] - Bitter.r[0]
    y = -Bitter.axi.h
    for i, (n, pitch) in enumerate(zip(Bitter.axi.turns, Bitter.axi.pitch)):
        dz = n * pitch
        _id = gmsh.model.occ.addRectangle(x, y, 0, dr, dz)
        # print(f"B[{i}]={_id}")
        gmsh_ids.append(_id)

        y += dz
    # print(f"gmsh_ids: {gmsh_ids}")

    # Cooling Channels
    if len(Bitter.coolingslits) > 0:
        slits = []
        # print(f"CoolingSlits[r]: {Bitter.coolingslits[0]['r']}")
        for r in Bitter.coolingslits[0]["r"]:
            x = float(r)
            pt1 = gmsh.model.occ.addPoint(x, Bitter.z[0], 0)
            pt2 = gmsh.model.occ.addPoint(x, Bitter.z[1], 0)
            _id = gmsh.model.occ.addLine(pt1, pt2)
            slits.append((1, _id))

        ngmsh_ids = []
        domain = []
        for i in gmsh_ids:
            domain.append((2, i))
        o, m = gmsh.model.occ.fragment(domain, slits)
        for j, entries in enumerate(m):
            _ids = []
            for id_tuple in entries:
                if id_tuple[0] == 2:
                    _ids.append(id_tuple[1])
            if _ids:
                ngmsh_ids.append(_ids)
        gmsh_ids = ngmsh_ids

        # need to account for changes
        gmsh.model.occ.synchronize()

    if debug:
        print(f"gmsh_ids: {gmsh_ids}")

    # Now create air
    if AirData:
        (r, z) = Bitter.boundingBox()
        r0_air = 0
        dr_air = r[1] * AirData[0]
        z0_air = z[0] * AirData[1]
        dz_air = abs(z[1] - z[0]) * AirData[1]
        _id = gmsh.model.occ.addRectangle(r0_air, z0_air, 0, dr_air, dz_air)

        ov, ovv = gmsh.model.occ.fragment(
            [(2, _id)], [(2, i) for i in flatten(gmsh_ids)]
        )
        gmsh.model.occ.synchronize()
        return (gmsh_ids, (_id, dr_air, z0_air, dz_air))

    gmsh.model.occ.synchronize()
    return (gmsh_ids, ())


def gmsh_bcs(Bitter: Bitter, mname: str, ids: tuple, debug: bool = False) -> dict:
    """
    retreive ids for bcs in gmsh geometry
    """

    defs = {}
    (B_ids, Air_data) = ids

    prefix = ""
    if mname:
        prefix = f"{mname}_"
    print(f"Bitter/gmsh_bcs: Bitter={Bitter.name}, prefix={prefix}")

    # set physical name
    if len(B_ids) == 1:
        psname = f"{prefix[0:len(prefix)-1]}"
        ps = gmsh.model.addPhysicalGroup(2, B_ids)
        gmsh.model.setPhysicalName(2, ps, psname)
        defs[psname] = ps
    else:
        for i, id in enumerate(B_ids):
            if isinstance(id, int):
                # print(f"B{i+1}: {id}")
                ps = gmsh.model.addPhysicalGroup(2, [id])
            else:
                # print(f"B{i+1}: {id}")
                ps = gmsh.model.addPhysicalGroup(2, id)
            psname = f"{prefix}B{i+1}"
            gmsh.model.setPhysicalName(2, ps, psname)
            defs[psname] = ps

    # get BC ids
    gmsh.option.setNumber("Geometry.OCCBoundsUseStl", 1)
    # TODO: if z[xx] < 0 multiply by 1+eps to get a min by 1-eps to get a max
    eps = 1.0e-3

    bcs_defs = {
        f"{prefix}HP": [
            Bitter.r[0] * (1 - eps),
            Bitter.z[0] * (1 + eps),
            Bitter.r[-1] * (1 + eps),
            Bitter.z[0] * (1 - eps),
        ],
        f"{prefix}BP": [
            Bitter.r[0] * (1 - eps),
            Bitter.z[-1] * (1 - eps),
            Bitter.r[-1] * (1 + eps),
            Bitter.z[-1] * (1 + eps),
        ],
        f"{prefix}Rint": [
            Bitter.r[0] * (1 - eps),
            Bitter.z[0] * (1 + eps),
            Bitter.r[0] * (1 + eps),
            Bitter.z[1] * (1 + eps),
        ],
        f"{prefix}Rext": [
            Bitter.r[1] * (1 - eps),
            Bitter.z[0] * (1 + eps),
            Bitter.r[1] * (1 + eps),
            Bitter.z[1] * (1 + eps),
        ],
    }
    # Cooling Channels
    if len(Bitter.coolingslits) > 0:
        # print(f"CoolingSlits[r]: {Bitter.coolingslits[0]['r']}")
        for i, r in enumerate(Bitter.coolingslits[0]["r"]):
            bcs_defs[f"{prefix}slit{i}"] = [
                r * (1 - eps),
                Bitter.z[0] * (1 + eps),
                r * (1 + eps),
                Bitter.z[1] * (1 + eps),
                1,
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

    for key in bcs_defs:
        defs[key] = create_bcs(key, bcs_defs[key], 1)

    return defs


def gmsh_msh(defs: dict, lc: list):
    """
    create msh

    TODO:
    - select algo
    - mesh characteristics
    - crack plugin for CoolingSlits
    """
    print("TODO: set characteristic lengths")

    Origin = gmsh.model.occ.addPoint(0, 0, 0, 0.1, 0)
    gmsh.model.occ.synchronize()
    gmsh.model.mesh.setSize(gmsh.model.getEntities(0), 10)
    gmsh.model.mesh.generate(2)
    pass


if __name__ == "__main__":
    import argparse
    import yaml

    parser = argparse.ArgumentParser()
    parser.add_argument("input_file")
    parser.add_argument("--debug", help="activate debug", action="store_true")
    parser.add_argument("--display", help="activate display", action="store_true")
    parser.add_argument("--mesh", help="perform mesh", action="store_true")
    args = parser.parse_args()

    # load Bitter
    with open(args.input_file, "r") as cfgdata:
        Object = yaml.load(cfgdata, Loader=yaml.FullLoader)

    gmsh.initialize()

    ids = gmsh_ids(Bitter=Object, AirData=(), debug=args.debug)
    if args.mesh:
        defs = gmsh_bcs(Bitter=Object, mname="", ids=ids, debug=args.debug)
        for key in defs:
            defs[key] = create_bcs(key, defs[key], 1)
        gmsh_msh(defs=defs, lc=[])

    # Creates  graphical user interface
    if args.display:
        gmsh.fltk.run()
    gmsh.finalize()
