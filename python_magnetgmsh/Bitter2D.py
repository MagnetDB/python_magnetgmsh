import os
import sys

import yaml
import gmsh
from python_magnetgeo.Bitter import Bitter
from python_magnetgeo.Shape2D import Shape2D

from .utils.lists import flatten

# TieRod
def create_shape(x: float, y: float, shape: Shape2D):
    curv = []
    pts = []
    for i, pt in enumerate(shape.pts):
        pts.append(gmsh.model.occ.addPoint(x + pt[0], pt[1], 0))
        if i >= 1:
            curv.append(gmsh.model.occ.addLine(pts[i - 1], pts[i]))
    curv.append(gmsh.model.occ.addLine(pts[-1], pts[0]))
    _cl = gmsh.model.occ.addCurveLoop(curv)
    print(f"create_shape: _cl={_cl}, {curv}")
    curv.clear()
    pts.clear()
    return _cl


def gmsh2D_ids(Bitter: Bitter, AirData: tuple, debug: bool = False) -> tuple:
    """
    create gmsh 2D geometry
    """
    print("Bitter/gmsh2D_ids")

    from math import pi, cos, sin

    tierod = Bitter.tierod
    theta = 2 * pi / float(tierod.n)
    Origin = gmsh.model.occ.addPoint(0, 0, 0)

    # Bitter sector
    curv = []
    pt0_r0 = gmsh.model.occ.addPoint(
        Bitter.r[0] * cos(-theta / 2.0), Bitter.r[0] * sin(-theta / 2.0), 0
    )
    pt1_r0 = gmsh.model.occ.addPoint(
        Bitter.r[0] * cos(theta / 2.0), Bitter.r[0] * sin(theta / 2.0), 0
    )
    curv.append(gmsh.model.occ.addCircleArc(pt0_r0, Origin, pt1_r0))

    pt0_r1 = gmsh.model.occ.addPoint(
        Bitter.r[1] * cos(-theta / 2.0), Bitter.r[1] * sin(-theta / 2.0), 0
    )
    pt1_r1 = gmsh.model.occ.addPoint(
        Bitter.r[1] * cos(theta / 2.0), Bitter.r[1] * sin(theta / 2.0), 0
    )
    curv.append(gmsh.model.occ.addLine(pt0_r0, pt0_r1))
    curv.append(gmsh.model.occ.addCircleArc(pt0_r1, Origin, pt1_r1))
    curv.append(gmsh.model.occ.addLine(pt1_r1, pt1_r0))
    cl = gmsh.model.occ.addCurveLoop(curv)
    sector = gmsh.model.occ.addPlaneSurface([cl])
    print(f"Bitter sector: {cl} = {curv}")
    del curv

    _ltierod = create_shape(tierod.r, 0, tierod.shape)
    tierod_id = gmsh.model.occ.addPlaneSurface([_ltierod])
    # disk = gmsh.model.occ.addPlaneSurface([cl, _ltierod])

    # CoolingSlits
    holes = [tierod_id]
    names = []
    for j, slit in enumerate(Bitter.coolingslits):
        _names = []
        print(f"slit[{j}]: nslits={slit.n}, r={slit.r}, tierod={tierod.r}")
        nslits = slit.n
        if slit.r == tierod.r:
            nslits += tierod.n

        theta_s = 2 * pi / float(nslits)
        angle = slit.angle * pi / 180.0

        # create Shape for slit
        _lc = create_shape(x=slit.r, y=0, shape=slit.shape)
        slit_id = gmsh.model.occ.addPlaneSurface([_lc])
        if angle != 0:
            gmsh.model.occ.rotate([(2, slit_id)], 0, 0, 0, 0, 0, 1, angle)
            print(f"slit[{j}][0]: rotate {angle} init")

        if slit.r == tierod.r and angle == 0:
            print("skip slit")
        else:
            holes.append(slit_id)
            _names.append(f"slit{j}_0")

        for n in range(1, nslits):
            if (
                n * theta_s + angle <= theta / 2.0
                or n * theta_s + angle >= 2 * pi - theta / 2.0
            ):
                res = gmsh.model.occ.copy([(2, slit_id)])
                # print(f"res={res}")
                _id = res[0][1]
                gmsh.model.occ.rotate([(2, _id)], 0, 0, 0, 0, 0, 1, n * theta_s)
                holes.append(_id)
                _names.append(f"slit{j}_{n}")

        names.append(_names)

        if slit.r == tierod.r and angle == 0:
            print(f"remove slit{j}_0: {slit_id}")
            gmsh.model.occ.remove([(2, slit_id)], recursive=True)
            gmsh.model.occ.synchronize()

    print(f"holes={holes}")
    print(f"names={names}")
    cad = gmsh.model.occ.cut(
        [(2, sector)], [(2, _id) for _id in holes], removeTool=False
    )
    print(f"cad: {cad}")

    # get BCs ids
    # use
    # gmsh/model/occ/getBoundingBox
    # gmsh/model/occ/getEntitiesInBoundingBox
    def create_bcgroup(shape: int, subshape: int, name: str):
        xmin, ymin, zmin, xmax, ymax, zmax = gmsh.model.occ.getBoundingBox(2, subshape)
        # print(f"boundingbox[{name}]: {[xmin, ymin, zmin, xmax, ymax, zmax]}")
        if abs(zmin - zmax) >= 1.0e-6:
            raise RuntimeError(
                f"create_bcgroup({name}): subshape is expected to be in OxOy plane (zmin={zmin}, Zmax={zmax})"
            )

        interface = gmsh.model.occ.getEntitiesInBoundingBox(
            xmin, ymin, zmin, xmax, ymax, zmax, dim=1
        )
        print(f"interface[{name}]: {interface} ({len(interface)})")

    gmsh.model.occ.removeAllDuplicates()
    create_bcgroup(cad[1][1], tierod_id, "tierod")

    slit_names = flatten(names)
    print(f"slit_names: {len(slit_names)} names, {len(holes)} slits")
    for i in range(1, len(holes)):
        create_bcgroup(cad[1][1], holes[i], slit_names[i - 1])
    for hole in holes:
        gmsh.model.occ.remove([(2, hole)], recursive=True)

    return ([cad[1][1]], (), ())


def main():
    import argparse

    """Console script for python_magnetgeo."""
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "filename", help="name of the model to be loaded (yaml file)", type=str
    )
    parser.add_argument("--wd", help="set a working directory", type=str, default="")
    parser.add_argument("--show", help="display gmsh windows", action="store_true")
    parser.add_argument("--verbose", help="activate debug mode", action="store_true")
    parser.add_argument("--debug", help="activate debug mode", action="store_true")
    args = parser.parse_args()
    print(f"Arguments: {args}")

    cwd = os.getcwd()
    if args.wd:
        os.chdir(args.wd)

    with open(args.filename, "r") as f:
        Object = yaml.load(f, Loader=yaml.FullLoader)
        print(f"Object={Object}, type={type(Object)}")

    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 1)
    gmsh.option.setNumber("General.Verbosity", 0)
    if args.debug or args.verbose:
        gmsh.option.setNumber("General.Verbosity", 5)
    gmsh.model.add(args.filename)
    gmsh.logger.start()

    gmsh2D_ids(Object, (), args.debug)

    gmsh.model.occ.synchronize()
    if args.show:
        gmsh.fltk.run()
    gmsh.finalize()


if __name__ == "__main__":
    sys.exit(main())
