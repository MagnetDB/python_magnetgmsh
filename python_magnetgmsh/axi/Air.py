# Load Modules for geometrical Objects
from python_magnetgeo.Insert import Insert
from python_magnetgeo.MSite import MSite
from python_magnetgeo.Bitter import Bitter
from python_magnetgeo.Supra import Supra
from python_magnetgeo.Bitters import Bitters
from python_magnetgeo.Supras import Supras
from python_magnetgeo.Screen import Screen
from python_magnetgeo.Helix import Helix

ObjectType = MSite | Bitters | Supras | Insert | Bitter | Supra | Screen | Helix


def gmsh_air(Object: ObjectType, AirData: tuple) -> tuple:
    """
    create Air box
    """
    if isinstance(Object, MSite):
        ([r_min, r_max], [z_min, z_max]) = Object.boundingBox()
        r0 = 0
        dr = r_max * AirData[0]
        z0 = z_min * AirData[1]
        dz = abs(z_max - z_min) * AirData[1]
    else:
        (r, z) = Object.boundingBox()
        print(f"gmsh_air: r={r}, z={z}")
        r0 = 0
        dr = r[1] * AirData[0]
        z0 = z[0] * AirData[1]
        dz = abs(z[1] - z[0]) * AirData[1]

    return (r0, z0, dr, dz)


def gmsh_boundingbox(name: str) -> tuple:
    import gmsh

    x0 = []
    y0 = []
    z0 = []
    x1 = []
    y1 = []
    z1 = []

    vGroups = gmsh.model.getPhysicalGroups()
    print(f"gmsh_boundingbox: {name}: {len(vGroups)}")
    for iGroup in vGroups:
        dimGroup = iGroup[0]  # 1D, 2D or 3D
        tagGroup = iGroup[1]
        namGroup = gmsh.model.getPhysicalName(dimGroup, tagGroup)
        print(f"namGroup={namGroup}, dimGroup={dimGroup}")
        if namGroup == name:
            vEntities = gmsh.model.getEntitiesForPhysicalGroup(dimGroup, tagGroup)
            print(
                f"gmsh_boundingbox: {name}: dimGroup{dimGroup}, entities={vEntities} (type={type(vEntities)})"
            )
            if isinstance(vEntities, int):
                (x0i, y0i, z0i, x1i, y1i, z1i) = gmsh.model.getBoundingBox(2, vEntities)
                print(f"x0i={x0i}")
                x0.append(x0i)
                y0.append(y0i)
                z0.append(z0i)
                x1.append(x1i)
                y1.append(y1i)
                z1.append(z1i)
            else:
                for entity in vEntities:
                    (x0i, y0i, z0i, x1i, y1i, z1i) = gmsh.model.getBoundingBox(
                        2, entity
                    )
                    print(f"x0i={x0i}")
                    x0.append(x0i)
                    y0.append(y0i)
                    z0.append(z0i)
                    x1.append(x1i)
                    y1.append(y1i)
                    z1.append(z1i)

    xmin = min(x0)
    xmax = max(x1)
    ymin = min(y0)
    ymax = max(y1)
    zmin = min(z0)
    zmax = max(z1)

    res = (xmin, ymin, zmin, xmax, ymax, zmax)
    return res
