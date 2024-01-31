"""
Define HTS insert geometry
"""

import gmsh
from python_magnetgeo.SupraStructure import (
    tape,
    pancake,
    isolation,
    dblpancake,
    HTSinsert,
)

from .utils.lists import flatten


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
) -> int | list:
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
    print(f"insert_ids: HTSInsert={HTSinsert}, detail={detail}")

    x0 = HTSInsert.r0
    y0 = HTSInsert.z0 - HTSInsert.getH() / 2.0
    n_dp = len(HTSInsert.dblpancakes)

    if detail == "None":
        #
        id = gmsh.model.occ.addRectangle(
            HTSInsert.r0, y0, 0, (HTSInsert.r1 - HTSInsert.r0), HTSInsert.getH()
        )

        # Now create air
        Air_data = ()
        if AirData:
            r0_air = 0
            dr_air = (HTSInsert.r1 - HTSInsert.r0) * AirData[0]
            z0_air = y0 * AirData[1]
            dz_air = (2 * abs(y0)) * AirData[1]
            
            A_id = gmsh.model.occ.addRectangle(r0_air, z0_air, 0, dr_air, dz_air)
            ov, ovv = gmsh.model.occ.fragment([(2, A_id)], [(2, id)])
            gmsh.model.occ.synchronize()
            
            Air_data = (A_id, dr_air, z0_air, dz_air)

        return (id, Air_data)

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
            print(f"HTSInsert gmsh: dp[{j}]")
            if isinstance(dp, list):
                for p in dp:
                    if debug:
                        print(f"HTSInsert gmsh: dp[{j}] type(p)={type(p)}")
                    if isinstance(p, list):
                        if debug:
                            print(
                                f"HTSInsert gmsh: dp[{j}] len(p)={len(p)}, type(p[0])={type(p[0])}, len(p)={len(p)}, dp[-1]={dp[-1]}"
                            )
                        if len(p) == 2 and isinstance(p[0], int):
                            # detail == pancake
                            # print(
                            #    f"HTSInsert gmsh: dp[{j}] len(p)={len(p)}, p={p}, i_ids={len(i_ids)}"
                            # )

                            if j >= 1:
                                ov, ovv = gmsh.model.occ.fragment(
                                    [(2, p[0])], [(2, i_ids[j - 1])]
                                )
                                gmsh.model.occ.synchronize()
                            if j < n_dp - 1:
                                ov, ovv = gmsh.model.occ.fragment(
                                    [(2, p[1])], [(2, i_ids[j])]
                                )
                                gmsh.model.occ.synchronize()
                            ov, ovv = gmsh.model.occ.fragment(
                                [(2, dp[-1])], [(2, p[0]), (2, p[1])]
                            )
                            gmsh.model.occ.synchronize()

                        else:
                            # detail == tape
                            # p = [ mandrin, [[SC, duromag], [SC, duromag], ...] ]
                            if debug:
                                print(
                                    f"HTSInsert gmsh: dp[{j}] len(p)={len(p)}, type(p[0])={type(p[0])}"
                                )
                            flat_p0 = flatten(p[0])
                            # print(f"flatten p0: {len(flat_p0)}")
                            flat_p1 = flatten(p[1])
                            # print(f"flatten p1: {len(flat_p1)}")
                            start = 0
                            end = len(flat_p0)
                            step = 10
                            if j >= 1:
                                for k in range(start, end, step):
                                    x = k
                                    # print(
                                    #     f"ids/chunk[j={j}, x={x}, x+step={x+step}]: flat_p0"
                                    # )
                                    ov, ovv = gmsh.model.occ.fragment(
                                        [(2, i_ids[j - 1])],
                                        [(2, l) for l in flat_p0[x : x + step]],
                                    )
                                    gmsh.model.occ.synchronize()

                            start = 0
                            end = len(flat_p1)
                            step = 10
                            if j < n_dp - 1:
                                for k in range(start, end, step):
                                    x = k
                                    # print(
                                    #     f"ids/chunk[j={j}, x={x}, x+step={x+step}]: flat_p1"
                                    # )
                                    ov, ovv = gmsh.model.occ.fragment(
                                        [(2, i_ids[j])],
                                        [(2, l) for l in flat_p1[x : x + step]],
                                    )
                                    gmsh.model.occ.synchronize()
                            for k in range(start, end, step):
                                x = k
                                # print(
                                #     f"dp/chunk[j={j}, x={x}, x+step={x+step}]: flat_p1"
                                # )
                                ov, ovv = gmsh.model.occ.fragment(
                                    [(2, dp[-1])],
                                    [(2, l) for l in flat_p1]
                                    + [(2, l) for l in flat_p1[x : x + step]],
                                )
                                gmsh.model.occ.synchronize()

            else:
                # detail == dblpancake
                if j >= 1:
                    ov, ovv = gmsh.model.occ.fragment([(2, dp)], [(2, i_ids[j - 1])])
                    gmsh.model.occ.synchronize()
                if j < n_dp - 1:
                    ov, ovv = gmsh.model.occ.fragment([(2, dp)], [(2, i_ids[j])])
                    gmsh.model.occ.synchronize()

        # Now create air
        Air_data = ()
        if AirData:
            print("HTSInsert gmsh: create air")
            y0 = HTSInsert.z0 - HTSInsert.getH() / 2.0  # need to force y0 to init value
            r0_air = 0
            dr_air = HTSInsert.r1 * AirData[0]
            z0_air = y0 * AirData[1]
            dz_air = (2 * abs(y0)) * AirData[1]
            _id = gmsh.model.occ.addRectangle(r0_air, z0_air, 0, dr_air, dz_air)

            # TODO fragment _id with dp_ids, i_ids
            for j, i_dp in enumerate(i_ids):
                ov, ovv = gmsh.model.occ.fragment([(2, _id)], [(2, i_dp)])
                gmsh.model.occ.synchronize()

            for j, dp in enumerate(dp_ids):
                # dp = [ [p0, p1], isolation ]
                print(f"HTSInsert with Air: dp[{j}] detail={detail}")
                if isinstance(dp, list):
                    # detail == pancake|tape
                    print(f"HTSInsert with Air: dp[{j}] len={len(dp)}")
                    flat_dp = flatten(dp)
                    start = 0
                    end = len(flat_dp)
                    step = 10
                    for k in range(start, end, step):
                        x = k
                        print(f"chunk[j={j}, x={x}, x+step={x+step}]: flat_dp")
                        ov, ovv = gmsh.model.occ.fragment(
                            [(2, _id)], [(2, l) for l in flat_dp[x : x + step]]
                        )
                        gmsh.model.occ.synchronize()
                else:
                    # detail == dblpancake
                    print(f"HTSInsert with Air: dp[{j}] dp={dp}")
                    ov, ovv = gmsh.model.occ.fragment([(2, _id)], [(2, dp)])
                    gmsh.model.occ.synchronize()
                    # ov, ovv = gmsh.model.occ.fragment([(2, _id)], [(2, i) for i in i_ids])

            # print("dp_ids:", dp_ids)
            # print("i_ids:", i_ids)
            Air_data = (_id, dr_air, z0_air, dz_air)

        print("insert_ids: done")
        return ([dp_ids, i_ids], Air_data)


def insert_bcs(
    HTSInsert: HTSinsert, name: str, detail: str, ids: tuple, debug: bool = False
):
    """
    create bcs groups for gmsh

    inputs:

    returns
    """
    print(f"insert_bcs: HTSInsert={HTSInsert}, name{name}, detail={detail}")

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
            gmsh.model.setPhysicalName(2, ps, f"{prefix}i{i}")
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
                gmsh.model.setPhysicalName(2, ps, f"{prefix}p0_dp{i}")
                defs[f"{prefix}p0_dp{i}"] = ps
                ps = gmsh.model.addPhysicalGroup(2, [dp[0][1]])
                gmsh.model.setPhysicalName(2, ps, f"{prefix}p1_dp{i}")
                defs[f"{prefix}p1_dp{i}"] = ps
                ps = gmsh.model.addPhysicalGroup(2, [dp[1]])
                gmsh.model.setPhysicalName(2, ps, f"{prefix}i_dp{i}")
                defs[f"{prefix}i_p{i}"] = ps
            elif detail == "tape":
                # print("HTSInsert/gsmh_bcs (tape):", dp)
                ps = gmsh.model.addPhysicalGroup(2, [dp[1]])
                gmsh.model.setPhysicalName(2, ps, f"{prefix}i_dp{i}")
                defs[f"{prefix}i_p{i}"] = ps
                for t in dp[0][0]:
                    # print("p0:", t)
                    if isinstance(t, list):
                        for l, t_id in enumerate(t):
                            ps = gmsh.model.addPhysicalGroup(2, [t_id[0]])
                            gmsh.model.setPhysicalName(2, ps, f"{prefix}sc{l}_p0_dp{i}")
                            defs[f"{prefix}sc{l}_p0_dp{i}"] = ps
                            ps = gmsh.model.addPhysicalGroup(2, [t_id[1]])
                            gmsh.model.setPhysicalName(2, ps, f"{prefix}du{l}_p0_dp{i}")
                            defs[f"{prefix}du{l}_p0_dp{i}"] = ps
                    else:
                        ps = gmsh.model.addPhysicalGroup(2, [t])
                        gmsh.model.setPhysicalName(2, ps, f"{prefix}mandrin_p0_dp{i}")
                        defs[f"{prefix}mandrin_p0_dp{i}"] = ps
                        # print(f"HTSInsert/gmsh_bcs: mandrin {t}: {ps}")
                for t in dp[0][1]:
                    # print("p1:", t)
                    if isinstance(t, list):
                        for l, t_id in enumerate(t):
                            ps = gmsh.model.addPhysicalGroup(2, [t_id[0]])
                            gmsh.model.setPhysicalName(2, ps, f"{prefix}sc{l}_p1_dp{i}")
                            defs[f"{prefix}sc{l}_p1_dp{i}"] = ps
                            ps = gmsh.model.addPhysicalGroup(2, [t_id[1]])
                            gmsh.model.setPhysicalName(2, ps, f"{prefix}du{l}_p1_dp{i}")
                            defs[f"{prefix}du{l}_p1_dp{i}"] = ps
                    else:
                        ps = gmsh.model.addPhysicalGroup(2, [t])
                        gmsh.model.setPhysicalName(2, ps, f"{prefix}mandrin_p{1}_dp{i}")
                        defs[f"{prefix}mandrin_p1_dp{i}"] = ps
                        # print(f"HTSInsert/gmsh_bcs: mandrin {t}: {ps}")
    else:
        ps = gmsh.model.addPhysicalGroup(2, [gmsh_ids])
        gmsh.model.setPhysicalName(2, ps, f"{name}")

    # TODO set lc charact on Domains
    # TODO retreive BCs group for Rint, Rext, Top, Bottom

    print("TODO: Set Physical Surfaces")
    # Select the corner point by searching for it geometrically:
    gmsh.option.setNumber("Geometry.OCCBoundsUseStl", 1)

    if isinstance(gmsh_ids, list):
        dp_ids = gmsh_ids[0]
        i_ids = gmsh_ids[1]
        z = HTSInsert.z1
        for i, isol in enumerate(i_ids):
            z += HTSInsert.dblpancakes[i].getH()

        n_dp = HTSInsert.getN()
        z = HTSInsert.z1
        for i, dp in enumerate(dp_ids):
            # print(f"dp[{i}] = {dp}")
            dp = HTSInsert.dblpancakes[i]
            isolant = HTSInsert.isolations[i]
            if detail == "dblpancake":
                bcs_defs[f"{prefix}dp{i}_rInt"] = [
                    dp.getR0(),
                    z,
                    dp.getR0(),
                    z + dp.getH(),
                ]

                bcs_defs[f"{prefix}dp{i}_rExt"] = [
                    dp.getR1(),
                    z,
                    dp.getR1(),
                    z + dp.getH(),
                ]
                # not yet z += dp.getH()
            elif detail == "pancake":
                # print("dp:", dp)
                p = dp.pancake
                dp_i = dp.isolation
                bcs_defs[f"{prefix}p0_dp{i}_rInt"] = [
                    p.getR0(),
                    z,
                    p.getR0(),
                    (z + p.getH()),
                ]

                bcs_defs[f"{prefix}p0_dp{i}_rExt"] = [
                    p.getR1(),
                    z,
                    p.getR1(),
                    (z + p.getH() + isolant.getH()),
                ]

                z += p.getH()

                bcs_defs[f"{prefix}i_dp{i}_rInt"] = [
                    p.getR0(),
                    (z),
                    p.getR0(),
                    (z + dp_i.getH()),
                ]

                bcs_defs[f"{prefix}i_dp{i}_rExt"] = [
                    p.getR1(),
                    (z),
                    p.getR1(),
                    (z + dp_i.getW()),
                ]
                z += dp_i.getH()

                bcs_defs[f"{prefix}p1_dp{i}_rInt"] = [p.getR0(), (z), p.getR0(), (z)]

                bcs_defs[f"{prefix}p1_dp{i}_rExt"] = [
                    p.getR1(),
                    z,
                    p.getR1(),
                    (z + dp_i.getH()),
                ]

            elif detail == "tape":
                # print("HTSInsert/gsmh_bcs (tape):", dp)
                p = dp.pancake
                dp_i = dp.isolation
                tape = dp.pancake.tape
                r0 = p.getR0()
                for l in range(p.getN()):
                    bcs_defs[f"{prefix}sc{l}_p0_dp{i}_rInt"] = [
                        r0,
                        z,
                        r0,
                        (z + tape.getH()),
                    ]

                    bcs_defs[f"{prefix}sc{l}_p0_dp{i}_rExt"] = [
                        r0 + tape.getW_Sc(),
                        z,
                        r0 + tape.getW_Sc(),
                        (z + tape.getH()),
                    ]
                    r0 += tape.getW()

                bcs_defs[f"{prefix}mandrin_p0_dp{i}_rInt"] = [
                    p.getMandrin(),
                    z,
                    p.getMandrin(),
                    z + p.getH(),
                ]
                z += tape.getH()

                # add isolant here
                bcs_defs[f"{prefix}i_dp{i}_rInt"] = [
                    dp_i.getR0(),
                    z,
                    dp_i.getR0(),
                    (z + dp_i.getH()),
                ]

                bcs_defs[f"{prefix}i_dp{i}_rExt"] = [
                    dp_i.getR0() + dp_i.getW(),
                    z,
                    dp_i,
                    z + dp_i.getH(),
                ]
                z += dp_i.getH()

                r0 = p.getR0()
                for l in range(p.getN()):
                    bcs_defs[f"{prefix}sc{l}_p1_dp{i}_rInt"] = [
                        r0,
                        z,
                        r0,
                        z + tape.getH(),
                    ]

                    bcs_defs[f"{prefix}sc{l}_p1_dp{i}_rExt"] = [
                        r0 + tape.getW_Sc(),
                        z,
                        r0 + tape.getW_Sc(),
                        z + tape.getH(),
                    ]
                    r0 += tape.getW()

                bcs_defs[f"{prefix}mandrin_p1_dp{i}_rInt"] = [
                    p.getMandrin(),
                    z,
                    p.getMandrin(),
                    z + p.getH(),
                ]

            # update z
            z += dp.getH()
            if i < n_dp - 1:
                isolant = HTSInsert.isolations[i]
                bcs_defs[f"{prefix}i_dp{i}_rInt"] = [
                    isolant.getR0(),
                    z,
                    isolant.getR0(),
                    (z + isolant.getH()),
                ]

                bcs_defs[f"{prefix}i_dp{i}_rExt"] = [
                    isolant.getR0() + isolant.getW(),
                    z,
                    HTSInsert.getR1(),
                    (z + isolant.getH()),
                ]
                z += isolant.getW()
    else:
        bcs_defs[f"{prefix}HP"] = [
            HTSInsert.getR0(),
            (HTSInsert.z0 - HTSInsert.getH() / 2.0),
            HTSInsert.getR1(),
            (HTSInsert.z0 - HTSInsert.getH() / 2.0),
        ]

        bcs_defs[f"{prefix}BP"] = [
            HTSInsert.getR0(),
            (HTSInsert.z0 + HTSInsert.getH() / 2.0),
            HTSInsert.getR1(),
            (HTSInsert.z0 + HTSInsert.getH() / 2.0),
        ]

        bcs_defs[f"{prefix}rInt"] = [
            HTSInsert.getR0(),
            (HTSInsert.z0 - HTSInsert.getH() / 2.0),
            HTSInsert.getR0(),
            (HTSInsert.z0 + HTSInsert.getH() / 2.0),
        ]

        bcs_defs[f"{prefix}rExt"] = [
            HTSInsert.getR1(),
            (HTSInsert.z0 - HTSInsert.getH() / 2.0),
            HTSInsert.getR1(),
            (HTSInsert.z0 + HTSInsert.getH() / 2.0),
        ]

    # Air
    if Air_data:
        (Air_id, dr_air, z0_air, dz_air) = Air_data

        ps = gmsh.model.addPhysicalGroup(2, [Air_id])
        gmsh.model.setPhysicalName(2, ps, "Air")
        defs["Air"] = ps
        # TODO: Axis, Inf
        gmsh.option.setNumber("Geometry.OCCBoundsUseStl", 1)

        bcs_defs[f"ZAxis"] = [0, z0_air, 0, z0_air + dz_air]
        bcs_defs[f"Infty"] = [
            [0, z0_air, dr_air, z0_air],
            [dr_air, z0_air, dr_air, z0_air + dz_air],
            [0, z0_air + dz_air, dr_air, z0_air + dz_air],
        ]

    print("insert_bcs: done")
    return defs
