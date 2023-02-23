#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from typing import Type, List, Union

import gmsh


def minmax(box: List[float], eps: float):
    rmin = box[0] * (1 - eps)
    if box[0] < 0:
        rmin = box[0] * (1 + eps)

    zmin = box[1] * (1 - eps)
    if box[1] < 0:
        zmin = box[1] * (1 + eps)

    rmax = box[2] * (1 + eps)
    if box[2] < 0:
        rmax = box[2] * (1 - eps)

    zmax = box[3] * (1 + eps)
    if box[3] < 0:
        zmax = box[3] * (1 - eps)

    # print(rmin, rmax, zmin, zmax)
    return (rmin, rmax, zmin, zmax)


def create_bcs(
    name: str,
    box: Union[List[float], List[List[float]]],
    dim: int = 1,
    eps: float = 1.0e-6,
):
    """
    """

    gmsh.model.occ.synchronize()
    ov = []
    if isinstance(box[0], float):
        (rmin, rmax, zmin, zmax) = minmax(box, eps)
        ov += gmsh.model.getEntitiesInBoundingBox(rmin, zmin, 0, rmax, zmax, 0, dim)
    else:
        for item in box:
            (rmin, rmax, zmin, zmax) = minmax(item, eps)
            gmsh.model.getEntitiesInBoundingBox(rmin, rmax, 0, zmin, zmax, 0, dim)

    ps = gmsh.model.addPhysicalGroup(1, [tag for (dim, tag) in ov])
    gmsh.model.setPhysicalName(1, ps, name)
    # print(f"create_bs: name={name}, box={box}, ps={ps}, ov={len(ov)}")

    if len(ov) == 0:
        print(f"create_bs: name={name}, box={box} no surface detected")
    return ps
