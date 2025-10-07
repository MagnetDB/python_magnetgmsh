# Task: Replace print() Statements with Python Logging Module

## Objective

Replace all `print()` statements in python_magnetgmsh with proper Python `logging` module usage to enable:
- Configurable log levels (DEBUG, INFO, WARNING, ERROR)
- Better control over output verbosity
- Professional logging practices
- Easier debugging and troubleshooting
- Log file output capability

## Current State Analysis

### Files with print() statements:
1. **cfg.py**: ~15+ print statements in geometry loading functions
2. **cli.py**: ~10+ print statements for progress/status
3. **rotate.py**: ~8 print statements for transformation info
4. **xao2msh.py**: Multiple print statements
5. **Bitter2D.py**: Extensive debug print statements
6. **Various mesh/ modules**: Additional print statements

### Current Problems:
```python
# cfg.py example - current approach
def Supra_Gmsh(mname, cad, gname, is2D, verbose=False):
    print(f"Supra_Gmsh: mname={mname}, cad={cad.name}, gname={gname}")
    solid_names = cad.get_names(prefix, is2D, verbose)
    print(f"supra: solid_names: {solid_names}", flush=True)
    return GeometryLoadResult(...)

# Issues:
# ❌ Cannot disable output without modifying code
# ❌ No differentiation between debug/info/warning
# ❌ Output mixes with user messages
# ❌ Cannot redirect to log files
# ❌ flush=True scattered inconsistently
```

## Requirements

### 1. Logging Configuration Module

Create `python_magnetgmsh/logging_config.py`:

```python
"""
Logging configuration for python_magnetgmsh.

Provides centralized logging setup with consistent formatting and
configurable output levels.
"""

import logging
import sys
from typing import Optional


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    verbose: bool = False,
    debug: bool = False
) -> logging.Logger:
    """
    Configure logging for python_magnetgmsh.
    
    Args:
        level: Base logging level (default: INFO)
        log_file: Optional file path for log output
        verbose: If True, set level to DEBUG
        debug: If True, set level to DEBUG and add more detail
        
    Returns:
        Configured root logger for python_magnetgmsh
    """
    # Determine logging level
    if debug:
        level = logging.DEBUG
    elif verbose:
        level = logging.INFO
    
    # Create logger
    logger = logging.getLogger('python_magnetgmsh')
    logger.setLevel(level)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create formatters
    if debug:
        # Detailed format for debug mode
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        # Simple format for normal operation
        formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setLevel(logging.DEBUG)  # Always DEBUG for files
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Module name (use __name__)
        
    Returns:
        Logger instance
        
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing geometry")
    """
    return logging.getLogger(f'python_magnetgmsh.{name}')
```

### 2. Logging Level Guidelines

Use appropriate log levels:

| Level | When to Use | Current print() Equivalent |
|-------|-------------|---------------------------|
| **DEBUG** | Detailed info for diagnosing problems | `if verbose: print(...)` with internal details |
| **INFO** | General informational messages | `print(...)` for normal operation |
| **WARNING** | Warning about potential issues | `print("Warning: ...")` |
| **ERROR** | Error that doesn't stop execution | `print("ERROR: ...")` |
| **CRITICAL** | Serious error, may cause failure | `print("CRITICAL: ...")` or exceptions |

### 3. Migration Examples

#### Example 1: cfg.py Functions

**Before:**
```python
def Supra_Gmsh(mname, cad, gname, is2D, verbose=False):
    print(f"Supra_Gmsh: mname={mname}, cad={cad.name}, gname={gname}")
    
    solid_names = cad.get_names(prefix, is2D, verbose)
    print(f"supra: solid_names: {solid_names}", flush=True)
    
    channels = cad.get_channels(mname)
    isolants = cad.get_isolants(mname)
    
    return GeometryLoadResult(...)
```

**After:**
```python
import logging

logger = logging.getLogger(__name__)


def Supra_Gmsh(mname, cad, gname, is2D, verbose=False):
    logger.info(f"Loading Supra geometry: {cad.name}")
    logger.debug(f"Supra_Gmsh: mname={mname}, gname={gname}, is2D={is2D}")
    
    solid_names = cad.get_names(prefix, is2D, verbose)
    logger.debug(f"Created {len(solid_names)} solid objects: {solid_names}")
    
    channels = cad.get_channels(mname)
    isolants = cad.get_isolants(mname)
    
    if channels:
        logger.debug(f"Found {len(channels)} cooling channels")
    
    return GeometryLoadResult(...)
```

#### Example 2: cli.py Main Function

**Before:**
```python
def main():
    args = parser.parse_args()
    print(f"Arguments: {args}, type={type(args)}")
    
    if args.wd:
        print(f"Changing to working directory: {args.wd}")
        os.chdir(args.wd)
    
    print(f"Loading geometry from: {args.filename}")
    geometry = getObject(args.filename)
    print(f"Loaded geometry: {geometry.name}, type: {type(geometry).__name__}")
    
    print("Generating CAD geometry...")
    
    if args.mesh:
        print("Generating mesh...")
        gmsh_msh(...)
        print(f"Mesh saved to: {mesh_filename}")
    
    print("Success!")
```

**After:**
```python
import logging
from .logging_config import setup_logging

logger = logging.getLogger(__name__)


def main():
    args = parser.parse_args()
    
    # Setup logging based on args
    setup_logging(
        verbose=args.verbose,
        debug=args.debug,
        log_file=f"{args.filename.replace('.yaml', '')}.log" if args.debug else None
    )
    
    logger.debug(f"Command-line arguments: {args}")
    
    if args.wd:
        logger.info(f"Working directory: {args.wd}")
        os.chdir(args.wd)
    
    logger.info(f"Loading geometry: {args.filename}")
    geometry = getObject(args.filename)
    logger.info(f"Loaded {type(geometry).__name__}: {geometry.name}")
    
    logger.info("Generating CAD geometry...")
    
    if args.mesh:
        logger.info("Generating mesh...")
        gmsh_msh(...)
        logger.info(f"Mesh saved: {mesh_filename}")
    
    logger.info("Processing complete!")
```

#### Example 3: Error Handling

**Before:**
```python
try:
    geometry = getObject(args.filename)
except ValidationError as e:
    print(f"ERROR: Geometry validation failed in {args.filename}")
    print(f"  {e}")
    return 1
except FileNotFoundError as e:
    print(f"ERROR: File not found: {args.filename}")
    return 1
```

**After:**
```python
try:
    geometry = getObject(args.filename)
except ValidationError as e:
    logger.error(f"Geometry validation failed: {args.filename}")
    logger.error(f"  {e}")
    return 1
except FileNotFoundError as e:
    logger.error(f"File not found: {args.filename}")
    return 1
except Exception as e:
    logger.exception(f"Unexpected error loading geometry")  # Includes traceback
    return 1
```

#### Example 4: Progress Messages

**Before:**
```python
for i, magnet in enumerate(cad.magnets):
    print(f"Processing magnet {i+1}/{len(cad.magnets)}: {magnet.name}")
    result = Bitter_Gmsh(...)
    print(f"  Created {len(result.solid_names)} solids")
```

**After:**
```python
logger.info(f"Processing {len(cad.magnets)} magnets...")

for i, magnet in enumerate(cad.magnets):
    logger.info(f"  [{i+1}/{len(cad.magnets)}] {magnet.name}")
    result = Bitter_Gmsh(...)
    logger.debug(f"    Created {len(result.solid_names)} solids")
```

### 4. Module-Level Logger Pattern

Each module should get its logger at the top:

```python
"""Module for geometry loading."""

import logging

# Get module-specific logger
logger = logging.getLogger(__name__)


def some_function():
    logger.info("Processing...")
    logger.debug("Detail: value=%s", some_value)
```

### 5. Verbose Flag Integration

Replace `verbose` parameter with logger level checks:

**Before:**
```python
def Bitter_Gmsh(mname, cad, gname, is2D, verbose=False):
    if verbose:
        print(f"Detailed info: {lots_of_data}")
```

**After:**
```python
def Bitter_Gmsh(mname, cad, gname, is2D, verbose=False):
    # For backward compatibility, still accept verbose
    # But now it just affects local behavior if needed
    logger.debug(f"Detailed info: {lots_of_data}")
    
    # Or remove verbose parameter entirely and rely on log level
```

### 6. Special Cases

#### Gmsh Verbosity Coordination

```python
# cli.py
def main():
    args = parser.parse_args()
    setup_logging(verbose=args.verbose, debug=args.debug)
    
    gmsh.initialize()
    
    # Coordinate Gmsh verbosity with our logging
    if args.debug:
        gmsh.option.setNumber("General.Verbosity", 5)
        logger.debug("Gmsh verbosity: maximum (5)")
    elif args.verbose:
        gmsh.option.setNumber("General.Verbosity", 3)
        logger.debug("Gmsh verbosity: normal (3)")
    else:
        gmsh.option.setNumber("General.Verbosity", 2)
```

#### User-Facing Messages

Keep some important user messages as INFO level (always visible):

```python
# Always visible to user
logger.info("Mesh generation complete")
logger.info(f"Output file: {output_file}")

# Debug details
logger.debug(f"Mesh contains {num_nodes} nodes, {num_elements} elements")
logger.debug(f"Processing time: {elapsed:.2f}s")
```

## Implementation Plan

### Phase 1: Setup (30 minutes)
1. Create `python_magnetgmsh/logging_config.py`
2. Add logging import to `__init__.py`
3. Update pyproject.toml if needed (logging is stdlib, no deps)

### Phase 2: CLI Modules (1 hour)
1. Update `cli.py` - add setup_logging() call in main()
2. Update `rotate.py` - replace prints
3. Update `xao2msh.py` - replace prints
4. Update `Bitter2D.py` - replace prints

### Phase 3: Core Modules (1-2 hours)
1. Update `cfg.py` - all loader functions
2. Update `mesh/` modules
3. Update utility modules

### Phase 4: Testing (30 minutes)
1. Test with different log levels
2. Test verbose/debug flags
3. Test log file output
4. Ensure backward compatibility

### Phase 5: Documentation (30 minutes)
1. Update README with logging examples
2. Add logging section to developer guide
3. Update CLI help text

## Testing Checklist

```bash
# Test normal operation (INFO level)
python_magnetgmsh test.yaml --mesh

# Test verbose mode (DEBUG level)
python_magnetgmsh test.yaml --mesh --verbose

# Test debug mode (DEBUG with details)
python_magnetgmsh test.yaml --mesh --debug

# Test with log file
python_magnetgmsh test.yaml --mesh --debug
# Should create test.log file

# Test quiet operation
python_magnetgmsh test.yaml --mesh --quiet  # Add --quiet flag
# Should only show WARNING and above
```

## Benefits After Migration

1. ✅ **Configurable verbosity** - Users control output level
2. ✅ **Professional logging** - Industry standard practices
3. ✅ **Better debugging** - Timestamps, line numbers, function names
4. ✅ **Log files** - Persistent records for troubleshooting
5. ✅ **Cleaner code** - Consistent logging style
6. ✅ **Performance** - Can disable debug messages in production
7. ✅ **Testing** - Can capture and verify log messages
8. ✅ **Maintenance** - Easier to find and update log messages

## Backward Compatibility

Maintain backward compatibility for `verbose` parameter:

```python
def Bitter_Gmsh(mname, cad, gname, is2D, verbose=False):
    """
    Args:
        verbose: Deprecated. Use logging level instead.
            For backward compatibility, affects local behavior.
    """
    if verbose:
        logger.debug("Verbose mode enabled (deprecated parameter)")
    
    # Use logger instead of verbose checks
    logger.debug(f"Processing {cad.name}")
```

## Code Review Checklist

When reviewing migrated code:

- [ ] All `print()` statements replaced with logger calls
- [ ] Appropriate log levels used (DEBUG/INFO/WARNING/ERROR)
- [ ] Module-level logger defined: `logger = logging.getLogger(__name__)`
- [ ] setup_logging() called in main() functions
- [ ] Error handling uses logger.error() or logger.exception()
- [ ] Debug details use logger.debug()
- [ ] User-facing status uses logger.info()
- [ ] No `flush=True` needed (logging handles this)
- [ ] Backward compatibility maintained for `verbose` parameter

## Example Output Comparison

### Before (print)
```
Arguments: Namespace(filename='test.yaml', wd='', mesh=True, verbose=False)
Loading geometry from: test.yaml
Loaded geometry: Insert, type: Insert
Supra_Gmsh: mname=, cad=Insert, gname=model
supra: solid_names: ['H1', 'H2', 'H3']
Generating CAD geometry...
Generating mesh...
Mesh saved to: test.msh
Success!
```

### After (logging - INFO level)
```
INFO: Loading geometry: test.yaml
INFO: Loaded Insert: Insert
INFO: Generating CAD geometry...
INFO: Generating mesh...
INFO: Mesh saved: test.msh
INFO: Processing complete!
```

### After (logging - DEBUG level)
```
2025-01-10 14:32:15 - python_magnetgmsh.cli - DEBUG - main:45 - Command-line arguments: Namespace(...)
2025-01-10 14:32:15 - python_magnetgmsh.cli - INFO - main:52 - Loading geometry: test.yaml
2025-01-10 14:32:15 - python_magnetgmsh.cli - INFO - main:54 - Loaded Insert: Insert
2025-01-10 14:32:15 - python_magnetgmsh.cfg - DEBUG - Supra_Gmsh:78 - Supra_Gmsh: mname=, gname=model, is2D=True
2025-01-10 14:32:15 - python_magnetgmsh.cfg - DEBUG - Supra_Gmsh:81 - Created 3 solid objects: ['H1', 'H2', 'H3']
2025-01-10 14:32:15 - python_magnetgmsh.cli - INFO - main:65 - Generating CAD geometry...
2025-01-10 14:32:16 - python_magnetgmsh.cli - INFO - main:70 - Generating mesh...
2025-01-10 14:32:18 - python_magnetgmsh.cli - INFO - main:73 - Mesh saved: test.msh
2025-01-10 14:32:18 - python_magnetgmsh.cli - INFO - main:88 - Processing complete!
```

## Success Criteria

Migration is complete when:
- [ ] Zero `print()` statements remain in production code
- [ ] All modules use consistent logging
- [ ] Log levels appropriately assigned
- [ ] Tests pass with logging enabled
- [ ] Documentation updated
- [ ] Command-line tools work with --verbose/--debug flags
- [ ] Log files can be generated
- [ ] No regression in functionality

---

**Priority**: High  
**Estimated Time**: 3-4 hours total  
**Breaking Changes**: None (backward compatible)  
**Dependencies**: None (logging is stdlib)  
**Impact**: Significant improvement in code quality and debugging capability
