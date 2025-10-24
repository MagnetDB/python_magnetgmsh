"""
Insert geometry manager using Gmsh.

This module manages complex geometries composed of multiple helix and ring components.
The Insert class reads a JSON configuration and creates all components.
"""

import gmsh
import argparse
from typing import List, Any, Optional

# Lazy loading import - automatically detects geometry type
from python_magnetgeo.utils import getObject
from python_magnetgeo.validation import ValidationError

# For type checking only
from python_magnetgeo.Insert import Insert as InsertConfig

from .helix import Helix
from .ring import Ring


def flatten_list(nested_list: List[List[Any]]) -> List[Any]:
    """Flatten a nested list into a single list."""
    return [item for sublist in nested_list for item in sublist]


class Insert:
    """Insert composed of multiple helix and ring components."""

    def __init__(self, config: InsertConfig, add_start_hole: bool = False):
        """Initialize insert from JSON configuration.

        Args:
            config_path: Path to JSON configuration file
        """
        self.config = config
        self.helices = []
        for helixconfig in self.config.helices:
            self.helices.append(Helix(helixconfig, add_start_hole=add_start_hole))

        self.rings = []
        for ringconfig in self.config.rings:
            self.rings.append(Ring(ringconfig))

        self.hangles = self.config.hangles
        self.rangles = self.config.rangles

        print(f"\nTotal components: {len(self.helices)} helices, {len(self.rings)} rings")

    def generate_geometry(self):
        """Generate geometry for all components."""
        print("\n" + "=" * 60)
        print("Generating Insert Geometry")
        print("=" * 60)

        # Generate all helices
        helices_ids = []
        ignore_ids = []
        for i, helix in enumerate(self.helices):
            helix_ids = helix.generate(ignore_ids)
            ignore_ids.extend(helix_ids)
            # print(f'H[{i+1}]: {helix_ids}')
            # eventually rotate: hangle
            # if hangles and hangles[i] != 0:
            #     gmsh.model.occ.rotate([(3, helix_ids[0])], 0, 0, 0, 0, 0, 1, math.radians(hangles[i]))
            #     gmsh.model.occ.synchronize()
            helices_ids.append(helix_ids)
        # print(f'helices_ids: {helices_ids}')

        # Generate all rings
        rings_ids = []
        for i, ring in enumerate(self.rings):
            ring_id = ring.generate()
            # print(f'R[{i+1}]: {ring_id}')

            # position ring on z (ring(i): Helix(i) to Helix(i+1) )
            h = self.helices[i].config.nturns * self.helices[i].config.pitch
            _z = 0
            if i % 2 == 0:
                _z = self.helices[i].config.z2
            else:
                _z = -(self.helices[i].config.z1 + self.ring[i].config.h)

            _z += +self.helices[i].config.z_offset

            print(f"  Translating ring R[{i+1}] to z={_z}")
            gmsh.model.occ.translate([(3, ring_id[0])], 0, 0, _z)
            gmsh.model.occ.synchronize()

            # eventually rotate: rangle
            # if rangles and rangles[i] != 0:
            #     gmsh.model.occ.rotate([(3, ring_id[0])], 0, 0, 0, 0, 0, 1, math.radians(rangles[i]))
            #     gmsh.model.occ.synchronize()

            rings_ids.append(ring_id)
        # print(f'rings_ids: {rings_ids}')

        # TODO assembly
        print("\n=== Assembling Helices and Rings ===")
        # Fragment geometry to create separate volumes
        helices_dimtags = [(3, id) for id in flatten_list(helices_ids)]
        rings_dimtags = [(3, id) for id in flatten_list(rings_ids)]
        # print(f'helices_dimtags: {helices_dimtags},  rings_dimtags: {rings_dimtags}')
        outDimTags, outDimTagsMap = gmsh.model.occ.fragment(
            helices_dimtags, rings_dimtags, removeObject=False, removeTool=False
        )
        # print(f"fragment: outDimTags={outDimTags}, outDimTagsMap={outDimTagsMap}")
        gmsh.model.occ.synchronize()

        # Display parent-child relationships
        print("Parent-child fragment relations:")
        children_dict = {}
        for parent, children in zip(helices_dimtags + rings_dimtags, outDimTagsMap):
            # print(f"  Parent {parent} -> Children {children}")
            for child in children:
                if parent[1] not in children_dict:
                    children_dict[parent[1]] = [child[1]]
                else:
                    children_dict[parent[1]].append(child[1])
        print(f"children_dict: {children_dict}")

        cyl_children_id = [dimtag[1] for dimtag in outDimTagsMap[0]]
        # get volume ids - see fragment_geometry in helix_restructured
        # print('done')

        for j, helix_id in enumerate(helices_ids):
            old_ids = helix_id.copy()
            helices_ids[j] = flatten_list([children_dict[id] for id in old_ids])
            print(f"helix_id old: {old_ids} --> new: {helices_ids[j]}")
            for i, id in enumerate(old_ids):
                if id != helices_ids[j][i]:
                    print("remove helix volume id:", id)
                    gmsh.model.occ.remove([(3, id)], False)
        print(f"helices_ids: {helices_ids}")

        for j, ring_id in enumerate(rings_ids):
            old_ids = ring_id.copy()
            rings_ids[j] = flatten_list([children_dict[id] for id in old_ids])
            print(f"ring_id old: {old_ids} --> new: {rings_ids[j]}")
            for i, id in enumerate(old_ids):
                if id != rings_ids[j][i]:
                    print("remove ring volume id:", id)
                    gmsh.model.occ.remove([(3, id)], False)
        print(f"rings_ids: {rings_ids}")

        gmsh.model.occ.synchronize()

        return helices_ids, rings_ids  # , children_dict

    def create_physical_groups(
        self, helices_ids: List[List[int]], rings_ids: List[List[int]]
    ):  # , children_dict   ):
        """Create physical groups for all components."""
        print("\n=== Creating Physical Groups for Insert ===")

        bcs_names = {}
        for i, helix in enumerate(self.helices):
            # print(f'Creating physical groups for helix {i+1}: {helix.config.name}, IDs: {helices_ids[i]}', end=" --> ")
            # new_ids = [children_dict[id] for id in helices_ids[i]]
            # print(f'New IDs: {flatten_list(new_ids)}')
            # _names = helix.create_physical_groups(flatten_list(new_ids), helix.config.name)
            _names = helix.create_physical_groups(helices_ids[i], helix.config.name)
            bcs_names.update(_names)

        for i, ring in enumerate(self.rings):
            # print(f'Creating physical groups for ring {i+1}: {ring.config.name}, IDs: {rings_ids[i]}', end=" --> ")
            # new_ids = [children_dict[id] for id in rings_ids[i]]
            # print(f'New IDs: {flatten_list(new_ids)}')
            # ring.create_physical_groups(flatten_list(new_ids), ring.config.name)
            ring.create_physical_groups(rings_ids[i], ring.config.name)

        # need to drop physical for V1 for 1st helix and last helix , V0 and V1 for the others
        gmsh.model.removePhysicalGroups([(2, bcs_names["H1_V1"])])
        gmsh.model.removePhysicalGroups([(2, bcs_names[f"H{len(self.helices)}_V1"])])
        for i in range(2, len(self.helices)):
            gmsh.model.removePhysicalGroups([(2, bcs_names[f"H{i}_V0"])])
            gmsh.model.removePhysicalGroups([(2, bcs_names[f"H{i}_V1"])])

        # TODO: rename physical for ring: V1 for odd ring --> BP, V0 for even ring --> HP
        # TODO: group BCs for channels between helices

    # def generate_mesh(self, helices_ids: List[List[int]], rings_ids: List[List[int]], children_dict, mesh_size: Optional[float] = None):
    def generate_mesh(
        self,
        helices_ids: List[List[int]],
        rings_ids: List[List[int]],
        mesh_size: Optional[float] = None,
    ):
        """Generate mesh for the entire insert.

        Args:
            mesh_size: Global mesh size (if None, auto-calculated)
        """
        print("\n=== Generating Mesh ===")

        # Set mesh options
        gmsh.option.setNumber("Geometry.NumSubEdges", 1000)
        gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 40)
        gmsh.option.setNumber("Mesh.MeshSizeMin", 0.1)
        gmsh.option.setNumber("Mesh.MeshSizeMax", 1)
        gmsh.option.setNumber("Mesh.AngleToleranceFacetOverlap", 0.1)

        """
        if mesh_size is None:
            # Auto-calculate mesh size based on first component
            if self.helices:
                for i, helix in enumerate(self.helices):
                    mesh_size = abs(helix.config.r2 - helix.config.r1) / 3.
                
            elif self.rings:
                for i, ring in enumerate(self.rings):
                    mesh_size = abs(ring.config.r2 - ring.config.r1) / 3.
            else:
                mesh_size = 1.0
                
        # else:
        # Set mesh size for all points
        print(f"Mesh size: {mesh_size:.4f}")
        gmsh.model.mesh.setSize(gmsh.model.getEntities(0), mesh_size)
        
        print(f"Mesh size: {mesh_size:.4f}")
        """

        # Generate 3D mesh
        print("Generating 3D mesh...")
        OUTPUT_MESH_FILE = self.config.name + ".msh"
        gmsh.model.mesh.generate(3)
        gmsh.write(OUTPUT_MESH_FILE)
        print(f"Mesh written to: {OUTPUT_MESH_FILE}")


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed arguments namespace
    """
    from ..mesh.axi import get_allowed_algo as get_allowed_algo2D
    from ..mesh.m3d import get_allowed_algo as get_allowed_algo3D

    parser = argparse.ArgumentParser(
        description="Generate insert geometry with multiple helix and ring components",
        add_help=True,
    )
    parser.add_argument("--wd", help="set a working directory", type=str, default="")
    parser.add_argument("-config", type=str, required=True, help="Path to YAML configuration file")
    parser.add_argument("-start_hole", action="store_true", help="Add start hole to helices")
    parser.add_argument("-mesh", action="store_true", help="Generate mesh after geometry creation")
    parser.add_argument(
        "--algo2d",
        help="select an algorithm for 2d mesh",
        type=str,
        choices=get_allowed_algo2D(),
        default="Delaunay",
    )
    parser.add_argument(
        "--algo3d",
        help="select an algorithm for 3d mesh",
        type=str,
        choices=get_allowed_algo3D(),
        default="Delaunay",
    )
    parser.add_argument("-nopopup", action="store_true", help="Do not show Gmsh GUI")
    parser.add_argument("-mesh-size", type=float, default=None, help="Global mesh size (optional)")
    args = parser.parse_args()
    print(f"Arguments: {args}")
    return args


def main():
    """Main function to orchestrate the insert generation process."""
    import os 
    
    print("=" * 60)
    print("Insert Gmsh Geometry Generator")
    print("=" * 60)

    # try:
    # Initialize Gmsh
    gmsh.initialize()
    gmsh.model.add("insert")

    # Parse command line arguments
    args = parse_arguments()
    print("args:", args)

    cwd = os.getcwd()
    if args.wd:
        os.chdir(args.wd)
        
    # Create insert and load configuration
    try:
        insertconfig = getObject(args.config)
    except ValidationError as e:
        # Handle validation errors from python_magnetgeo
        print(f"Validation error: {e}")

    insert = Insert(insertconfig, start_hole=args.start_hole)

    # Generate geometry
    # helices_ids, rings_ids, children_dict = insert.generate_geometry()
    helices_ids, rings_ids = insert.generate_geometry()

    # Create physical groups
    insert.create_physical_groups(helices_ids, rings_ids)  # , children_dict)

    # Generate mesh if requested
    if args.mesh:
        # insert.generate_mesh(helices_ids, rings_ids, children_dict, args.mesh_size)
        from ..mesh.axi import MeshAlgo2D
        from ..mesh.m3d import MeshAlgo3D

        gmsh.option.setNumber("Mesh.Algorithm", MeshAlgo2D[args.algo2d])
        gmsh.option.setNumber("Mesh.Algorithm3D", MeshAlgo3D[args.algo3d])
        insert.generate_mesh(helices_ids, rings_ids, args.mesh_size)

    print("\n" + "=" * 60)
    print("Insert generation completed successfully")
    print("=" * 60)

    # Show GUI if not suppressed
    if not args.nopopup:
        gmsh.fltk.run()

    """
    except Exception as e:
        print(f"\nError during insert generation: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
    """
    if args.wd:
            os.chdir(cwd)

    gmsh.finalize()  # Uncomment if you want to finalize Gmsh

if __name__ == "__main__":
    main()
