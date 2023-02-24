"""

"""

from typing import Union

import re
import gmsh


def create_physicalgroups(
    tree,
    solid_names: list,
    GeomParams: dict,
    hideIsolant: bool,
    groupIsolant: bool,
    debug: bool = False,
):
    """
    creates PhysicalVolumes
    """

    tr_subelements = tree.xpath("//" + GeomParams["Solid"][1])
    stags = {}
    for i, sgroup in enumerate(tr_subelements):
        for j, child in enumerate(sgroup):
            sname = solid_names[j]
            oname = sname
            print(f"sname={sname}: child.attrib={child.attrib}")

            indices = int(child.attrib["index"]) + 1
            if debug:
                print(
                    f"sname[{j}]: oname={oname}, sname={sname}, child.attrib={child.attrib}, solid_name={solid_names[j]}, indices={indices}"
                )

            skip = False
            if hideIsolant and (
                "Isolant" in sname or "Glue" in sname or "Kapton" in sname
            ):
                if debug:
                    print(f"skip isolant: {sname}")
                skip = True

            # TODO if groupIsolant and "glue" in sname:
            #    sname = remove latest digit from sname
            if groupIsolant and (
                "Isolant" in sname or "Glue" in sname or "Kapton" in sname
            ):
                sname = re.sub(r"\d+$", "", sname)

            if not skip:
                if sname in stags:
                    stags[sname].append(indices)
                else:
                    stags[sname] = [indices]

    # Physical Volumes
    if debug:
        print("Solidtags:")
    for sname in stags:
        pgrp = gmsh.model.addPhysicalGroup(GeomParams["Solid"][0], stags[sname])
        gmsh.model.setPhysicalName(GeomParams["Solid"][0], pgrp, sname)
        if debug:
            print(f"{sname}: {stags[sname]}, pgrp={pgrp}")

    return stags


def create_physicalbcs(
    tree,
    GeomParams,
    groupCoolingChannels,
    Channels,
    hideIsolant,
    groupIsolant,
    debug: bool = False,
):

    tr_elements = tree.xpath("//group")

    bctags = {}
    for i, group in enumerate(tr_elements):
        if debug:
            print(
                "name=",
                group.attrib["name"],
                group.attrib["dimension"],
                group.attrib["count"],
            )

        indices = []
        if group.attrib["dimension"] == GeomParams["Face"][1]:
            for child in group:
                indices.append(int(child.attrib["index"]) + 1)
            sname = group.attrib["name"]

            sname = sname.replace("Air_", "")
            if debug:
                print(f"sname={sname} indices={indices}")

            skip = False

            # if hideIsolant remove "iRint"|"iRext" in Bcs otherwise sname: do not record physical surface for Interface
            if hideIsolant:
                if "IrInt" in sname or "IrExt" in sname:
                    skip = True
                if "iRint" in sname or "iRext" in sname:
                    skip = True
                if "Interface" in sname:
                    if groupIsolant:
                        sname = re.sub(r"\d+$", "", sname)

            if groupIsolant:
                if "IrInt" in sname or "IrExt" in sname:
                    sname = re.sub(r"\d+$", "", sname)
                if "iRint" in sname or "iRext" in sname:
                    sname = re.sub(r"\d+$", "", sname)
                    # print("groupBC:", sname)
                if "Interface" in sname:
                    # print("groupBC: skip ", sname)
                    skip = True

            print(
                f"BCs[{i}]: name={group.attrib['name']}, {group.attrib['dimension']}, {group.attrib['count']}, sname={sname}, skip={skip}"
            )
            if debug:
                print(
                    f"BCs[{i}]: name={group.attrib['name']}, {group.attrib['dimension']}, {group.attrib['count']}, sname={sname}, skip={skip}"
                )
            if not skip:
                if not sname in bctags:
                    bctags[sname] = indices
                else:
                    for index in indices:
                        bctags[sname].append(index)

            if sname in bctags:
                print(f"bctags[{sname}] = {bctags[sname]}")

    if groupCoolingChannels:
        print(f"group cooling channels: {Channels}")
        print(f"registred bctags: {bctags.keys()}")
        if isinstance(Channels, dict):
            for key in Channels:
                print(f"Channels[{key}]]: {Channels[key]}")
                for i, channel in enumerate(Channels[key]):
                    if isinstance(channel[0], str):
                        print(f"{channel} strcase")
                        for bc in channel:
                            tags = []
                            for bc in channel:
                                if bc in bctags:
                                    tags += bctags[bc]
                                    del bctags[bc]
                            if tags:
                                print(f"{key}_Channel{i}: tags={tags}")
                                bctags[f"{key}_Channel{i}"] = tags

                    elif isinstance(channel[0], list):
                        for schannel in channel:
                            print(f"{schannel}, listcase")

        elif isinstance(Channels, list):
            for i, channel in enumerate(Channels):
                print(f"Channel[{i}]: {channel}")
                tags = []
                for bc in channel:
                    if bc in bctags:
                        tags += bctags[bc]
                        del bctags[bc]
                if tags:
                    print(f"Channel{i}: tags={tags}")
                    bctags[f"Channel{i}"] = tags

    # Physical Surfaces
    if debug:
        print("BCtags:")
    for bctag in bctags:
        pgrp = gmsh.model.addPhysicalGroup(GeomParams["Face"][0], bctags[bctag])
        gmsh.model.setPhysicalName(GeomParams["Face"][0], pgrp, bctag)
        print(bctag, bctags[bctag], pgrp)
        if debug:
            print(bctag, bctags[bctag], pgrp)

    return bctags

