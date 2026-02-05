"""

"""

from typing import Union
import logging

import re
import gmsh
from ..utils.lists import flatten

logger = logging.getLogger(__name__)


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

    logger.info(f"Creating physical groups (2D mode: {is2D})")
    logger.debug(f"Surface tags: {list(stags.keys())}")
    logger.debug(f"Volume tags: {list(vtags.keys())}")
    logger.debug(f"Excluded tags: {excluded_tags}")

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
            logger.debug(f"Searching regexp={regexp}, found {len(match)} matches")
            if match:
                SGroups = [re.sub(regexp, "", solid) for solid in match]
                SGroups.sort()
                SGroups = list(dict.fromkeys(SGroups))
                for group in SGroups:
                    r = re.compile(f"^{group}")
                    newlist = list(filter(r.match, list(stags.keys())))
                    logger.debug(f"Group {group}: {len(newlist)} items")
                    dict_tags[group] = newlist
                    excluded_tags += newlist

        logger.debug(f"Total excluded tags: {len(excluded_tags)}")
        logger.debug("Setting physical groups for dict_stags")
        for sname, values in dict_tags.items():
            if not sname in excluded_tags:
                _ids = flatten([stags[s] for s in values])
                logger.debug(f"Creating physical group: {sname} with {len(_ids)} elements")
                pgrp = gmsh.model.addPhysicalGroup(
                    GeomParams["Solid"][0], _ids, name=sname
                )
                logger.debug(f"  Physical group {sname}: {len(_ids)} elements, pgrp={pgrp}")

    logger.debug("Setting physical groups for volume tags")
    vdim = GeomParams["Solid"][0]
    sdim = GeomParams["Face"][0]

    if is2D:
        sdim = GeomParams["Solid"][0]

    for vname in vtags:
        pgrp = gmsh.model.addPhysicalGroup(vdim, vtags[vname], name=vname)
        logger.debug(f"Volume group {vname}: {len(vtags[vname])} elements, pgrp={pgrp}")

    logger.debug("Setting physical groups for surface tags (excluding excluded tags)")
    for sname in stags:
        if not sname in excluded_tags:
            pgrp = gmsh.model.addPhysicalGroup(sdim, stags[sname], name=sname)
            logger.debug(f"Surface group {sname}: {len(stags[sname])} elements, pgrp={pgrp}")

    logger.info("Physical groups created:")
    vGroups = gmsh.model.getPhysicalGroups()
    for iGroup in vGroups:
        dimGroup = iGroup[0]  # 1D, 2D or 3D
        tagGroup = iGroup[1]
        namGroup = gmsh.model.getPhysicalName(dimGroup, tagGroup)
        logger.debug(f"  {namGroup} (dim={dimGroup})")

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
    logger.info("Creating physical boundary conditions")
    logger.debug(f"groupCoolingChannels={groupCoolingChannels}, Channels={type(Channels).__name__ if Channels else None}")

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
        logger.debug(f"Grouping cooling channels")
        if isinstance(Channels, dict):
            logger.debug(f"Processing channels from dict with {len(Channels)} keys")
            for key in Channels:
                logger.debug(f"Processing channel group: {key}")
                for i, channel in enumerate(Channels[key]):
                    if isinstance(channel[0], str):
                        logger.debug(f"Processing string-based channel: {channel}")
                        for bc in channel:
                            tags = []
                            for bc in channel:
                                if bc in bctags:
                                    tags += bctags[bc]
                                    del bctags[bc]
                            if tags:
                                logger.debug(f"Created channel group {key}_Channel{i}: {len(tags)} tags")
                                bctags[f"{key}_Channel{i}"] = tags

                    elif isinstance(channel[0], list):
                        for schannel in channel:
                            logger.debug(f"Processing list-based sub-channel: {schannel}")

        elif isinstance(Channels, list):
            logger.debug(f"Processing channels from list with {len(Channels)} items")
            for i, channel in enumerate(Channels):
                logger.debug(f"Processing channel {i}: {channel}")
                tags = []
                for bc in channel:
                    if bc in bctags:
                        tags += bctags[bc]
                        del bctags[bc]
                if tags:
                    logger.debug(f"Created Channel{i}: {len(tags)} tags")
                    bctags[f"Channel{i}"] = tags

        logger.debug(f"Registered boundary condition tags: {list(bctags.keys())}")

    # Physical Surfaces
    logger.debug("Creating physical groups for boundary conditions")
    logger.debug(f"BC tags: {list(bctags.keys())}")
    logger.debug(f"Excluded tags: {exclude_tags}")
    logger.debug("Creating physical groups...")
    for bctag in bctags:
        if not bctag in exclude_tags:
            pgrp = gmsh.model.addPhysicalGroup(GeomParams["Face"][0], bctags[bctag])
            gmsh.model.setPhysicalName(GeomParams["Face"][0], pgrp, bctag)
            logger.debug(f"BC group {bctag}: {len(bctags[bctag])} elements, pgrp={pgrp}")

    logger.info("Physical boundary conditions created")
