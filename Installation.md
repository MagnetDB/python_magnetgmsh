# Installation Guide

This document provides comprehensive installation instructions for python_magnetgmsh using various package managers and build tools.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Install (pip)](#quick-install-pip)
- [Installation Methods](#installation-methods)
  - [Standard Python Tools](#1-standard-python-tools-pip--build)
  - [UV (Modern Fast Installer)](#2-uv-modern-fast-installer)
  - [Poetry (Dependency Management)](#3-poetry-dependency-management)
  - [Debian Package](#4-debian-package)
- [Development Environment Setup](#development-environment-setup)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

- **Python**: 3.9 or higher (3.10+ recommended)
- **Operating System**: Linux, macOS, or Windows
- **Gmsh**: Version 4.13.1 or higher
- **Git**: For source installation

### Required Dependencies

The following dependencies are automatically installed:

- `xmltodict >= 0.14.2`
- `gmsh >= 4.13.1`
- `pyyaml >= 6.0`
- `python-magnetgeo >= 1.0.0, < 2.0.0`
- `numpy >= 1.24.0`

### Optional Dependencies

- **Development**: `pytest`, `pytest-cov`, `black`, `flake8`, `mypy`
- **Documentation**: `sphinx`, `sphinx-rtd-theme`

---

## Quick Install (pip)

For most users, the simplest installation method:

```bash
# Install from PyPI (when available)
pip install python-magnetgmsh

# Or install from GitHub
pip install git+https://github.com/Trophime/python_magnetgmsh.git

# Verify installation
python_magnetgmsh --help
```

---

## Installation Methods

### 1. Standard Python Tools (pip + build)

This method uses the standard Python packaging tools based on PEP 517/518.

#### 1.1 Install from Source

```bash
# Clone repository
git clone https://github.com/Trophime/python_magnetgmsh.git
cd python_magnetgmsh

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode (for development)
pip install -e .

# Or install in standard mode
pip install .
```

#### 1.2 Install with Optional Dependencies

```bash
# Install with development tools
pip install -e ".[dev]"

# Install with documentation tools
pip install -e ".[docs]"

# Install with all optional dependencies
pip install -e ".[dev,docs]"
```

#### 1.3 Build Distribution Packages

```bash
# Install build tool
pip install build

# Build source distribution and wheel
python -m build

# Output in dist/:
#   python_magnetgmsh-0.1.0.tar.gz
#   python_magnetgmsh-0.1.0-py3-none-any.whl

# Install the wheel
pip install dist/python_magnetgmsh-0.1.0-py3-none-any.whl
```

#### 1.4 Using Makefile (Legacy Method)

```bash
# Clean previous builds
make clean

# Build distribution
make dist

# Install
make install

# Or use pip directly
pip install dist/*.whl
```

**Note**: The Makefile references `setup.py` which is deprecated. Use `python -m build` instead.

---

### 2. UV (Modern Fast Installer)

[UV](https://github.com/astral-sh/uv) is a fast Python package installer and resolver written in Rust.

#### 2.1 Install UV

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or via pip
pip install uv
```

#### 2.2 Install python_magnetgmsh with UV

```bash
# Clone repository
git clone https://github.com/Trophime/python_magnetgmsh.git
cd python_magnetgmsh

# Create virtual environment with UV
uv venv

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install package
uv pip install -e .

# Install with development dependencies
uv pip install -e ".[dev]"
```

#### 2.3 UV Project Configuration

The `pyproject.toml` includes UV-specific configuration:

```toml
[tool.uv]
dev-dependencies = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "black>=23.0",
    "flake8>=6.0",
    "mypy>=1.0",
]

[tool.uv.sources]
python-magnetgeo = { git = "https://github.com/Trophime/python_magnetgeo.git" }
```

#### 2.4 UV Advantages

- ⚡ **10-100× faster** than pip for package installation
- 🔒 **Deterministic** dependency resolution
- 🎯 **Compatible** with pip and existing workflows
- 📦 **Smaller** disk footprint

---

### 3. Poetry (Dependency Management)

[Poetry](https://python-poetry.org/) provides advanced dependency management and packaging.

#### 3.1 Install Poetry

```bash
# Recommended installation
curl -sSL https://install.python-poetry.org | python3 -

# Or via pip (not recommended)
pip install poetry
```

#### 3.2 Install python_magnetgmsh with Poetry

```bash
# Clone repository
git clone https://github.com/Trophime/python_magnetgmsh.git
cd python_magnetgmsh

# Install dependencies and package
poetry install

# Install with optional dependencies
poetry install --with dev
poetry install --with docs
poetry install --with dev,docs

# Activate virtual environment
poetry shell

# Or run commands without activating
poetry run python_magnetgmsh --help
```

#### 3.3 Poetry Configuration

The `pyproject.toml` includes Poetry-specific configuration:

```toml
[tool.poetry]
name = "python_magnetgmsh"
version = "0.1.0"
description = "Python helpers to create HiFiMagnet cads and meshes with Gmsh"
authors = [
    "Christophe Trophime <christophe.trophime@lncmi.cnrs.fr>",
    "Romain Vallet <romain.vallet@lncmi.cnrs.fr>",
    "Jeremie Muzet <jeremie.muzet@lncmi.cnrs.fr>",
]

[tool.poetry.dependencies]
python = "^3.9"
xmltodict = "^0.14.2"
gmsh = "^4.13.1"
PyYAML = "^6.0"
python-magnetgeo = "^0.8.0"
numpy = "^1.24.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.0"
pytest-cov = "^4.0"
black = "^23.0"
flake8 = "^6.0"
mypy = "^1.0"

[tool.poetry.scripts]
python_magnetgmsh = "python_magnetgmsh.cli:main"
python_xao2gmsh = "python_magnetgmsh.xao2msh:main"
```

#### 3.4 Build with Poetry

```bash
# Build distribution packages
poetry build

# Output in dist/:
#   python_magnetgmsh-0.1.0.tar.gz
#   python_magnetgmsh-0.1.0-py3-none-any.whl

# Publish to PyPI (when ready)
poetry publish
```

#### 3.5 Poetry Advantages

- 🎯 **Deterministic** dependency resolution with lock file
- 📦 **Integrated** build and publish system
- 🔧 **Easy** dependency management
- 🎨 **Clean** virtual environment handling

---

### 4. Debian Package

Build and install python_magnetgmsh as a native Debian package.

#### 4.1 Prerequisites

```bash
# Install build dependencies
sudo apt-get update
sudo apt-get install -y \
    debhelper-compat \
    dh-python \
    pybuild-plugin-pyproject \
    python3-all \
    python3-setuptools \
    python3-wheel \
    python3-yaml \
    python3-numpy \
    python3-xmltodict \
    python3-pytest \
    gmsh
```

#### 4.2 Build from Source

python_magnetgmsh includes a `debian/` directory with packaging configuration.

```bash
# Clone repository
git clone https://github.com/Trophime/python_magnetgmsh.git
cd python_magnetgmsh

# Create debian directory
mkdir -p debian

# Create required files
touch debian/control
touch debian/rules
touch debian/changelog
touch debian/copyright
touch debian/compat
```

#### 4.4 debian/control

Create `debian/control`:
git clone https://github.com/Trophime/python_magnetgmsh.git
cd python_magnetgmsh

# Build package
dpkg-buildpackage -us -uc -b

# Package will be created in parent directory:
#   python3-magnetgmsh_0.1.0-1_all.deb
```

#### 4.4 Install Debian Package

```bash
# Install package
sudo dpkg -i ../python3-magnetgmsh_0.1.0-1_all.deb

# Install missing dependencies (if any)
sudo apt-get install -f

# Verify installation
python3 -c "import python_magnetgmsh; print(python_magnetgmsh.__version__)"
python_magnetgmsh --help
```

#### 4.4 debian/control

Create `debian/control`:

```debian
Source: python-magnetgmsh
Section: python
Priority: optional
Maintainer: Christophe Trophime <christophe.trophime@lncmi.cnrs.fr>
Build-Depends: debhelper-compat (= 12),
 dh-python,
 pybuild-plugin-pyproject,
 python3-all,
 python3-setuptools (>= 61.0),
 python3-wheel,
 python3-yaml (>= 6.0),
 python3-numpy (>= 1.24.0),
 python3-pytest (>= 7.0),
 gmsh (>= 4.13.1)
Standards-Version: 4.6.0
Homepage: https://github.com/Trophime/python_magnetgmsh
Rules-Requires-Root: no

Package: python3-magnetgmsh
Architecture: all
Depends: python3-magnetgeo (>= 1.0.0), python3-yaml (>= 6.0), 
 python3-numpy (>= 1.24.0), gmsh (>= 4.13.1), 
 python3-xmltodict (>= 0.14.2),
 ${python3:Depends}, ${misc:Depends}
Description: Python helpers to create HiFiMagnet CADs and meshes with Gmsh
 This package provides tools to:
  * Load geometry configurations from python_magnetgeo YAML files
  * Generate CAD models using Gmsh API
  * Create meshes for electromagnetic simulations
  * Convert Salome XAO files to Gmsh mesh format
  * Rotate existing meshes
 .
 Command-line tools included:
  * python_magnetgmsh: Main mesh generation tool
  * python_xao2gmsh: XAO to Gmsh converter
  * python_rotate: Mesh rotation utility
 .
 This package installs the library for Python 3.
```

#### 4.5 debian/rules

Create `debian/rules`:

```makefile
#!/usr/bin/make -f

export DH_VERBOSE = 1
export PYBUILD_NAME=magnetgmsh

%:
	dh $@ --with python3 --buildsystem=pybuild
```

#### 4.5 debian/rules

Create `debian/rules`:

```makefile
#!/usr/bin/make -f

export DH_VERBOSE = 1
export PYBUILD_NAME=magnetgmsh

%:
	dh $@ --with python3 --buildsystem=pybuild
```

Make it executable:
```bash
chmod +x debian/rules
```

#### 4.6 debian/changelog

Create `debian/changelog`:

```
python-magnetgmsh (0.1.0-1) UNRELEASED; urgency=medium

  * Initial release
  * Python 3.9+ support
  * Gmsh integration for mesh generation
  * XAO file support
  * Requires python-magnetgeo >= 1.0.0

 -- Christophe Trophime <christophe.trophime@lncmi.cnrs.fr>  Thu, 09 Jan 2025 10:00:00 +0100
#### 4.6 debian/changelog

Create `debian/changelog`:

```
python-magnetgmsh (0.1.0-1) UNRELEASED; urgency=medium

  * Initial Debian package release
  * Python 3.9+ support
  * Gmsh integration for mesh generation
  * XAO file support from Salome
  * Requires python_magnetgeo >= 1.0.0, < 2.0.0
  * Command-line tools: python_magnetgmsh, python_xao2gmsh
  * Mesh rotation utility included

 -- Christophe Trophime <christophe.trophime@lncmi.cnrs.fr>  Thu, 09 Jan 2025 10:00:00 +0100
```

#### 4.7 debian/compat

Create `debian/compat`:

```
12
```

#### 4.8 debian/copyright

Create `debian/copyright`:

```
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: python-magnetgmsh
Upstream-Contact: Christophe Trophime <christophe.trophime@lncmi.cnrs.fr>
Source: https://github.com/Trophime/python_magnetgmsh

Files: *
Copyright: 2020-2025 LNCMI <christophe.trophime@lncmi.cnrs.fr>
License: MIT

License: MIT
 Permission is hereby granted, free of charge, to any person obtaining a
 copy of this software and associated documentation files (the "Software"),
 to deal in the Software without restriction, including without limitation
 the rights to use, copy, modify, merge, publish, distribute, sublicense,
 and/or sell copies of the Software, and to permit persons to whom the
 Software is furnished to do so, subject to the following conditions:
 .
 The above copyright notice and this permission notice shall be included
 in all copies or substantial portions of the Software.
 .
 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
 OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
 IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
 CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
 TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
 SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Files: debian/*
Copyright: 2025 Christophe Trophime <christophe.trophime@lncmi.cnrs.fr>
License: MIT
```

#### 4.9 Build Debian Package

Now build the package:

```bash

### Standard Development Setup

```bash
# Clone repository
git clone https://github.com/Trophime/python_magnetgmsh.git
cd python_magnetgmsh

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks (optional)
pip install pre-commit
pre-commit install

# Verify setup
pytest
black --check python_magnetgmsh
flake8 python_magnetgmsh
mypy python_magnetgmsh
```

### Development with UV (Recommended)

```bash
# Clone repository
git clone https://github.com/Trophime/python_magnetgmsh.git
cd python_magnetgmsh

# Create virtual environment
uv venv

# Activate
source .venv/bin/activate

# Install in editable mode with dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Run code quality checks
black python_magnetgmsh
flake8 python_magnetgmsh
mypy python_magnetgmsh
```

### Development with Poetry

```bash
# Clone repository
git clone https://github.com/Trophime/python_magnetgmsh.git
cd python_magnetgmsh

# Install with dev dependencies
poetry install --with dev

# Activate virtual environment
poetry shell

# Run tests
poetry run pytest

# Run code quality checks
poetry run black python_magnetgmsh
poetry run flake8 python_magnetgmsh
poetry run mypy python_magnetgmsh
```

### Development Tools Configuration

All tools are configured in `pyproject.toml`:

#### Black (Code Formatter)
```bash
# Format code
black python_magnetgmsh

# Check without modifying
black --check python_magnetgmsh

# Configuration: line-length = 100, Python 3.9+
```

#### Flake8 (Linter)
```bash
# Check code style
flake8 python_magnetgmsh

# Configuration: follow PEP 8
```

#### MyPy (Type Checker)
```bash
# Check type hints
mypy python_magnetgmsh

# Configuration: Python 3.9, gradual typing
```

#### Pytest (Testing)
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=python_magnetgmsh --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### IDE Setup

#### VS Code

Create `.vscode/settings.json`:

```json
{
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length", "100"],
  "python.testing.pytestEnabled": true,
  "editor.formatOnSave": true,
  "python.analysis.typeCheckingMode": "basic"
}
```

#### PyCharm

1. Go to **Settings → Tools → Python Integrated Tools**
2. Set default test runner to **pytest**
3. Go to **Settings → Tools → Black**
4. Enable "Run Black on save"
5. Set line length to 100

### Environment Variables

```bash
# Set working directory for tests
export MAGNETGMSH_TEST_DATA=/path/to/test/data

# Enable debug mode
export MAGNETGMSH_DEBUG=1

# Use custom Gmsh installation
export GMSH_PATH=/opt/gmsh/bin/gmsh
```

---

## Verification

### Verify Installation

```bash
# Check version
python -c "import python_magnetgmsh; print(python_magnetgmsh.__version__)"

# Check command-line tools
python_magnetgmsh --help
python_xao2gmsh --help

# Check dependencies
python -c "import python_magnetgeo; print(python_magnetgeo.__version__)"
python -c "import gmsh; print(gmsh.__version__)"
```

### Run Tests

```bash
# Run test suite
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_cfg.py

# Run with coverage
pytest --cov=python_magnetgmsh --cov-report=term-missing
```

### Test Basic Functionality

```bash
# Create test directory
mkdir -p test_data
cd test_data

# Test mesh generation (requires geometry file)
python_magnetgmsh example.yaml --mesh --show

# Test XAO conversion (requires XAO file)
python_xao2gmsh example.xao --geo example.yaml mesh

# Test mesh rotation
python -m python_magnetgmsh.rotate mesh.msh --rotate 45 --show
```

---

## Troubleshooting

### Common Issues

#### 1. python_magnetgeo Version Conflict

**Error:**
```
RuntimeError: python_magnetgmsh requires python_magnetgeo >=1.0.0,<2.0.0 but found 0.8.0
```

**Solution:**
```bash
# Upgrade python_magnetgeo
pip install --upgrade "python-magnetgeo>=1.0.0,<2.0.0"

# Or with UV
uv pip install --upgrade "python-magnetgeo>=1.0.0,<2.0.0"
```

#### 2. Gmsh Not Found

**Error:**
```
ModuleNotFoundError: No module named 'gmsh'
```

**Solution:**
```bash
# Install Gmsh Python API
pip install gmsh

# Or use system Gmsh with Python bindings
sudo apt-get install python3-gmsh  # Debian/Ubuntu
```

#### 3. Missing Build Dependencies (Debian)

**Error:**
```
dpkg-buildpackage: error: debian/rules build subprocess returned exit status 2
```

**Solution:**
```bash
# Install all build dependencies
sudo apt-get build-dep python3-magnetgmsh

# Or manually install missing packages
sudo apt-get install pybuild-plugin-pyproject
```

#### 4. Poetry Lock File Issues

**Error:**
```
The current project's Python requirement (>=3.9) is not compatible with some of the required packages Python requirement
```

**Solution:**
```bash
# Update lock file
poetry lock --no-update

# Or regenerate completely
rm poetry.lock
poetry install
```

#### 5. UV Installation Fails

**Error:**
```
error: Failed to download distribution
```

**Solution:**
```bash
# Clear UV cache
uv cache clean

# Retry installation
uv pip install -e .

# Or use pip as fallback
pip install -e .
```

### Getting Help

- **Documentation**: https://python-magnetgmsh.readthedocs.io
- **GitHub Issues**: https://github.com/Trophime/python_magnetgmsh/issues
- **Email**: christophe.trophime@lncmi.cnrs.fr

---

## Comparison Table

| Method | Speed | Use Case | Reproducibility | Learning Curve |
|--------|-------|----------|-----------------|----------------|
| **pip** | Medium | Quick install, standard | Medium | Low |
| **UV** | Fast ⚡ | Fast development | High | Low |
| **Poetry** | Medium | Dependency management | Very High | Medium |
| **Debian** | Slow | System integration | Very High | High |

### Recommendations

- **Beginners**: Use **pip** (standard, simple)
- **Developers**: Use **UV** (fast, modern)
- **Projects**: Use **Poetry** (dependency locking)
- **Deployment**: Use **Debian packages** (system integration)

---

## Next Steps

After installation:

1. Read the [User Guide](README.md)
2. Review [API Documentation](https://python-magnetgmsh.readthedocs.io)
3. Check [Breaking Changes](BREAKING_CHANGES.md) if upgrading
4. See [Examples](examples/) for usage patterns

---

**Last Updated**: January 2025  
**Version**: 0.1.0  
**Python**: 3.9+
