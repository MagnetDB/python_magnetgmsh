import gmsh

MeshAlgo2D = {
    "MeshAdapt": 1,
    "Automatic": 2,
    "Initial": 3,
    "Delaunay": 5,
    "Frontal-Delaunay": 6,
    "BAMG": 7,
}


def get_allowed_algo() -> list:
    """
    return allowed 2D algo
    """
    return list(MeshAlgo2D.keys())


def gmsh_msh(algo: str, lc: float, air: bool = False, scaling: bool = False):
    """
    create Axi msh

    TODO:
    - select algo
    - mesh characteristics
    - crack plugin for Bitter CoolingSlits
    """
    print("TODO: set characteristic lengths")

    Origin = gmsh.model.occ.addPoint(0, 0, 0, 0.1, 0)
    gmsh.model.occ.synchronize()

    # add Points
    EndPoints_tags = [Origin]

    # scaling
    unit = 1
    if scaling:
        unit = 0.001
        gmsh.option.setNumber("Geometry.OCCScaling", unit)

    print(f"Mesh Length Characteristics: lc={lc}")

    # Assign a mesh size to all the points:
    lcar1 = 5 * lc * unit
    gmsh.model.mesh.setSize(gmsh.model.getEntities(0), lcar1)

    """
    if "Air" in defs:
        gmsh.model.mesh.setSize(
            gmsh.model.getEntitiesForPhysicalGroup(0, defs["ZAxis"]), lc[1]
        )
        gmsh.model.mesh.setSize(
            gmsh.model.getEntitiesForPhysicalGroup(0, defs["Infty"]), lc[1]
        )
    """

    # LcMax -                         /------------------
    #                               /
    #                             /
    #                           /
    # LcMin -o----------------/
    #        |                |       |
    #      Point           DistMin DistMax
    # Field 1: Distance to electrodes

    if EndPoints_tags:
        gmsh.model.mesh.field.add("Distance", 1)
        gmsh.model.mesh.field.setNumbers(1, "NodesList", EndPoints_tags)

        # Field 2: Threshold that dictates the mesh size of the background field
        gmsh.model.mesh.field.add("Threshold", 2)
        gmsh.model.mesh.field.setNumber(2, "IField", 1)
        gmsh.model.mesh.field.setNumber(2, "LcMin", lcar1 / 20.0)
        gmsh.model.mesh.field.setNumber(2, "LcMax", lcar1)
        gmsh.model.mesh.field.setNumber(2, "DistMin", 5 * unit)
        gmsh.model.mesh.field.setNumber(2, "DistMax", 10 * unit)
        gmsh.model.mesh.field.setNumber(2, "StopAtDistMax", 15 * unit)
        gmsh.model.mesh.field.setAsBackgroundMesh(2)

    gmsh.option.setNumber("Mesh.Algorithm", MeshAlgo2D[algo])
    gmsh.model.mesh.generate(2)
    pass

