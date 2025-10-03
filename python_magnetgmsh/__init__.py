"""Top-level package for Python Magnet Gmsh."""

__author__ = """Christophe Trophime"""
__email__ = "christophe.trophime@lncmi.cnrs.fr"
__version__ = "0.1.0"

import python_magnetgeo

MIN_MAGNETGEO_VERSION = "0.8.0"
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