import gmsh
import math
from typing import List, Tuple, Optional

# Lazy loading import - automatically detects geometry type
from python_magnetgeo.utils import getObject
from python_magnetgeo.validation import ValidationError

# For type checking only
from python_magnetgeo.Ring import Ring as RingConfig

"""
Configuration for ring geometry parameters.

    r1: float  # Inner radius
    r2: float  # Outer radius
    h: float  # Height
    n: int  # Number of slits
    r_slit: float  # Radius of slit
    e_slit: float  # Radial width of slit
    angular_length: float  # Angular length of slit (degrees)
    name: str = "ring"  # Component name
    add_fillet: bool = False  # Add fillets to slits
    eps: float = 1e-3  # Tolerance for physical groups
"""


class Ring:
    """Ring geometry component."""

    def __init__(self, config: RingConfig):
        """Initialize ring component.

        Args:
            config: Ring configuration parameters
        """
        self.config = config
        self.volume_ids = []
        self.physical_groups = {}
        self.eps = 1.0e-3

    def create_single_slit(self, angular_length_rad: float) -> List[Tuple]:
        """Create a single slit geometry.

        Args:
            angular_length_rad: Angular length in radians

        Returns:
            List of slit dimension tags
        """
        r_slit = (self.config.r[1] + self.config.r[2]) / 2.0
        e_slit = self.config.r[2] - self.config.r[1]
        h = abs(self.config.z[1] - self.config.z[0])
        angular_length_rad = self.config.angle * math.pi / 180.0

        # Create inner and outer cylinders for slit
        slit_int = gmsh.model.occ.addCylinder(
            0, 0, -h / 4.0, 0.0, 0.0, 2 * h, r_slit - e_slit / 2.0, tag=-1, angle=angular_length_rad
        )
        slit_ext = gmsh.model.occ.addCylinder(
            0, 0, -h / 4.0, 0.0, 0.0, 2 * h, r_slit + e_slit / 2.0, tag=-1, angle=angular_length_rad
        )

        # Cut to create slit
        outDimTags, _ = gmsh.model.occ.cut(
            [(3, slit_ext)], [(3, slit_int)], removeObject=True, removeTool=True
        )
        slit = outDimTags
        gmsh.model.occ.synchronize()

        # Center the slit
        gmsh.model.occ.rotate(slit, 0, 0, 0, 0, 0, 1, -angular_length_rad / 2)

        return slit

    def add_fillets_to_slit(self, slit: List[Tuple], angular_length_rad: float) -> List[Tuple]:
        """Add fillets to slit edges.

        Args:
            slit: Slit dimension tags
            angular_length_rad: Angular length in radians

        Returns:
            Modified slit with fillets
        """
        r_slit = (self.config.r[1] + self.config.r[2]) / 2.0
        e_slit = self.config.r[2] - self.config.r[1]
        h = abs(self.config.z[1] - self.config.z[0])
        angular_length_rad = self.config.angle * math.pi / 180.0

        # Create first fillet
        fillet_0 = gmsh.model.occ.addCylinder(
            r_slit,
            0,
            -h / 4.0,
            0.0,
            0.0,
            2 * h,
            e_slit / 2.0,
        )
        gmsh.model.occ.rotate([(3, fillet_0)], 0, 0, 0, 0, 0, 1, -angular_length_rad / 2)

        # Create second fillet
        out = gmsh.model.occ.copy([(3, fillet_0)])
        fillet_1 = out[0][1]
        gmsh.model.occ.rotate([(3, fillet_1)], 0, 0, 0, 0, 0, 1, angular_length_rad)
        gmsh.model.occ.synchronize()

        # Fuse slit with fillets
        outDimTags, _ = gmsh.model.occ.fuse(
            slit, [(3, fillet_0), (3, fillet_1)], removeObject=True, removeTool=True
        )
        gmsh.model.occ.synchronize()

        return outDimTags

    def generate(self) -> List[int]:
        """Generate the ring geometry.

        Returns:
            List of volume IDs created
        """
        print(f"\n=== Generating Ring: {self.config.name} ===")

        r1 = self.config.r[0]
        r2 = self.config.r[-1]
        h = abs(self.config.z[1] - self.config.z[0])
        angular_length_rad = self.config.angle * math.pi / 180.0

        # Create base cylinder
        cyl_int = gmsh.model.occ.addCylinder(0, 0, 0, 0, 0, h, r1)
        cyl_ext = gmsh.model.occ.addCylinder(0, 0, 0, 0, 0, h, r2)

        outDimTags, _ = gmsh.model.occ.cut(
            [(3, cyl_ext)], [(3, cyl_int)], removeObject=True, removeTool=True
        )
        cyl = outDimTags
        gmsh.model.occ.synchronize()

        # Create slits
        theta = 2 * math.pi / self.config.n

        # Create base slit
        slit = self.create_single_slit(angular_length_rad)
        print("slit:", slit)

        # Add fillets if requested
        if self.config.fillets:
            slit = self.add_fillets_to_slit(slit, angular_length_rad)

        # Create and rotate multiple slits
        slits = []
        for i in range(self.config.n):
            out = gmsh.model.occ.copy(slit)
            gmsh.model.occ.rotate(out, 0, 0, 0, 0, 0, 1, i * theta)
            slits.append(out[0])

        # Cut slits from cylinder
        outDimTags, _ = gmsh.model.occ.cut(cyl, slits, removeObject=True, removeTool=True)
        ring = outDimTags

        gmsh.model.occ.remove(slit, True)
        gmsh.model.occ.synchronize()

        ## TODO: need to rotate ring to match zero orientation ##
        angle = (2 * math.pi - theta * self.config.n) / self.config.n
        gmsh.model.occ.rotate(ring, 0, 0, 0, 0, 0, 1, (theta + angle)/2.)

        volume_ids = [ring[0][1]]
        print(f"  Created volumes: {volume_ids}")

        return volume_ids

    def create_physical_groups(self, volume_ids: List[int], prefix=""):
        """Create physical groups for the ring."""
        if len(volume_ids) == 0:
            print(f"  Warning: No volumes for {self.config.name}")
            return

        if prefix != "":
            prefix += "_"

        print(f"\n=== Creating Ring Physical Groups for {self.config.name} ===")
        gmsh.model.addPhysicalGroup(3, volume_ids, name=self.config.name)

        # create surface physical groups
        self.create_boundary_groups(volume_ids, prefix=prefix)

    def create_boundary_groups(self, volume_ids: List[int], prefix=""):
        """Create physical groups for ring boundaries."""
        # TODO retreive BCs as a dict: entries are bcnames and values gmsh physical_surface_id and surfaces_ids
        print(f"\n=== Creating Ring Boundary Physical Groups for {self.config.name} ===")

        eps = self.eps
        r1 = self.config.r[0]
        r2 = self.config.r[-1]
        r_slit = (self.config.r[1] + self.config.r[2]) / 2.0
        e_slit = self.config.r[2] - self.config.r[1]

        # Get bounding box for z-coordinates
        bbox = gmsh.model.occ.getBoundingBox(3, volume_ids[0])
        zmin, zmax = bbox[2], bbox[5]

        # V0 and V1 (top and bottom surfaces)
        # V0: "{prefix}HP" if not self.config.isbpside else "V0"
        # V1: "{prefix}BP" if self.config.isbpside else "V1"
        V0 = gmsh.model.getEntitiesInBoundingBox(
            -r2 - eps, -r2 - eps, zmin - eps, r2 + eps, r2 + eps, zmin + eps, 2
        )
        # TODO: if len(V0) is not 1 - happens when assembling, need further processing for slits
        if len(V0) == 1:
            print(f"Created V0 group: {len(V0)} surfaces (V0={V0})")
            gmsh.model.addPhysicalGroup(2, [tag for (dim, tag) in V0], name=f"{prefix}V0")

        V1 = gmsh.model.getEntitiesInBoundingBox(
            -r2 - eps, -r2 - eps, zmax - eps, r2 + eps, r2 + eps, zmax + eps, 2
        )
        # TODO: if len(V1) is not 1 - happens when assembling, need further processing for slits
        if len(V1) == 1:
            print(f"Created V1 group: {len(V1)} surfaces (V1={V1})")
            gmsh.model.addPhysicalGroup(2, [tag for (dim, tag) in V1], name=f"{prefix}V1")

        # Rint (inner radius surfaces)
        rint = gmsh.model.getEntitiesInBoundingBox(
            -r1 - eps, -r1 - eps, zmin - eps, r1 + eps, r1 + eps, zmax + eps, 2
        )
        gmsh.model.addPhysicalGroup(2, [tag for (dim, tag) in rint], name=f"{prefix}Rint")
        print(f"Found {len(rint)} surfaces for Rint (rint={rint})")

        # Rslit (inner radius surfaces)
        if len(V0) == 1 and len(V1) == 1:
            r = r_slit + e_slit / 2.0 + eps
            rslit = gmsh.model.getEntitiesInBoundingBox(
                -r - eps, -r - eps, zmin - eps, r + eps, r + eps, zmax + eps, 2
            )
            gmsh.model.addPhysicalGroup(
                2,
                [tag for (dim, tag) in rslit if (dim, tag) not in rint + V0 + V1],
                name=f"{prefix}Coolingslit",
            )
            print(f"Found {len(rslit)} surfaces for Rslit (rslit={rslit})")
        else:
            r = r_slit + e_slit / 2.0 + eps
            rslit_in = gmsh.model.getEntitiesInBoundingBox(
                -r - eps, -r - eps, zmin - eps, r + eps, r + eps, zmax + eps, 2
            )
            r = r_slit - e_slit / 2.0 - eps
            rslit_ext = gmsh.model.getEntitiesInBoundingBox(
                -r - eps, -r - eps, zmin - eps, r + eps, r + eps, zmax + eps, 2
            )
            rslit = rslit_in + rslit_ext

            # Remove interface Helix/R
            interface = []
            if len(V0) == 1:
                interface = gmsh.model.getEntitiesInBoundingBox(
                    -r - eps, -r - eps, zmax - eps, r + eps, r + eps, zmax + eps, 2
                )
                interface.append(V1[0])
            else:
                interface = gmsh.model.getEntitiesInBoundingBox(
                    -r - eps, -r - eps, zmin - eps, r + eps, r + eps, zmin + eps, 2
                )
                interface.append(V0[0])

            gmsh.model.addPhysicalGroup(
                2,
                [tag for (dim, tag) in rslit if (dim, tag) not in rint + interface],
                name=f"{prefix}Coolingslit",
            )

        # Rext (inner radius surfaces)
        rext = gmsh.model.getEntitiesInBoundingBox(
            -r2 - eps, -r2 - eps, zmin - eps, r2 + eps, r2 + eps, zmax + eps, 2
        )

        gmsh.model.addPhysicalGroup(
            2,
            [tag for (dim, tag) in rext if (dim, tag) not in rint + V0 + V1 + rslit],
            name=f"{prefix}Rext",
        )
        print(f"Found {len(rext)} surfaces for Rext (rint={rext})")

    def generate_mesh(self, mesh_size: Optional[float] = None):
        """Generate mesh for the entire insert.

        Args:
            mesh_size: Global mesh size (if None, auto-calculated)
        """
        print("\n=== Generating Mesh ===")

        r1 = self.config.r[0]
        r2 = self.config.r[-1]

        if mesh_size is None:
            # Auto-calculate mesh size based on first component
            mesh_size = abs(r2 - r1) / 3.0

        print(f"Mesh size: {mesh_size:.4f}")

        # Set mesh size for all points
        gmsh.model.mesh.setSize(gmsh.model.getEntities(0), mesh_size)

        # Generate 3D mesh
        print("Generating 3D mesh...")
        OUTPUT_MESH_FILE = self.config.name + ".msh"
        gmsh.model.mesh.generate(3)
        gmsh.write(OUTPUT_MESH_FILE)
        print(f"Mesh written to: {OUTPUT_MESH_FILE}")


def main():
    """Main function to orchestrate the helix generation process."""
    import os

    print("=" * 60)
    print("Ring Gmsh Geometry Generator")
    print("=" * 60)

    from .insert import parse_arguments

    try:
        # Initialize Gmsh
        gmsh.initialize()
        gmsh.model.add("ring")

        # Parse command line arguments
        args = parse_arguments()
        cwd = os.getcwd()
        if args.wd:
            os.chdir(args.wd)

        # Load configuration from JSON file
        try:
            ringconfig = getObject(args.config)
        except ValidationError as e:
            # Handle validation errors from python_magnetgeo
            print(f"Validation error: {e}")

        ring = Ring(ringconfig)

        # Generate geometry
        ring_ids = ring.generate()

        # Create physical groups
        ring.create_physical_groups(ring_ids)

        # Generate mesh if requested
        if args.mesh:
            ring.generate_mesh(args.mesh_size)

        print("\n" + "=" * 60)
        print("Ring generation completed successfully")
        print("=" * 60)

        # Show GUI if not suppressed
        if not args.nopopup:
            gmsh.fltk.run()

    except Exception as e:
        print(f"\nError during ring generation: {e}")
        raise
    finally:
        gmsh.finalize()  # Uncomment if you want to finalize Gmsh

    if args.wd:
            os.chdir(cwd)


if __name__ == "__main__":
    main()
