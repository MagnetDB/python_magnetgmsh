# Python Magnet Gmsh

<!--
[![PyPI version](https://img.shields.io/pypi/v/python_magnetgmsh.svg)](https://pypi.python.org/pypi/python_magnetgmsh)
[![Build Status](https://img.shields.io/travis/Trophime/python_magnetgmsh.svg)](https://travis-ci.com/Trophime/python_magnetgmsh)
[![Documentation Status](https://readthedocs.org/projects/python-magnetgmsh/badge/?version=latest)](https://python-magnetgmsh.readthedocs.io/en/latest/?version=latest)
[![Updates](https://pyup.io/repos/github/Trophime/python_magnetgmsh/shield.svg)](https://pyup.io/repos/github/Trophime/python_magnetgmsh/)
-->

Python Magnet Gmsh provides tools to create CAD and mesh files using Gmsh for high-field magnet geometries.

- **Free software**: MIT license
- **Documentation**: https://python-magnetgmsh.readthedocs.io

## Version 0.1.0 - Breaking Changes

**This release introduces breaking changes.** See [API Breaking Changes](#api-breaking-changes) section below.

## Features

- **Gmsh CAD/Mesh Generation** - Create CAD and mesh files from magnetgeo YAML configurations
- **XAO Format Support** - Convert Salome XAO files to Gmsh mesh format
- **2D Sector Meshes** - Generate specialized 2D meshes for Bitter sectors
- **Mesh Transformation** - Rotate meshes around arbitrary axes
- **Command-line Tools** - Easy-to-use CLI interface
- **Type Safety** - Full type annotations for better IDE support

## Requirements

- **Python**: 3.9 or higher
- **python_magnetgeo**: 1.0.0 or higher (< 2.0.0)
- **Gmsh**: 4.13.1 or higher
- **PyYAML**: 6.0 or higher
- **NumPy**: 1.24.0 or higher

## Installation

### Using pip

```bash
pip install python_magnetgmsh
```

### Development Installation

```bash
# Clone the repository
git clone https://github.com/Trophime/python_magnetgmsh.git
cd python_magnetgmsh

# Create virtual environment
python -m venv --system-site-packages magnetgmsh-env
source ./magnetgmsh-env/bin/activate  # On Windows: magnetgmsh-env\Scripts\activate

# Install in development mode
pip install -e .
```

### Using Latest Gmsh Development Version

```bash
pip install -i https://gmsh.info/python-packages-dev --force-reinstall --no-cache-dir gmsh
```

## Quick Start

### Method 1: Using Command-Line Tools

After installation, you can use the convenient command-line tools:

```bash
# Generate mesh from YAML configuration
python_magnetgmsh test.yaml --wd /data/geometries --mesh --show

# Convert XAO to Gmsh mesh
python_xao2gmsh test-Axi.xao --geo test.yaml --wd /data/geometries mesh --group CoolingChannels
```

### Method 2: Using Python Module Interface

```bash
# Create mesh from magnetgeo YAML file (Axisymmetric)
python -m python_magnetgmsh.cli --wd /data/geometries test.yaml --thickslit --mesh --lc --show

# Create 2D mesh for Bitter sector
python -m python_magnetgmsh.m2d.Bitter2D --wd /data/geometries M9_Bi.yaml --mesh --lc 20 --show

# Convert Salome XAO to Gmsh mesh
python -m python_magnetgmsh.xao2msh --wd /data/geometries test-Axi.xao --geo test.yaml mesh --group CoolingChannels

# Rotate a mesh around X-axis
python -m python_magnetgmsh.rotate HL-31_H1.msh --wd /data/meshes --rotate 45
```

### CLI Options

**Main CLI (`python_magnetgmsh.cli`)**:
- `--wd`: Set working directory
- `--air`: Activate air generation with ratios `infty_Rratio infty_Zratio`
- `--thickslit`: Model thick cooling slits
- `--mesh`: Activate mesh generation
- `--algo2d`: Select 2D mesh algorithm (Delaunay, MeshAdapt, etc.)
- `--scaling`: Scale to meters (default unit is mm)
- `--lc`: Load mesh size from file
- `--show`: Display Gmsh GUI
- `--verbose`: Enable verbose output
- `--debug`: Enable debug mode

**XAO to Mesh Converter (`python_magnetgmsh.xao2msh`)**:
- `--geo`: YAML geometry configuration file
- `--wd`: Working directory
- `mesh`: Generate mesh from XAO
- `--group`: Specify physical group name

**Mesh Rotation (`python_magnetgmsh.rotate`)**:
- `--wd`: Working directory
- `--rotate`: Rotation angle in degrees (around X-axis)
- `--show`: Display result in Gmsh GUI

## Usage Examples

### Example 1: Basic Mesh Generation

```bash
# Generate CAD and mesh from YAML
python_magnetgmsh M9_Bitters.yaml --wd /data/geometries --mesh --show
```

### Example 2: Mesh with Air Domain

```bash
# Generate mesh with surrounding air domain
python_magnetgmsh test.yaml --wd /data/geometries --thickslit --air 10 6 --mesh
```

### Example 3: XAO Conversion

```bash
# Convert Salome XAO file to Gmsh mesh with physical groups
python_xao2gmsh M9_HLtest-Axi.xao --geo M9_HLtest.yaml --wd /data/cad mesh --group CoolingChannels
```

### Example 4: Mesh Transformation

```bash
# Rotate mesh 45 degrees around X-axis
python -m python_magnetgmsh.rotate HL-31_H1.msh --wd /data/meshes --rotate 45
# Output: HL-31_H1-rotate-45.0deg.msh
```

## Supported Geometry Types

The following geometry types from `python_magnetgeo` are supported:

| Type | Description |
|------|-------------|
| `Insert` | Complete magnet insert assembly |
| `Helix` | Helical coil geometry |
| `Bitter` | Single Bitter plate |
| `Bitters` | Multiple Bitter plates |
| `Supra` | Superconducting coil |
| `Supras` | Multiple superconducting coils |
| `MSite` | Measurement site configuration |

## API Breaking Changes

### Version 0.1.0 Changes

This version introduces several breaking changes related to `python_magnetgeo` 1.0.0 dependency:

#### 1. Strict Dependency Version

**Breaking Change**: `python_magnetgeo` version must be >= 1.0.0 and < 2.0.0

```python
# The package now requires:
python-magnetgeo>=1.0.0,<2.0.0
```

**Impact**: Package will fail to import if `python_magnetgeo` is outside this range.

**Migration**:
```bash
pip install "python-magnetgeo>=1.0.0,<2.0.0"
```

#### 2. Python Version Requirement

**Breaking Change**: Minimum Python version increased to 3.9

**Migration**: Upgrade to Python 3.9 or higher

#### 3. Geometry Loading Function Return Types

**Breaking Change**: All geometry loading functions now return `GeometryLoadResult` objects

```python
# Old code (no longer works):
solid_names, channels, isolants = Bitter_Gmsh(...)

# New code:
result = Bitter_Gmsh(...)
solid_names = result.solid_names
channels = result.channels
isolants = result.isolants
```

**Affected Functions**:
- `Bitter_Gmsh()`
- `Supra_Gmsh()`
- `Helix_Gmsh()`
- `Insert_Gmsh()`
- `Bitters_Gmsh()`
- `Supras_Gmsh()`
- `Magnet_Gmsh()`
- `MSite_Gmsh()`

#### 4. Error Handling Required

**Breaking Change**: `ValidationError` from `python_magnetgeo` must be handled

```python
from python_magnetgeo.validation import ValidationError

try:
    result = Insert_Gmsh(mname, cad, gname, is2D, verbose)
except ValidationError as e:
    print(f"Validation error: {e}")
    # Handle error appropriately
```

#### 5. Unsupported Geometry Types

**Breaking Change**: Unsupported geometry types now raise `ValueError`

```python
# Will raise ValueError if geometry type not in:
# Bitter, Bitters, Supra, Supras, Helix, Insert, MSite
```

**Migration**: Ensure your geometry types are supported or handle the exception.

### Migration Checklist

- [ ] Upgrade `python_magnetgeo` to 1.0.0 or higher
- [ ] Upgrade Python to 3.9 or higher
- [ ] Update code to use `GeometryLoadResult` objects
- [ ] Add `try/except` blocks for `ValidationError`
- [ ] Handle `ValueError` for unsupported geometry types
- [ ] Test all mesh generation workflows

### Quick Migration Example

```python
# Before (v0.0.x):
from python_magnetgmsh.cfg import Bitter_Gmsh

solid_names, channels, isolants = Bitter_Gmsh(name, bitter, gname, is2D)

# After (v0.1.0):
from python_magnetgmsh.cfg import Bitter_Gmsh
from python_magnetgeo.validation import ValidationError

try:
    result = Bitter_Gmsh(name, bitter, gname, is2D, verbose=False)
    solid_names = result.solid_names
    channels = result.channels
    isolants = result.isolants
except ValidationError as e:
    print(f"Invalid geometry: {e}")
except ValueError as e:
    print(f"Unsupported geometry type: {e}")
```

## Known Limitations

> [!CAUTION]
> The `--group` and `--hide` options are not yet implemented in `python_magnetgmsh.cli`

### TODO Items

The following features are planned for future releases:

- [ ] yaml file for MeshData to be derived from magnetgeo
- [ ] MeshData store a dict of surface with associated lc
- [ ] Add an order for Meshing, Use lc from dict to set mesh carac on box not using surface id (in case lc different from surface)
- [ ] Add option to load mesh carac from yaml file
- [ ] Make algo2d, algo3d choices enum
- [ ] Add Screens support to MSite
- [ ] Fix mesh generation in CLI (Axi only)
- [ ] Fix 3D mesh in XAO format
- [ ] Create proper boundary conditions for Supra structures
- [ ] Create Docker/Singularity image
- [ ] Use Gmsh loading XAO feature starting from gmsh 4.14

## Development

### Setting Up Development Environment

```bash
# Clone repository
git clone https://github.com/Trophime/python_magnetgmsh.git
cd python_magnetgmsh

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run test suite
pytest

# Run with coverage
pytest --cov=python_magnetgmsh --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Code Quality

```bash
# Format code with Black
black python_magnetgmsh

# Check code style
flake8 python_magnetgmsh

# Type checking
mypy python_magnetgmsh
```

### Running Test Suites

```bash
# Run main test suite
./testsuite.sh

# Run XAO test suite
./testsuite-xao.sh
```

### Contribution Guidelines

We welcome contributions! Please follow these guidelines:

- **Code Style**: Follow PEP 8, use Black formatter (line length 100)
- **Type Hints**: Add type annotations to all functions
- **Documentation**: Write docstrings for all public methods
- **Testing**: Maintain test coverage above 80%
- **Commits**: Use clear, descriptive commit messages
- **Pull Requests**: Include description of changes and link related issues

### Reporting Issues

When reporting issues, please include:

- Python version (`python --version`)
- `python_magnetgmsh` version
- `python_magnetgeo` version
- Gmsh version
- Minimal reproducible example
- Full error traceback
- YAML configuration file (if applicable)
- Operating system

## Documentation

Full documentation is available at: https://python-magnetgmsh.readthedocs.io

### Documentation Contents

- **User Guide**: Getting started, tutorials, examples
- **API Reference**: Complete function and class documentation
- **CLI Reference**: Command-line tool usage
- **Migration Guide**: Upgrading from older versions
- **Developer Guide**: Contributing, architecture, testing

## Credits

This package was created with [Cookiecutter](https://github.com/audreyr/cookiecutter) and the [audreyr/cookiecutter-pypackage](https://github.com/audreyr/cookiecutter-pypackage) project template.

### Authors

- **Christophe Trophime** - Lead Developer - <christophe.trophime@lncmi.cnrs.fr>
- **Romain Vallet** - Contributor - <romain.vallet@lncmi.cnrs.fr>
- **Jeremie Muzet** - Contributor - <jeremie.muzet@lncmi.cnrs.fr>

### Acknowledgments

- LNCMI (Laboratoire National des Champs Magnétiques Intenses)
- CNRS (Centre National de la Recherche Scientifique)
- Gmsh development team

## Related Projects

- **python_magnetgeo**: Magnet geometry definitions and YAML configuration
- **hifimagnet.salome**: Salome integration for CAD/mesh generation
- **feelpp**: Finite element library for electromagnetics simulation

## Support

## TODOs

- [ ] finish 3D mesh implementation
- [ ] use mesh_dict to improve 3D mesh

### Getting Help

- **Documentation**: https://python-magnetgmsh.readthedocs.io
- **GitHub Issues**: https://github.com/Trophime/python_magnetgmsh/issues
- **Email**: christophe.trophime@lncmi.cnrs.fr

### Professional Support

For professional support, custom development, or consulting services, please contact LNCMI.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Citation

If you use python_magnetgmsh in your research, please cite:

```bibtex
@software{python_magnetgmsh,
  author = {Trophime, Christophe and Vallet, Romain and Muzet, Jeremie},
  title = {Python Magnet Gmsh},
  version = {0.1.0},
  year = {2025},
  url = {https://github.com/Trophime/python_magnetgmsh}
}
```

---

**Version 0.1.0** | Released: 2025 | Requires: python_magnetgeo >= 1.0.0
