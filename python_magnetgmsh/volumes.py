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
    for stag in stags:
        pgrp = gmsh.model.addPhysicalGroup(GeomParams["Solid"][0], stags[stag])
        gmsh.model.setPhysicalName(GeomParams["Solid"][0], pgrp, stag)
        if debug:
            print(f"{stag}: {stags[stag]}, pgrp={pgrp}")

    return stags


def create_bcs(
    tree,
    gname,
    GeomParams,
    NHelices,
    innerLead_exist,
    outerLead_exist,
    groupCoolingChannels,
    Channels,
    compound,
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

            # keep only H0_V0 if no innerlead otherwise keep Lead_V0
            # keep only H14_V1 if not outerlead otherwise keep outerlead V1
            # print(innerLead_exist, re.search('H\d+_V0',sname))
            if innerLead_exist:
                match = re.search("H\d+_V0", sname)
                if match or (sname.startswith("Inner") and sname.endswith("V1")):
                    skip = True
            else:
                match = re.search("H\d+_V0", sname)
                if match:
                    num = int(sname.split("_")[0].replace("H", ""))
                    if num != 1:
                        skip = True
            if outerLead_exist:
                match = re.search("H\d+_V1", sname)
                if match:
                    skip = True
                if sname.startswith("Outer") and sname.endswith("V1"):
                    skip = True
            else:
                match = re.search("H\d+_V1", sname)
                if match:
                    num = int(sname.split("_")[0].replace("H", ""))
                    if num != NHelices:
                        skip = True

            # groupCoolingChannels option (see Tools_SMESH::CreateChannelSubMeshes for HL and for HR ??) + watch out when hideIsolant is True
            # TODO case of HR: group HChannel and muChannel per Helix
            if groupCoolingChannels:
                print(f"groupCoolingChannels: sname={sname} type={type(Channels)}")
                if isinstance(Channels, dict):
                    for key in Channels:
                        if key in sname:
                            for j, channel in enumerate(Channels[key]):
                                for cname in channel:
                                    if sname.endswith(cname):
                                        print(
                                            f"sname={sname}, cname={cname}, channel={channel}, key={key} dictcase"
                                        )
                                        sname = f"{key}_Channel{j}"
                                        break
                elif isinstance(Channels, list):
                    print(f"Channels]: {Channels}")
                    for j, channel in enumerate(Channels):
                        print(f"Channel[{j}]: {channel}")
                        for cname in channel:
                            if sname.endswith(cname):
                                print(f"sname={sname}, cname={cname} listcase")
                                sname = f"Channel{j}"
                                break

                # TODO make it more general
                # so far assume only one insert and  insert is the 1st compound
                if compound:
                    if sname.startswith(compound[0]):
                        if "_rInt" in sname or "_rExt" in sname:
                            skip = True
                        if "_IrInt" in sname or "_IrExt" in sname:
                            skip = True
                        if "_iRint" in sname or "_iRext" in sname:
                            skip = True
                else:
                    if "_rInt" in sname or "_rExt" in sname:
                        skip = True
                    if "_IrInt" in sname or "_IrExt" in sname:
                        skip = True
                    if "_iRint" in sname or "_iRext" in sname:
                        skip = True

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

