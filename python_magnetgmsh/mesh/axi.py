import gmsh

MeshAlgo2D = {
    "MeshAdapt": 1,
    "Automatic": 2,
    "Initial": 3,
    "Delaunay": 5,
    "Frontal-Delaunay": 6,
    "BAMG": 7,
}

from ..MeshAxiData import MeshAxiData


def get_allowed_algo() -> list:
    """
    return allowed 2D algo
    """
    return list(MeshAlgo2D.keys())


def get_algo(name: str):
    return MeshAlgo2D[name]


def gmsh_msh(
    algo: str, meshdata: MeshAxiData, air: bool = False, scaling: bool = False
):
    """
    create Axi msh

    TODO:
    - select algo
    - mesh characteristics
    - crack plugin for Bitter CoolingSlits
    """
    print("create Axi Gmsh")

    # scaling
    unit = 1
    if scaling:
        unit = 0.001
        gmsh.option.setNumber("Geometry.OCCScaling", unit)

    # Assign a mesh size to all the points:
    lcar1 = 40 * unit
    gmsh.model.mesh.setSize(gmsh.model.getEntities(0), lcar1)

    mesh_dict = meshdata.mesh_dict
    lcs = meshdata.surfhypoths
    cracks = {}

    # get ov and lc per PhysicalSurface
    lc_data = {}
    vGroups = gmsh.model.getPhysicalGroups()
    for iGroup in vGroups:
        dimGroup = iGroup[0]  # 1D, 2D or 3D
        tagGroup = iGroup[1]
        namGroup = gmsh.model.getPhysicalName(dimGroup, tagGroup)
        if namGroup in mesh_dict:
            def_lcs = mesh_dict[namGroup]
            if isinstance(def_lcs, int):
                lc = lcs[def_lcs]
            else:
                lc = lcs[def_lcs[0]][def_lcs[1]]

            vEntities = gmsh.model.getEntitiesForPhysicalGroup(dimGroup, tagGroup)
            ov = []
            for entity in vEntities:
                (xmin, ymin, zmin, xmax, ymax, zmax) = gmsh.model.getBoundingBox(
                    2, entity
                )
                _ov = gmsh.model.getEntitiesInBoundingBox(
                    xmin, ymin, zmin, xmax, ymax, zmax, 0
                )
                ov += _ov
            lc_data[namGroup] = (ov, lc)

        if "slit" in namGroup:
            print(f"{namGroup}: Bitter cooling slit tag={tagGroup}")
            cracks[namGroup] = tagGroup
        """
        else:
            print(f"{namGroup} not in mesh_dict")
        """

    # Apply lc in reverse order to get nice mesh
    for key in reversed(lc_data):
        (ov, lc) = lc_data[key]
        # print(f"{key}: {lc}")
        gmsh.model.mesh.setSize(ov, lc)

    # LcMax -                         /------------------
    #                               /
    #                             /
    #                           /
    # LcMin -o----------------/
    #        |                |       |
    #      Point           DistMin DistMax
    # Field 1: Distance to electrodes

    Origin = gmsh.model.occ.addPoint(0, 0, 0, lcar1)
    gmsh.model.occ.synchronize()

    # add Points
    EndPoints_tags = [Origin]

    if EndPoints_tags:
        gmsh.model.mesh.field.add("Distance", 1)
        gmsh.model.mesh.field.setNumbers(1, "NodesList", EndPoints_tags)

        # Field 2: Threshold that dictates the mesh size of the background field
        gmsh.model.mesh.field.add("Threshold", 2)
        gmsh.model.mesh.field.setNumber(2, "IField", 1)
        gmsh.model.mesh.field.setNumber(2, "LcMin", lcar1 / 100.0)
        gmsh.model.mesh.field.setNumber(2, "LcMax", lcar1)
        gmsh.model.mesh.field.setNumber(2, "DistMin", 10 * unit)
        gmsh.model.mesh.field.setNumber(2, "DistMax", 14 * unit)
        gmsh.model.mesh.field.setNumber(2, "StopAtDistMax", 17 * unit)
        gmsh.model.mesh.field.setAsBackgroundMesh(2)

        """
        # We could also use a `Box' field to impose a step change in element sizes
        # inside a box
        gmsh.model.mesh.field.add("Box", 3)
        gmsh.model.mesh.field.setNumber(3, "VIn", lcar1 / 15.0)
        gmsh.model.mesh.field.setNumber(3, "VOut", lcar1)
        gmsh.model.mesh.field.setNumber(3, "XMin", 0)
        gmsh.model.mesh.field.setNumber(3, "XMax", 20 * unit)
        gmsh.model.mesh.field.setNumber(3, "YMin", -60 * unit)
        gmsh.model.mesh.field.setNumber(3, "YMax", 60 * unit)
        gmsh.model.mesh.field.setNumber(3, "Thickness", 0.3 * unit)

        # Let's use the minimum of all the fields as the mesh size field:
        gmsh.model.mesh.field.add("Min", 4)
        gmsh.model.mesh.field.setNumbers(4, "FieldsList", [1, 2, 3])
        """

    gmsh.option.setNumber("Mesh.Algorithm", MeshAlgo2D[algo])
    gmsh.model.mesh.generate(2)

    """ Only working when 1 Bitter section and gmsh >= 4.11.xx
    if cracks:
        print("Creating cracks for Bitter cooling slits")
        for i, crack in enumerate(cracks):
            print(f"[{i}] {crack}: id={cracks[crack]}")
            gmsh.plugin.setNumber("Crack", "Dimension", 1)
            gmsh.plugin.setNumber("Crack", "PhysicalGroup", cracks[crack])
            gmsh.plugin.setNumber("Crack", "DebugView", 1)
            gmsh.plugin.run("Crack")
    """

    pass

