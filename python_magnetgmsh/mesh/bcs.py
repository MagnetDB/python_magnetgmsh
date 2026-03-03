#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import gmsh
from ..logging_config import get_logger

logger = get_logger(__name__)


def minmax(box: list[float], eps: float):
    """
    minmax:  add tolerance to Axi bounding box

    box: boundingbox as a list [rmin, zmin, rmax, zmax]
    eps: tolerance
    """

    rmin = box[0] * (1 - eps)
    if box[0] < 0:
        rmin = box[0] * (1 + eps)
    if box[0] == 0:
        rmin = -eps

    zmin = box[1] * (1 - eps)
    if box[1] < 0:
        zmin = box[1] * (1 + eps)
    if box[1] == 0:
        zmin = -eps

    rmax = box[2] * (1 + eps)
    if box[2] < 0:
        rmax = box[2] * (1 - eps)
    if box[2] == 0:
        rmax = eps

    zmax = box[3] * (1 + eps)
    if box[3] < 0:
        zmax = box[3] * (1 - eps)
    if box[3] == 0:
        zmax = eps

    # print(rmin, rmax, zmin, zmax)
    return (rmin, rmax, zmin, zmax)


def create_bcs(name: str, box: list, dim: int = 1, eps: float = 1.0e-6):
    """
    create BCs for name

    name:
    box:
    dim:
    eps:
    """

    print(f"create BCs for {name}", flush=True)

    gmsh.model.occ.synchronize()
    ov = []
    if isinstance(box[0], float) or isinstance(box[0], int):
        (rmin, rmax, zmin, zmax) = minmax(box, eps)
        ov += gmsh.model.getEntitiesInBoundingBox(rmin, zmin, 0, rmax, zmax, 0, dim)
    else:
        for item in box:
            # print(f'create_bcs: item={item}')
            (rmin, rmax, zmin, zmax) = minmax(item, eps)
            _ov = gmsh.model.getEntitiesInBoundingBox(rmin, zmin, 0, rmax, zmax, 0, dim)
            if len(_ov) == 0:
                print(f"create_bs: name={name}, item={item} no surface detected")
                print(f"minmax: {(rmin, rmax, zmin, zmax)}")
            # print(f'create_bcs: _ov={_ov}')
            ov += _ov
            # print(f'create_bcs: ov={ov}')

    ps = gmsh.model.addPhysicalGroup(1, [tag for (dim, tag) in ov])
    gmsh.model.setPhysicalName(1, ps, name)
    # print(f"create_bs: name={name}, box={box}, ps={ps}, ov={len(ov)}")

    if len(ov) == 0:
        print(f"create_bs: name={name}, box={box} no surface detected")
    return ps
