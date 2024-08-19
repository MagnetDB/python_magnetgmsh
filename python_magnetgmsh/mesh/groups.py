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
    print(f"stags={stags.keys()}")
    print(f"vtags={vtags.keys()}")
    print(f"excluded_tags={excluded_tags}")

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
                print(
                    f"{sname}: _ids={len(_ids)} items, pgrp={pgrp}, dim={GeomParams['Solid'][0]}"
                )

    print("set physical for vtags")
    vdim = GeomParams["Solid"][0]
    sdim = GeomParams["Face"][0]

    if is2D:
        sdim = GeomParams["Solid"][0]

    for vname in vtags:
        pgrp = gmsh.model.addPhysicalGroup(vdim, vtags[vname], name=vname)
        # gmsh.model.setPhysicalName(GeomParams["Solid"][0], pgrp, sname)
        # if debug:
        print(f"{vname}: {len(vtags[vname])}, pgrp={pgrp}, dim={vdim}")

    print("set physical for stags - ignore exclude_tags")
    for sname in stags:
        if not sname in excluded_tags:
            pgrp = gmsh.model.addPhysicalGroup(sdim, stags[sname], name=sname)
            # gmsh.model.setPhysicalName(GeomParams["Solid"][0], pgrp, sname)
            # if debug:
            print(f"{sname}: {len(stags[sname])}, pgrp={pgrp}, dim={sdim}")

    print("PhysicalGroups:")
    vGroups = gmsh.model.getPhysicalGroups()
    for iGroup in vGroups:
        dimGroup = iGroup[0]  # 1D, 2D or 3D
        tagGroup = iGroup[1]
        namGroup = gmsh.model.getPhysicalName(dimGroup, tagGroup)
        print(f"namGroup: {namGroup}, dim: {dimGroup}")

    pass


def create_physicalbcs(
    bctags: dict,
    GeomParams: dict,
    groupCoolingChannels: bool,
    Channels: Union[list, dict],
    hideIsolant: bool,
    groupIsolant: bool,
    debug: bool = False,
) -> None:
    print(
        f"create_physicalbcs: groupCoolingChannels={groupCoolingChannels}, Channels={Channels}, bctags={bctags}"
    )

    exclude_tags = {}
    if hideIsolant:
        # populate exlude_tags
        raise RuntimeError("hideIsolant case not implemented")

    if groupIsolant:
        # select Isolant just like section for Bitter
        # populate exclude_tags
        raise RuntimeError("groupIsolant not implemented")

    def bc_match(name: str, cond: str):
        import re

        # create regexp from cond
        regexp = rf"[i]{cond.capitalize()}_\d+"
        return re.search(regexp, name)

    if groupCoolingChannels:
        print(f"group cooling channels: {Channels}")
        if isinstance(Channels, dict):
            print(f"Channels (dict): {Channels}")
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
            print(f"Channels (list): {Channels}")
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

        print(f"registered bctags: {bctags.keys()}")

    # Physical Surfaces
    if debug:
        print("BCtags:")
    print(f"bctags={bctags}")
    print(f"exlude_tags={exclude_tags}")
    print("create physcicalgroups")
    for bctag in bctags:
        if not bctag in exclude_tags:
            pgrp = gmsh.model.addPhysicalGroup(GeomParams["Face"][0], bctags[bctag])
            gmsh.model.setPhysicalName(GeomParams["Face"][0], pgrp, bctag)
            print(bctag, bctags[bctag], pgrp)
            if debug:
                print(bctag, bctags[bctag], pgrp)

    print("create_physicalbcs done")
