"""
Define HTS insert geometry
"""
from typing import Union, List, Optional

import gmsh
from python_magnetgeo.SupraStructure import (
    tape,
    pancake,
    isolation,
    dblpancake,
    HTSinsert,
)


def flatten(S: list) -> list:
    from pandas.core.common import flatten as pd_flatten

    return list(pd_flatten(S))


def tape_ids(tape: tape, x0: float, y0: float, detail: str) -> list:
    """
    create tape for gmsh

    inputs:
    x0, y0: coordinates of lower left point

    returns gmsh ids
    ie. [tape,isolation]
    """

    _tape = gmsh.model.occ.addRectangle(x0, y0, 0, tape.w, tape.h)
    _e = gmsh.model.occ.addRectangle(x0 + tape.w, y0, 0, tape.e, tape.h)

    return [_tape, _e]


def pancake_ids(
    pancake: pancake, x0: float, y0: float, detail: str
) -> Union[int, list]:
    """
    create pancake for gmsh

    inputs:
    x0, y0: coordinates of lower left point
    tag: for tape
    tag_e: for insulation

    returns gmsh ids
    ie. [_mandrin, [tape_id]]
    """
    # print("gmsh/pancake")

    # TODO return either pancake as a whole or detailed
    if detail == "pancake":
        _id = gmsh.model.occ.addRectangle(
            pancake.getR0(), y0, 0, pancake.getW(), pancake.getH()
        )
        return _id
    else:
        _mandrin = gmsh.model.occ.addRectangle(
            pancake.r0 - pancake.mandrin, y0, 0, pancake.mandrin, pancake.getH()
        )
        # print("pancake/gmsh: create mandrin {_mandrin}")
        x0 = pancake.r0
        t_ids = []
        for i in range(pancake.n):
            tape_id = tape_ids(pancake.tape, x0, y0, detail)
            x0 = x0 + pancake.tape.getW()
            t_ids.append(tape_id)

        # gmsh.model.occ.synchronize()
        return [_mandrin, t_ids]


def isolation_ids(isolation: isolation, x0: float, y0: float, detail: str):
    """
    create isolation for gmsh

    inputs:
    x0, y0: coordinates of lower left point

    returns gmsh id
    """

    _id = gmsh.model.occ.addRectangle(
        isolation.r0, y0, 0, isolation.getW(), isolation.getH()
    )
    return _id


def dblpancake_ids(dblpancake: dblpancake, x0: float, y0: float, detail: str):
    """
    create dbl pancake for gmsh

    inputs:
    x0, y0: coordinates of lower left point

    returns tuple of gmsh ids
    ie. (m_id, t_id, e_id, i_id)
    """

    if detail == "dblpancake":
        _id = gmsh.model.occ.addRectangle(
            dblpancake.getR0(), y0, 0, dblpancake.getW(), dblpancake.getH()
        )
        return _id
    else:
        p_ids = []

        _id = pancake_ids(dblpancake.pancake, x0, y0, detail)
        p_ids.append(_id)

        y0 += dblpancake.pancake.getH()
        _isolation_id = isolation_ids(dblpancake.isolation, x0, y0, detail)

        y0 += dblpancake.isolation.getH()
        _id = pancake_ids(dblpancake.pancake, x0, y0, detail)
        p_ids.append(_id)

        # gmsh.model.occ.synchronize()
        return [p_ids, _isolation_id]


def insert_ids(
    HTSInsert: HTSinsert, detail: str, AirData: tuple = (), debug: bool = False
):
    """
    create insert for gmsh

    inputs:
    x0, y0: coordinates of lower left point
    detail: level of precision

    returns gmsh ids depending on detail value
    ie. [dp_ids, isolation_ids]
    """
    # print(f"insert_ids: {HTSinsert}")

    x0 = HTSInsert.r0
    y0 = HTSInsert.z0 - HTSInsert.getH() / 2.0
    n_dp = len(HTSInsert.dblpancakes)

    if detail == "None":
        #
        id = gmsh.model.occ.addRectangle(
            HTSInsert.r0, y0, 0, (HTSInsert.r1 - HTSInsert.r0), HTSInsert.getH()
        )

        # Now create air
        if AirData:
            r0_air = 0
            dr_air = (HTSInsert.r1 - HTSInsert.r0) * AirData[0]
            z0_air = y0 * AirData[1]
            dz_air = (2 * abs(y0)) * AirData[1]
            _id = gmsh.model.occ.addRectangle(r0_air, z0_air, 0, dr_air, dz_air)

            ov, ovv = gmsh.model.occ.fragment([(2, _id)], [(2, id)])
            return (id, (_id, dr_air, z0_air, dz_air))
        return (id, None)

    else:
        dp_ids = []
        i_ids = []

        for i, dp in enumerate(HTSInsert.dblpancakes):
            dp_id = dblpancake_ids(dp, x0, y0, detail)
            dp_ids.append(dp_id)
            y0 += dp.getH()
            if i != n_dp - 1:
                _id = isolation_ids(HTSInsert.isolations[i], x0, y0, detail)
                y0 += HTSInsert.isolations[i].getH()
                i_ids.append(_id)

        # for i,ids in enumerate(i_ids):
        #    print(f"i_ids[{i}]={ids}")

        # Perform BooleanFragment
        # print(f"Create BooleanFragments (detail={detail})")
        for j, dp in enumerate(dp_ids):
            # print(f"HTSInsert gmsh: dp[{j}]")
            if isinstance(dp, list):
                for p in dp:
                    # print(f"HTSInsert gmsh: dp[{j}] p={p}")
                    # dp = [ [p0, p1], isolation ]
                    if isinstance(p, list):
                        # print(f"HTSInsert gmsh: dp[{j}] len(p)={len(p)}, {type(p[0])}, dp[-1]={dp[-1]}" )
                        if len(p) == 2 and isinstance(p[0], int):
                            # detail == pancake
                            # print(f"HTSInsert gmsh: dp[{j}] len(p)={len(p)}, p={p}, i_ids={len(i_ids)}")

                            if j >= 1:
                                ov, ovv = gmsh.model.occ.fragment(
                                    [(2, p[0])], [(2, i_ids[j - 1])]
                                )
                            if j < n_dp - 1:
                                ov, ovv = gmsh.model.occ.fragment(
                                    [(2, p[1])], [(2, i_ids[j])]
                                )
                            ov, ovv = gmsh.model.occ.fragment(
                                [(2, dp[-1])], [(2, p[0]), (2, p[1])]
                            )

                        else:
                            # detail == tape
                            # p = [ mandrin, [[SC, duromag], [SC, duromag], ...] ]
                            # print(f"HTSInsert gmsh: dp[{j}] len(p)={len(p)}, p={p}")
                            flat_p0 = flatten(p[0])
                            flat_p1 = flatten(p[1])
                            if j >= 1:
                                ov, ovv = gmsh.model.occ.fragment(
                                    [(2, i_ids[j - 1])], [(2, l) for l in flat_p0]
                                )
                            if j < n_dp - 1:
                                ov, ovv = gmsh.model.occ.fragment(
                                    [(2, i_ids[j])], [(2, l) for l in flat_p1]
                                )
                            ov, ovv = gmsh.model.occ.fragment(
                                [(2, dp[-1])],
                                [(2, l) for l in flat_p0] + [(2, l) for l in flat_p1],
                            )

            else:
                # detail == dblpancake
                if j >= 1:
                    ov, ovv = gmsh.model.occ.fragment([(2, dp)], [(2, i_ids[j - 1])])
                if j < n_dp - 1:
                    ov, ovv = gmsh.model.occ.fragment([(2, dp)], [(2, i_ids[j])])

        # Now create air
        if AirData:
            y0 = HTSInsert.z0 - HTSInsert.getH() / 2.0  # need to force y0 to init value
            r0_air = 0
            dr_air = (HTSInsert.r1 - HTSInsert.r0) * 2
            z0_air = y0 * 1.2
            dz_air = (2 * abs(y0)) * 1.2
            _id = gmsh.model.occ.addRectangle(r0_air, z0_air, 0, dr_air, dz_air)

            # TODO fragment _id with dp_ids, i_ids
            for j, i_dp in enumerate(i_ids):
                ov, ovv = gmsh.model.occ.fragment([(2, _id)], [(2, i_dp)])

            for j, dp in enumerate(dp_ids):
                # dp = [ [p0, p1], isolation ]
                # print(f"HTSInsert with Air: dp[{j}] detail={detail} dp={dp}")
                if isinstance(dp, list):
                    # detail == pancake|tape
                    # print(_id, flatten(dp))
                    ov, ovv = gmsh.model.occ.fragment(
                        [(2, _id)], [(2, l) for l in flatten(dp)]
                    )
                else:
                    # detail == dblpancake
                    ov, ovv = gmsh.model.occ.fragment([(2, _id)], [(2, dp)])
                    # ov, ovv = gmsh.model.occ.fragment([(2, _id)], [(2, i) for i in i_ids])

            # print("dp_ids:", dp_ids)
            # print("i_ids:", i_ids)
            return ([dp_ids, i_ids], (_id, dr_air, z0_air, dz_air))

        return ([dp_ids, i_ids], ())


def insert_bcs(HTSInsert, name: str, detail: str, ids: tuple, debug: bool = False):
    """
    create bcs groups for gmsh

    inputs:

    returns
    """

    defs = {}
    bcs_defs = {}
    (gmsh_ids, Air_data) = ids

    prefix = ""
    if name:
        prefix = f"{name}_"
    # print("Set Physical Volumes")
    if isinstance(gmsh_ids, list):
        dp_ids = gmsh_ids[0]
        i_ids = gmsh_ids[1]
        for i, isol in enumerate(i_ids):
            ps = gmsh.model.addPhysicalGroup(2, [isol])
            gmsh.model.setPhysicalName(2, ps, f"{prefix}i_dp{i}")
            defs[f"{prefix}i_dp{i}"] = ps
        for i, dp in enumerate(dp_ids):
            # print(f"dp[{i}] = {dp}")
            if detail == "dblpancake":
                ps = gmsh.model.addPhysicalGroup(2, [dp])
                gmsh.model.setPhysicalName(2, ps, f"{prefix}dp{i}")
                defs[f"{prefix}dp{i}"] = ps
            elif detail == "pancake":
                # print("dp:", dp)
                ps = gmsh.model.addPhysicalGroup(2, [dp[0][0]])
                gmsh.model.setPhysicalName(2, ps, f"{prefix}p{0}_dp{i}")
                defs[f"{prefix}p{0}_dp{i}"] = ps
                ps = gmsh.model.addPhysicalGroup(2, [dp[0][1]])
                gmsh.model.setPhysicalName(2, ps, f"{prefix}p{1}_dp{i}")
                defs[f"{prefix}p{1}_dp{i}"] = ps
                ps = gmsh.model.addPhysicalGroup(2, [dp[1]])
                gmsh.model.setPhysicalName(2, ps, f"{prefix}i_dp{i}")
                defs[f"{prefix}i_p{i}"] = ps
            elif detail == "tape":
                # print("HTSInsert/gsmh_bcs (tape):", dp)
                ps = gmsh.model.addPhysicalGroup(2, [dp[1]])
                gmsh.model.setPhysicalName(2, ps, f"{prefix}i_p{i}")
                defs[f"{prefix}i_p{i}"] = ps
                for t in dp[0][0]:
                    # print("p0:", t)
                    if isinstance(t, list):
                        for l, t_id in enumerate(t):
                            ps = gmsh.model.addPhysicalGroup(2, [t_id[0]])
                            gmsh.model.setPhysicalName(
                                2, ps, f"{prefix}sc{l}_p{0}_dp{i}"
                            )
                            defs[f"{prefix}sc{l}_p{0}_dp{i}"] = ps
                            ps = gmsh.model.addPhysicalGroup(2, [t_id[1]])
                            gmsh.model.setPhysicalName(
                                2, ps, f"{prefix}du{l}_p{0}_dp{i}"
                            )
                            defs[f"{prefix}du{l}_p{0}_dp{i}"] = ps
                    else:
                        ps = gmsh.model.addPhysicalGroup(2, [t])
                        gmsh.model.setPhysicalName(2, ps, f"{prefix}mandrin_p{0}_dp{i}")
                        defs[f"{prefix}mandrin_p{0}_dp{i}"] = ps
                        # print(f"HTSInsert/gmsh_bcs: mandrin {t}: {ps}")
                for t in dp[0][1]:
                    # print("p1:", t)
                    if isinstance(t, list):
                        for l, t_id in enumerate(t):
                            ps = gmsh.model.addPhysicalGroup(2, [t_id[0]])
                            gmsh.model.setPhysicalName(
                                2, ps, f"{prefix}sc{l}_p{1}_dp{i}"
                            )
                            defs[f"{prefix}sc{l}_p{1}_dp{i}"] = ps
                            ps = gmsh.model.addPhysicalGroup(2, [t_id[1]])
                            gmsh.model.setPhysicalName(
                                2, ps, f"{prefix}du{l}_p{1}_dp{i}"
                            )
                            defs[f"{prefix}du{l}_p{1}_dp{i}"] = ps
                    else:
                        ps = gmsh.model.addPhysicalGroup(2, [t])
                        gmsh.model.setPhysicalName(2, ps, f"{prefix}mandrin_p{1}_dp{i}")
                        defs[f"{prefix}mandrin_p{1}_dp{i}"] = ps
                        # print(f"HTSInsert/gmsh_bcs: mandrin {t}: {ps}")
    else:
        ps = gmsh.model.addPhysicalGroup(2, [gmsh_ids])
        gmsh.model.setPhysicalName(2, ps, f"{name}")

    # TODO set lc charact on Domains
    # TODO retreive BCs group for Rint, Rext, Top, Bottom

    print("TODO: Set Physical Surfaces")
    # Select the corner point by searching for it geometrically:
    eps = 1e-3
    gmsh.option.setNumber("Geometry.OCCBoundsUseStl", 1)

    bcs_defs[f"{prefix}HP"] = [
        HTSInsert.getR0() * (1 - eps),
        (HTSInsert.z0 - HTSInsert.getH() / 2.0) * (1 - eps),
        HTSInsert.getR1() * (1 + eps),
        (HTSInsert.z0 - HTSInsert.getH() / 2.0) * (1 + eps),
    ]

    bcs_defs[f"{prefix}BP"] = [
        HTSInsert.getR0() * (1 - eps),
        (HTSInsert.z0 + HTSInsert.getH() / 2.0) * (1 - eps),
        HTSInsert.getR1() * (1 + eps),
        (HTSInsert.z0 + HTSInsert.getH() / 2.0) * (1 + eps),
    ]

    bcs_defs[f"{prefix}rInt"] = [
        HTSInsert.getR0() * (1 - eps),
        (HTSInsert.z0 - HTSInsert.getH() / 2.0) * (1 - eps),
        HTSInsert.getR0() * (1 + eps),
        (HTSInsert.z0 + HTSInsert.getH() / 2.0) * (1 + eps),
    ]

    bcs_defs[f"{prefix}rExt"] = [
        HTSInsert.getR1() * (1 - eps),
        (HTSInsert.z0 - HTSInsert.getH() / 2.0) * (1 - eps),
        HTSInsert.getR1() * (1 + eps),
        (HTSInsert.z0 + HTSInsert.getH() / 2.0) * (1 + eps),
    ]

    # Air
    if Air_data:
        (Air_id, dr_air, z0_air, dz_air) = Air_data

        ps = gmsh.model.addPhysicalGroup(2, [Air_id])
        gmsh.model.setPhysicalName(2, ps, "Air")
        defs["Air"] = ps
        # TODO: Axis, Inf
        gmsh.option.setNumber("Geometry.OCCBoundsUseStl", 1)

        eps = 1.0e-6

        bcs_defs[f"ZAxis"] = [-eps, z0_air - eps, +eps, z0_air + dz_air + eps]
        bcs_defs[f"Infty"] = [
            [-eps, z0_air - eps, dr_air + eps, z0_air + eps],
            [dr_air - eps, z0_air - eps, dr_air + eps, z0_air + dz_air + eps],
            [-eps, z0_air + dz_air - eps, dr_air + eps, z0_air + dz_air + eps],
        ]

    return defs
