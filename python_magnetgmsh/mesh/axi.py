import re

from math import copysign
import gmsh
from ..MeshAxiData import MeshAxiData
from ..MeshData import MeshData

MeshAlgo2D = {
    "MeshAdapt": 1,
    "Automatic": 2,
    "Initial": 3,
    "Delaunay": 5,
    "Frontal-Delaunay": 6,
    "BAMG": 7,
}

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
    return allowed 2D algo
    """
    return list(MeshAlgo2D.keys())


def get_algo(name: str):
    return MeshAlgo2D[name]


def gmsh_msh(
    algo: str,
    meshdata: MeshAxiData,
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

    meshdim = 2
    HXT_support = False
    print(f"create Axi Gmsh mesh ({algo})")
    gmsh.option.setNumber("Mesh.Algorithm", MeshAlgo2D[algo])

    # scaling
    unit = 1
    if scaling:
        unit = 0.001
        gmsh.option.setNumber("Geometry.OCCScaling", unit)

    # Assign a mesh size to all the points:
    lcar1 = 80 * unit

    Origin = gmsh.model.occ.addPoint(0, 0, 0, lcar1)
    gmsh.model.occ.synchronize()

    # add Points
    EndPoints_tags = [Origin]

    gmsh.model.mesh.setSize(gmsh.model.getEntities(0), lcar1)

    mesh_dict = meshdata.mesh_dict
    # print(f"mesh_dict: {mesh_dict}")
    lcs = meshdata.surfhypoths
    # print(f"lcs: {lcs}")

    eps = {}
    min_eps = 0.5 * unit
    """
    eps = {
        "Slit1": 0.16899920781621336,
        "Slit2": 0.15823567225436383,
        "Slit3": 0.11114198388441233,
        "Slit4": 0.13878949537006918,
    }
    min_eps = min(list(eps.values()))
    print(f"eps={eps}, min_eps={min_eps}")
    """

    # get ov and lc per PhysicalSurface
    lc_data = {}
    lc_sdata = {}
    vGroups = gmsh.model.getPhysicalGroups()
    for iGroup in vGroups:
        dimGroup = iGroup[0]  # 1D, 2D or 3D
        tagGroup = iGroup[1]
        namGroup = gmsh.model.getPhysicalName(dimGroup, tagGroup)
        # print(f"namGroup={namGroup} dimgroup={dimGroup}")
        if namGroup in mesh_dict:
            _namGroup = re.sub(r"_Slit\d+[_[lr]]", "", namGroup)
            def_lcs = mesh_dict[_namGroup]
            # print(f"mesh_dict[{_namGroup}]={def_lcs}")
            if isinstance(def_lcs, int):
                lc = lcs[def_lcs]
            else:
                lc = lcs[def_lcs[0]][def_lcs[1]]
            print(f"{namGroup}: lc={lc}")

            vEntities = gmsh.model.getEntitiesForPhysicalGroup(dimGroup, tagGroup)
            ov = []
            xmin = 0
            ymin = 0
            zmin = 0
            xmax = 0
            ymax = 0
            zmax = 0
            lc_data[namGroup] = {"box": [], "pts": [], "lc": lcar1}
            # if isinstance(vEntities, list):
            for i, entity in enumerate(vEntities):
                (xmin, ymin, zmin, xmax, ymax, zmax) = gmsh.model.getBoundingBox(
                    2, entity
                )
                _ov = gmsh.model.getEntitiesInBoundingBox(
                    xmin, ymin, zmin, xmax, ymax, zmax, 0
                )
                ov += _ov

                lc_data[namGroup]["box"].append((xmin, ymin, zmin, xmax, ymax, zmax))
                lc_data[namGroup]["pts"] += [tag for (dimtag, tag) in ov]
                lc_data[namGroup]["lc"] = lc
            # else:
            #     raise RuntimeError(
            #         f"vEntities: {type(vEntities)} unsupported return type"
            #     )

            # print(f"lc[{namGroup}]: {lc_data[namGroup]}")
        # else:
        #    print(f"{namGroup} is not in mesh_dict")

        if dimGroup == 1:
            vEntities = gmsh.model.getEntitiesForPhysicalGroup(dimGroup, tagGroup)
            ov = []
            lv = []
            size = []
            # if isinstance(vEntities, list):
            for i, entity in enumerate(vEntities):
                (xmin, ymin, zmin, xmax, ymax, zmax) = gmsh.model.getBoundingBox(
                    1, entity
                )
                _ov = gmsh.model.getEntitiesInBoundingBox(
                    xmin, ymin, zmin, xmax, ymax, zmax, 0
                )
                ov += _ov
                _lv = gmsh.model.getEntitiesInBoundingBox(
                    xmin, ymin, zmin, xmax, ymax, zmax, 1
                )
                # print(
                #     f"{namGroup}: entity={entity}, _lv={_lv}, xmin={xmin}, ymin={ymin}, zmin={zmin}, xmax={xmax}, ymax={ymax}, zmax={zmax}"
                # )
                lv += _lv
                size.append(max(abs(xmax - xmin), abs(ymax - ymin)))
            # else:
            #     raise RuntimeError(
            #         f"vEntities: {type(vEntities)} unsupported return type"
            #     )
            lc = lcar1

            if eps is not None:
                if namGroup in eps:
                    lc = eps[namGroup]

            lc_sdata[namGroup] = (ov, lv, size, lc)

    # Apply lc in reverse order to get nice mesh
    print("Physical Surfaces")
    for key, values in reversed(lc_data.items()):
        print(f"lc_data[{key}]: lc={values['lc']}")
        gmsh.model.mesh.setSize([(0, tag) for tag in values["pts"]], values["lc"])

    """
    print("Physical Lines:")
    for key in reversed(lc_sdata):
        print(f"lc_sdata[{key}]: size={lc_sdata[key][2]}, lc={lc_sdata[key][3]}")
    """

    # LcMax -                         /------------------
    #                               /
    #                             /
    #                           /
    # LcMin -o----------------/
    #        |                |       |
    #      Point           DistMin DistMax
    # Field 1: Distance to electrodes

    # Gmsh has to be compiled with HXT and P4EST to use automaticMeshSizeField
    # 2D size field not operational
    if HXT_support and algo == "HXT":
        gmsh.model.mesh.field.add("AutomaticMeshSizeField", 1)
        gmsh.model.mesh.field.setNumber(1, "features", True)
        gmsh.model.mesh.field.setNumber(1, "gradation", 2)
        gmsh.model.mesh.field.setNumber(1, "hBulk", lcar1 / 10.0 * unit)
        gmsh.model.mesh.field.setNumber(1, "hMax", lcar1 * unit)
        gmsh.model.mesh.field.setNumber(1, "hMin", lcar1 / 100.0 * unit)
        gmsh.model.mesh.field.setNumber(1, "smoothing", True)
        gmsh.model.mesh.field.setAsBackgroundMesh(1)

    # features: Enable computation of local feature size (thin channels), Type: boolean, Default value: 1
    # gradation: Maximum growth ratio for the edges lengths, Type: float, Default value: 1.1
    # hBulk: Default size where it is not prescribed, Type: float, Default value: -1
    # hMax: Maximum size, Type: float, Default value: -1
    # hMin: Minimum size, Type: float, Default value: -1
    # nPointsPerCircle: Number of points per circle (adapt to curvature of surfaces), Type: integer, Default value: 20
    # nPointsPerGap: Number of layers of elements in thin layers, Type: integer, Default value: 1
    # p4estFileToLoad: p4est file containing the size field, Type: string, Default value: ""
    # smoothing:Enable size smoothing (should always be true), Type: boolean, Default value: 1

    else:
        Lines = False
        Boxes = False
        nfield = 0
        dfields = []

        if air and EndPoints_tags:
            gmsh.model.mesh.field.add("Distance", nfield)
            gmsh.model.mesh.field.setNumbers(nfield, "NodesList", EndPoints_tags)
            nfield += 1

            # Field 2: Threshold that dictates the mesh size of the background field
            print(f"Field[Thresold] for Air (Distance with Origin): {nfield}")
            gmsh.model.mesh.field.add("Threshold", nfield)
            gmsh.model.mesh.field.setNumber(nfield, "IField", nfield - 1)
            gmsh.model.mesh.field.setNumber(nfield, "LcMin", lcar1 / 100.0 * unit)
            gmsh.model.mesh.field.setNumber(nfield, "LcMax", lcar1 * unit)
            gmsh.model.mesh.field.setNumber(nfield, "DistMin", 10 * unit)
            gmsh.model.mesh.field.setNumber(nfield, "DistMax", 14 * unit)
            gmsh.model.mesh.field.setNumber(nfield, "StopAtDistMax", True)
            dfields.append(nfield)
            nfield += 1

            # use a `Box' field to impose a step change in element sizes
            # inside a box
            max_xmin = 0
            max_zmax = 0
            min_zmin = 0
            for key, values in reversed(lc_data.items()):
                for box in values["box"]:
                    (xmin, ymin, zmin, xmax, ymax, zmax) = box
                    max_xmin = max(xmin, max_xmin)
                    max_zmax = max(zmax, max_zmax)
                    min_zmin = min(zmin, min_zmin)

            # correct zmax/zmin bound if zero ??

            print(f"Field[Box] for Air: {nfield}")
            gmsh.model.mesh.field.add("Box", nfield)
            gmsh.model.mesh.field.setNumber(nfield, "VIn", lcar1 / 30.0 * unit)
            gmsh.model.mesh.field.setNumber(nfield, "VOut", lcar1 * unit)
            gmsh.model.mesh.field.setNumber(nfield, "XMin", 0 * unit)
            gmsh.model.mesh.field.setNumber(nfield, "XMax", 0.8 * max_xmin)
            gmsh.model.mesh.field.setNumber(
                nfield, "YMin", copysign(1.2 * min_zmin, min_zmin)
            )
            gmsh.model.mesh.field.setNumber(
                nfield, "YMax", copysign(1.2 * max_zmax, max_zmax)
            )
            gmsh.model.mesh.field.setNumber(nfield, "Thickness", 0.3 * unit)
            dfields.append(nfield)
            nfield += 1

        for key, values in reversed(lc_data.items()):
            print(
                f'Field[Box] for {key}: from {nfield} to {nfield+len(values["box"])-1}'
            )
            for box in values["box"]:
                print(f"\t{box}")
            print(f"\tlc={values['lc']}")
            lc = values["lc"]
            for box in values["box"]:
                (xmin, ymin, zmin, xmax, ymax, zmax) = box
                gmsh.model.mesh.field.add("Box", nfield)
                gmsh.model.mesh.field.setNumber(nfield, "VIn", lc * unit)
                gmsh.model.mesh.field.setNumber(nfield, "VOut", lcar1 * unit)
                gmsh.model.mesh.field.setNumber(nfield, "XMin", xmin * unit)
                gmsh.model.mesh.field.setNumber(nfield, "XMax", xmax * unit)
                gmsh.model.mesh.field.setNumber(nfield, "YMin", ymin * unit)
                gmsh.model.mesh.field.setNumber(nfield, "YMax", ymax * unit)
                # gmsh.model.mesh.field.setNumber(nfield, "Thickness", 0.001 * unit)
                dfields.append(nfield)
                nfield += 1

        if Boxes:
            # special treatment for Slit: Try with refinedboxes
            for box in refinedboxes:
                (xmin, ymin, zmin, xmax, ymax, zmax) = box[0]
                hsize = box[1]  # almost working except a HP/BP
                gmsh.model.mesh.field.add("Box", nfield)
                gmsh.model.mesh.field.setNumber(nfield, "VIn", hsize * unit)
                gmsh.model.mesh.field.setNumber(nfield, "VOut", lcar1 * unit)
                gmsh.model.mesh.field.setNumber(nfield, "XMin", xmin * unit)
                gmsh.model.mesh.field.setNumber(nfield, "XMax", xmax * unit)
                gmsh.model.mesh.field.setNumber(nfield, "YMin", ymin * unit)
                gmsh.model.mesh.field.setNumber(nfield, "YMax", ymax * unit)
                gmsh.model.mesh.field.setNumber(nfield, "Thickness", 0.001 * unit)
                dfields.append(nfield)
                nfield += 1

        # # uncomment if test anisotropic
        # special treatment for Slit: add distance to line with a threshold (see gmsh-tuto)
        # TODO better to get curve list before, create just like gmsh_box but in gmsh_ids?
        uniq = []
        uniqpts = []
        sizedict = {}
        """
        curvelist = []
        ptslist = []
        lcdict = {}
        for key, values in lc_sdata.items():
            if not key in ["ZAxis", "Infty"]:
                _list = [tag for (dimtag, tag) in values[1]]
                curvelist += _list
                _plist = [tag for (dimtag, tag) in values[0]]
                ptslist += _plist
                print(
                    f"{key}: _list={_list}, size={values[2]} ({len(values[2])}), lc={values[3]}",
                    flush=True,
                )
                for i, tag in enumerate(_list):
                    sizedict[tag] = values[2][i]
                    lcdict[tag] = values[3]

        print(f"ptslist={ptslist} ({len(ptslist)})")
        seen = set()
        dupespts = [x for x in ptslist if x in seen or seen.add(x)]
        uniqpts = list(set(ptslist))
        print(f"uniqpts={uniqpts} ({len(uniqpts)})")
        print(f"dupespts={dupespts} ({len(dupespts)})")

        print(f"curvelist={curvelist} ({len(curvelist)})")
        seen = set()
        dupes = [x for x in curvelist if x in seen or seen.add(x)]
        uniq = list(set(curvelist))
        print(f"uniq={uniq} ({len(uniq)})")
        print(f"dupes={dupes} ({len(dupes)})")
        """

        if Lines:
            """
            # test boundary: dont work
            for curve in list(set(uniq)):
                gmsh.model.mesh.field.add("BoundaryLayer", nfield)
                gmsh.model.mesh.field.setNumbers(nfield, "CurvesList", uniq)
                gmsh.model.mesh.field.setNumbers(
                    nfield, "Size", [0.1 * unit] * len(uniq)
                )
                gmsh.model.mesh.field.setNumbers(
                    nfield, "Thickness", [0.01 * unit] * len(uniq)
                )
                dfields.append(nfield)
                nfield += 1
            """

            # refine pts: working needed in addition with refine curves
            # TODO give charact according to curve
            if uniqpts is not None:
                gmsh.model.mesh.field.add("Distance", nfield)
                gmsh.model.mesh.field.setNumbers(nfield, "NodesList", uniqpts)
                nfield += 1

                gmsh.model.mesh.field.add("Threshold", nfield)
                gmsh.model.mesh.field.setNumber(nfield, "IField", nfield - 1)
                gmsh.model.mesh.field.setNumber(nfield, "LcMin", min_eps / 2.0 * unit)
                gmsh.model.mesh.field.setNumber(nfield, "LcMax", lcar1 * unit)
                gmsh.model.mesh.field.setNumber(nfield, "DistMin", min_eps / 2.0 * unit)
                gmsh.model.mesh.field.setNumber(nfield, "DistMax", min_eps * unit)
                gmsh.model.mesh.field.setNumber(nfield, "StopAtDistMax", True)
                dfields.append(nfield)
                nfield += 1

                """
                # refine curves: working but creating huge mesh
                for curve in list(set(uniq)):
                    if lcdict[curve] != lcar1:
                        gmsh.model.mesh.field.add("Distance", nfield)
                        gmsh.model.mesh.field.setNumbers(nfield, "CurvesList", [curve])
                        sampling = int(sizedict[curve] / 0.05) * 10
                        print(
                            f"curve: id={curve}, size={sizedict[curve]}, sampling={sampling}, lc={lcdict[curve]}"
                        )
                        gmsh.model.mesh.field.setNumber(nfield, "Sampling", sampling)
                        nfield += 1

                        lc = lcdict[curve]
                        gmsh.model.mesh.field.add("Threshold", nfield)
                        gmsh.model.mesh.field.setNumber(nfield, "IField", nfield - 1)
                        gmsh.model.mesh.field.setNumber(nfield, "LcMin", lc / 3.0 * unit)
                        gmsh.model.mesh.field.setNumber(nfield, "LcMax", lcar1 * unit)
                        gmsh.model.mesh.field.setNumber(nfield, "DistMin", lc / 2.0 * unit)
                        gmsh.model.mesh.field.setNumber(nfield, "DistMax", lc * unit)
                        gmsh.model.mesh.field.setNumber(nfield, "StopAtDistMax", True)
                        dfields.append(nfield)
                        nfield += 1
                """

        # test Attractor: not working with actual gmsh package - need to check compile, support for mmg??
        if uniq is not None:
            for curve in list(set(uniq)):
                gmsh.model.mesh.field.add("AttractorAnisoCurve", nfield)
                gmsh.model.mesh.field.setNumbers(nfield, "CurvesList", [curve])
                gmsh.model.mesh.field.setNumber(nfield, "DistMin", 0.01 * unit)
                gmsh.model.mesh.field.setNumber(nfield, "DistMax", 0.06 * unit)
                sampling = int(sizedict[curve] / 0.05) * 10
                print(f"curve: id={curve}, size={sizedict[curve]}, sampling={sampling}")
                gmsh.model.mesh.field.setNumber(nfield, "Sampling", sampling)
                gmsh.model.mesh.field.setNumber(nfield, "SizeMaxNormal", 0.01 * unit)
                gmsh.model.mesh.field.setNumber(nfield, "SizeMinNormal", 0.001 * unit)
                gmsh.model.mesh.field.setNumber(
                    nfield, "SizeMaxTangent", sizedict[curve] / 500.0 * unit
                )
                gmsh.model.mesh.field.setNumber(
                    nfield, "SizeMinTangent", sizedict[curve] / 5000.0 * unit
                )
                nfield += 1

        # Let's use the minimum of all the fields as the mesh size field:
        print(f"dfields: {dfields}")
        if dfields:
            gmsh.model.mesh.field.add("Min", nfield)
            gmsh.model.mesh.field.setNumbers(nfield, "FieldsList", dfields)  # dfields
            print(f"Field[Min] = {nfield}, Min=[{dfields[0]},...,{dfields[-1]}]")

            print(f"Apply background mesh {nfield}")
            gmsh.model.mesh.field.setAsBackgroundMesh(nfield)

    gmsh.model.mesh.generate(meshdim)

    pass


def gmsh_cracks(debug: bool = False):
    """
    add cracks to mesh
    """
    print("Add cracks")

    cracks = {}
    vGroups = gmsh.model.getPhysicalGroups()
    for iGroup in vGroups:
        dimGroup = iGroup[0]  # 1D, 2D or 3D
        tagGroup = iGroup[1]
        namGroup = gmsh.model.getPhysicalName(dimGroup, tagGroup)
        if "slit" in namGroup:
            print(f"{namGroup}: Bitter cooling slit tag={tagGroup}")
            cracks[namGroup] = tagGroup

    """ Only working when 1 Bitter section and gmsh >= 4.11.xx """
    if cracks:
        print("Creating cracks for Bitter cooling slits")
        for i, crack in enumerate(cracks):
            print(f"[{i}] {crack}: id={cracks[crack]}")
            gmsh.plugin.setNumber("Crack", "Dimension", 1)
            gmsh.plugin.setNumber("Crack", "PhysicalGroup", cracks[crack])
            if debug:
                gmsh.plugin.setNumber("Crack", "DebugView", 1)
            gmsh.plugin.run("Crack")
    """ """

    pass
