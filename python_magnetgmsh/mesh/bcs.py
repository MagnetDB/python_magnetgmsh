#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from typing import List, Union

import gmsh


def create_bcs(name: str, box: Union[List[float], List[List[float]]], dim: int = 1):
    """
    """

    gmsh.model.occ.synchronize()
    ov = []
    if isinstance(box[0], float) or isinstance(box[0], int):
        ov += gmsh.model.getEntitiesInBoundingBox(
            box[0], box[1], 0, box[2], box[3], 0, dim
        )
    else:
        for item in box:
            ov += gmsh.model.getEntitiesInBoundingBox(
                item[0], item[1], 0, item[2], item[3], 0, dim
            )

    ps = gmsh.model.addPhysicalGroup(1, [tag for (dim, tag) in ov])
    gmsh.model.setPhysicalName(1, ps, name)
    # print(f"create_bs: name={name}, box={box}, ps={ps}, ov={len(ov)}")

    if len(ov) == 0:
        print(f"create_bs: name={name}, box={box} no surface detected")
    return ps
