import os

import gmsh

import xmltodict
from collections import OrderedDict
from ..logging_config import get_logger

logger = get_logger(__name__)


def load_Xao_groups(xml_dict: dict, debug: bool = False) -> tuple:
    """
    load Xao as an xmldict
    Returns tuple for vtags, stags, ltags
    """

    vtags = {}
    stags = {}
    ltags = {}

    # load group name definition
    for key, value in xml_dict["XAO"]["groups"].items():
        # logger.debug(f"key={key}, value={value}")
        if key == "group":
            for i, item in enumerate(value):
                name = item["@name"]
                dimension = item["@dimension"]
                count = item["@count"]
                logger.debug(f"Processing group: {name}, dimension: {dimension}, count: {count}")
                elements = []
                if isinstance(item["element"], list):
                    for evalue in item["element"]:
                        # logger.debug(f'evalue={list(evalue.values())}')
                        elements += [int(v) + 1 for v in list(evalue.values())]
                elif isinstance(item["element"], dict) or isinstance(
                    item["element"], OrderedDict
                ):
                    # logger.debug(f"evalue={list(item['element'].values())}")
                    elements += [int(v) + 1 for v in list(item["element"].values())]
                logger.debug(f"Group {name}: {len(elements)} elements")

                if dimension == "solid":
                    vtags[name] = elements
                elif dimension == "face":
                    stags[name] = elements
                elif dimension == "edge":
                    ltags[name] = elements
                else:
                    raise RuntimeError(
                        f"unexpected dimension for {name} - got {dimension} expect solid|face|edge"
                    )

    return (vtags, stags, ltags)


def load_Xao(file: str, GeomParams: dict, debug=False):
    """
    load Xao and return (gname, tags)
    """

    cleanup = False

    # try to load file with xmltodict
    logger.info(f"Loading XAO file with xmltodict: {file}")
    with open(file, "r") as f:
        xml_content = f.read()
        # logger.debug(xml_content)

        # change xml format to ordered dict
        my_ordered_dict = xmltodict.parse(xml_content)
        # logger.debug("Ordered Dictionary is:")
        # logger.debug(my_ordered_dict)

        # load group name definition
        if debug:
            for key, value in my_ordered_dict["XAO"]["geometry"].items():
                logger.debug(f"key={key}, value type={type(value)}")
                if isinstance(value, OrderedDict):
                    for skey, svalue in value.items():
                        logger.debug(f"  skey={skey}, svalue={svalue}")

        # look for shape if BREP is not embedded and store the value in  tmp file
        cad = my_ordered_dict["XAO"]["geometry"]
        gname = cad["@name"]
        fformat = cad["shape"]["@format"]
        ffile = None
        if "@file" in cad["shape"]:
            ffile = cad["shape"]["@file"]
        else:
            logger.info("CAD geometry is embedded in XAO file")
            cad_data = cad["shape"]["#text"]

            ffile = f"tmp.{fformat.lower()}"
            with open(ffile, "x") as f:
                f.write(cad_data)
                cleanup = True

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
    """

    gmsh.model.add(gname)
    logger.info(f"Importing CAD shapes from {ffile}")
    volumes = gmsh.model.occ.importShapes(ffile)
    gmsh.model.occ.synchronize()

    if len(gmsh.model.getEntities(GeomParams["Solid"][0])) == 0:
        logger.error(f"Failed to load solids from {ffile}")
        logger.error(f"Volumes imported: {len(volumes)}")
        exit(1)

    if debug:
        # get all model entities
        ent = gmsh.model.getEntities()
        for e in ent:
            logger.debug(f"Entity: {e}")
    if cleanup:
        os.remove(ffile)

    tags = load_Xao_groups(my_ordered_dict)
    return (gname, tags)
