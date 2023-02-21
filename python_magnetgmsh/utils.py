import sys
import os

from io import StringIO
import yaml
from lxml import etree

import gmsh


def load_Xao(file: str, GeomParams: dict, debug=False):
    """
    load Xao and return (gname, tree)
    """

    gname = ""
    fformat = ""
    cad = None
    gfile = ""
    cleanup = False
    tree = None

    with open(file, "r") as f:
        tree = etree.parse(f, parser=None)
    if debug:
        print(etree.tostring(tree.getroot()))

    # get geometry 'name' and shape 'format', 'file'
    tr_elements = tree.xpath("//geometry")
    for i, group in enumerate(tr_elements):
        gname = group.attrib["name"]
        if debug:
            print("gname=", gname)
        gmsh.model.add(gname)
        for child in group:
            if "format" in child.attrib:
                fformat = child.attrib["format"]
                if debug:
                    print(f"format: {child.attrib['format']}")

            # CAD is stored in a separate file
            if "file" in child.attrib and child.attrib["file"] != "":
                gfile = child.attrib["file"]

    if not gfile:
        print("CAD is embedded into xao file")
        cad_elements = tree.xpath("//shape")
        gfile = "tmp." + fformat.lower()
        for item in cad_elements:
            if debug:
                print(item.text)
            with open(gfile, "x") as f:
                cadData = StringIO(item.text)
                f.write(cadData.getvalue())
                cadData.close()
                cleanup = True

    volumes = gmsh.model.occ.importShapes(gfile)
    gmsh.model.occ.synchronize()

    if len(gmsh.model.getEntities(GeomParams["Solid"][0])) == 0:
        print(f"Pb loaging {gfile}:")
        print(f"Solids: {len(volumes)}")
        exit(1)

    if debug:
        # get all model entities
        ent = gmsh.model.getEntities()
        for e in ent:
            print(e)
    if cleanup:
        os.remove(gfile)

    return (gname, tree)
