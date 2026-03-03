import os
import sys
import gmsh

from ..argparse_utils import add_common_args, add_wd_arg, add_show_arg


def main():
    import argparse

    """Console script for python_magnetgeo."""
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "filenames",
        help="name of the meshes to be loaded (msh file)",
        nargs="+",
        metavar="filenames",
        type=str,
    )
    add_wd_arg(parser)
    add_show_arg(parser)
    add_common_args(parser)
    args = parser.parse_args()
    print(f"Arguments: {args}")

    cwd = os.getcwd()
    if args.wd:
        os.chdir(args.wd)

    meshname = ""
    i = 1
    new_msh = []
    for mesh in args.filenames:
        print("\nOpen ", mesh)
        gmsh.initialize()
        gmsh.option.setNumber("General.Terminal", 1)
        gmsh.option.setNumber("General.Verbosity", 0)
        if args.debug:
            gmsh.option.setNumber("General.Verbosity", 5)
        gmsh.open(mesh)

        if args.verbose:
            print("    tags of Entities before =", gmsh.model.getEntities())
        for dims in [0, 1, 2]:
            tagsEnt = gmsh.model.getEntities(dims)

            tagsEnt_toRemove = []
            for dim, tag in tagsEnt:
                if tag < 1000:
                    gmsh.model.setTag(dim, tag, tag + i * 1000)
                    tagsEnt_toRemove.append((dim, tag))

            # print("tagsEnt_toRemove=", tagsEnt_toRemove)
            gmsh.model.removeEntities(tagsEnt_toRemove)
            # print("tags of Entities after=", gmsh.model.getEntities(dims))

        if args.verbose:
            print("     tags of Entities before =", gmsh.model.getEntities())

        vGroups = gmsh.model.getPhysicalGroups()
        for iGroup in vGroups:
            dimGroup = iGroup[0]  # 1D, 2D or 3D
            tagGroup = iGroup[1]
            namGroup = gmsh.model.getPhysicalName(dimGroup, tagGroup)
            if args.verbose:
                print(f"    Physical group : ({dimGroup},{tagGroup},{namGroup})")
            vEnt = gmsh.model.getEntitiesForPhysicalGroup(dimGroup, tagGroup)
            gmsh.model.removePhysicalGroups([(dimGroup, tagGroup)])
            gmsh.model.addPhysicalGroup(dimGroup, vEnt, tagGroup + i * 1000)
            gmsh.model.setPhysicalName(dimGroup, tagGroup + i * 1000, f"{namGroup}_{i}")
            if args.verbose:
                print(
                    f"      Physical group modified : ({dimGroup},{tagGroup + i * 100},{namGroup}_{i})"
                )

        gmsh.model.occ.synchronize()

        curves = gmsh.model.getEntities(dim=1)
        if args.verbose:
            print("    Curves:", curves)

        surfaces = gmsh.model.getEntities(dim=2)
        if args.verbose:
            print("    Surfaces:", surfaces)

        new_msh.append(mesh.replace(".msh", "_temp.msh"))
        print(f"    Save {new_msh[-1]}")
        gmsh.write(f"{new_msh[-1]}")

        gmsh.finalize()
        i += 1
        meshname += mesh.replace(".msh", "") + "_"

    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 1)
    gmsh.option.setNumber("General.Verbosity", 0)
    if args.debug:
        gmsh.option.setNumber("General.Verbosity", 5)

    gmsh.open(new_msh[0])
    for msh in new_msh[1:]:
        gmsh.merge(msh)

    gmsh.model.occ.synchronize()

    gmsh.model.mesh.generate(2)
    print(f"\nSave {meshname}.msh\n")
    gmsh.write(f"{meshname}.msh".format("merged"))

    if args.show:
        gmsh.fltk.run()
    gmsh.finalize()

    for msh in new_msh:
        print("Delete ", msh)
        os.remove(msh)


if __name__ == "__main__":
    sys.exit(main())
