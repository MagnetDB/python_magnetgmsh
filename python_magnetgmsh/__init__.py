"""Top-level package for Python Magnet Gmsh."""

__author__ = """Christophe Trophime"""
__email__ = "christophe.trophime@lncmi.cnrs.fr"
__version__ = "0.1.0"

# Version is read from package metadata (defined in pyproject.toml)
# This ensures a single source of truth for the version number
try:
    from importlib.metadata import version, PackageNotFoundError
except ImportError:
    # Fallback for Python < 3.8 (though we require 3.11+)
    from importlib_metadata import version, PackageNotFoundError

try:
    __version__ = version("python-magnetgmsh")
except PackageNotFoundError:
    # Package not installed (e.g., running from source without install)
    # This is expected during development before running `pip install -e .`
    __version__ = "0.0.0+unknown"

import python_magnetgeo

MIN_MAGNETGEO_VERSION = "1.0.0"
MAX_MAGNETGEO_VERSION = "2.0.0"

def check_magnetgeo_compatibility():
    """Verify python_magnetgeo version compatibility."""
    try:
        from packaging import version
        current = version.parse(python_magnetgeo.__version__)
        min_ver = version.parse(MIN_MAGNETGEO_VERSION)
        max_ver = version.parse(MAX_MAGNETGEO_VERSION)
        
        if not (min_ver <= current < max_ver):
            raise RuntimeError(
                f"python_magnetgmsh requires python_magnetgeo >={MIN_MAGNETGEO_VERSION},<{MAX_MAGNETGEO_VERSION} "
                f"but found {python_magnetgeo.__version__}"
            )
    except ImportError:
        # packaging not available, do basic string check
        if not hasattr(python_magnetgeo, '__version__'):
            raise RuntimeError("python_magnetgeo version cannot be determined")

# Call on import
check_magnetgeo_compatibility()
