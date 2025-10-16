import re

from math import copysign
import gmsh
from ..MeshData import MeshData

MeshAlgo3D = {
    "Delaunay": 1,
    "Automatic": 2,
    "Initial": 3,
    "Frontal": 4,
    "MMG3D": 7,
    "R-tree": 9,
    "HXT": 10,
}


def get_allowed_algo() -> list:
    """
    return allowed 3D algo
    """
    return list(MeshAlgo3D.keys())


def get_algo(name: str):
    return MeshAlgo3D[name]


def gmsh_msh(
    algo: str,
    meshdata: MeshData,
    refinedboxes: list,
    air: bool = False,
    scaling: bool = False,
):
    """
    create Axi msh

    TODO:
    - select algo
    - mesh characteristics
    - crack plugin for Bitter CoolingSlits
    """

    meshdim = 3
    HXT_support = True
    print(f"create 3D Gmsh mesh ({algo})", flush=True)
    gmsh.option.setNumber("Mesh.Algorithm", 2)  # select Automatic 2D algo
    gmsh.option.setNumber("Mesh.Algorithm3D", MeshAlgo3D[algo])

    # scaling
    unit = 1
    if scaling:
        unit = 0.001
        gmsh.option.setNumber("Geometry.OCCScaling", unit)

    # TODO use mesh_dict to assign better lc to surfaces
    # Assign a mesh size to all the points:
    lcar1 = 80 * unit

    Origin = gmsh.model.occ.addPoint(0, 0, 0, lcar1)
    gmsh.model.occ.synchronize()

    # add Points
    EndPoints_tags = [Origin]

    gmsh.model.mesh.setSize(gmsh.model.getEntities(0), lcar1)

    # -clscale 0.01 Set mesh element size factor (Mesh.MeshSizeFactor)
    # -rand Set random perturbation factor (Mesh.RandomFactor)
    # -clcurv value Compute mesh element size from curvature, with value the target number of elements per 2*pi radians (Mesh.MeshSizeFromCurvature)
    gmsh.model.mesh.generate(meshdim)

    pass
