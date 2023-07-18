"""

"""

from typing import Union

import re
import gmsh
from ..utils.lists import flatten


def create_physicalgroups(
    vtags: dict,
    stags: dict,
    excluded_tags: list,
    GeomParams: dict,
    hideIsolant: bool,
    groupIsolant: bool,
    is2D: bool = True,
    debug: bool = False,
) -> None:
    """
    creates PhysicalVolumes
    """

    print(f"create_physicalgroups: is2D={is2D}")

    dict_tags = {}

    if hideIsolant:
        # populate exlude_tags
        raise RuntimeError("hideIsolant case not implemented")

    if groupIsolant:
        # select Isolant just like section for Bitter
        # populate exclude_tags
        raise RuntimeError("groupIsolant not implemented")

    if is2D:
        # Create Physical surfaces
        regexp_stags = [
            r"_Slit\d+",
        ]
        for regexp in regexp_stags:
            match = [solid for solid in list(stags.keys()) if re.search(regexp, solid)]
            print(f"looking for regexp={regexp} (found: {match})")
            if match:
                SGroups = [re.sub(regexp, "", solid) for solid in match]
                SGroups.sort()
                SGroups = list(dict.fromkeys(SGroups))
                for group in SGroups:
                    r = re.compile(f"^{group}")
                    newlist = list(filter(r.match, list(stags.keys())))
                    print(f"{group}: {newlist}")
                    dict_tags[group] = newlist
                    excluded_tags += newlist

        print(f"excluded_tags={excluded_tags}")
        print("set physical for dict_stags")
        for sname, values in dict_tags.items():
            if not sname in excluded_tags:
                _ids = flatten([stags[s] for s in values])
                print(f"sname={sname}, _ids={_ids}")
                pgrp = gmsh.model.addPhysicalGroup(
                    GeomParams["Solid"][0], _ids, name=sname
                )
                # gmsh.model.setPhysicalName(GeomParams["Solid"][0], pgrp, sname)
                # if debug:
                print(f"{sname}: _ids={_ids}, pgrp={pgrp}")

    else:
        raise RuntimeError("3D case not implemented")

    print("set physical for stags - ignore exclude_tags")
    for sname in stags:
        if not sname in excluded_tags:
            pgrp = gmsh.model.addPhysicalGroup(
                GeomParams["Solid"][0], stags[sname], name=sname
            )
            # gmsh.model.setPhysicalName(GeomParams["Solid"][0], pgrp, sname)
            # if debug:
            print(f"{sname}: {stags[sname]}, pgrp={pgrp}")

    print("PhysicalGroups:")
    vGroups = gmsh.model.getPhysicalGroups()
    for iGroup in vGroups:
        dimGroup = iGroup[0]  # 1D, 2D or 3D
        tagGroup = iGroup[1]
        namGroup = gmsh.model.getPhysicalName(dimGroup, tagGroup)
        print(namGroup)

    # get groups


def create_physicalbcs(
    bctags: dict,
    GeomParams: dict,
    groupCoolingChannels: bool,
    Channels: Union[list, dict],
    hideIsolant: bool,
    groupIsolant: bool,
    debug: bool = False,
) -> None:
    exclude_tags = {}

    if hideIsolant:
        # populate exlude_tags
        raise RuntimeError("hideIsolant case not implemented")

    if groupIsolant:
        # select Isolant just like section for Bitter
        # populate exclude_tags
        raise RuntimeError("groupIsolant not implemented")

    if groupCoolingChannels:
        print(f"group cooling channels: {Channels}")
        print(f"registered bctags: {bctags.keys()}")
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
        if not bctag in exclude_tags:
            pgrp = gmsh.model.addPhysicalGroup(GeomParams["Face"][0], bctags[bctag])
            gmsh.model.setPhysicalName(GeomParams["Face"][0], pgrp, bctag)
            print(bctag, bctags[bctag], pgrp)
            if debug:
                print(bctag, bctags[bctag], pgrp)
