---
title: Python Magnet Gmsh
---

[![image](https://img.shields.io/pypi/v/python_magnetgmsh.svg)](https://pypi.python.org/pypi/python_magnetgmsh)

[![image](https://img.shields.io/travis/Trophime/python_magnetgmsh.svg)](https://travis-ci.com/Trophime/python_magnetgmsh)

[![Documentation Status](https://readthedocs.org/projects/python-magnetgmsh/badge/?version=latest)](https://python-magnetgmsh.readthedocs.io/en/latest/?version=latest)

[![Updates](https://pyup.io/repos/github/Trophime/python_magnetgmsh/shield.svg)](https://pyup.io/repos/github/Trophime/python_magnetgmsh/)

Python Magnet Geometry contains magnet geometrical models

-   Free software: MIT license
-   Documentation: <https://python-magnetgmsh.readthedocs.io>.

Features
========

-   Load/Create CAD and Mesh with Gmsh
-   Create Gmsh mesh from Salome XAO format

INSTALL
=======

To install in a python virtual env

```
python -m venv --system-site-packages magnetgmsh-env
source ./magnetgmsh-env/bin/activate
pip install -r requirements.txt
```

Examples
========

Use Gmsh API to create a msh file from a magnetgeo yaml file

```
python3 -m python_magnetgmsh.cli --wd /data/geometries test.yaml --mesh [--lc] --show
```

[NOTE]
===
group/hide options is not implement in python_magnetgmsh.cli
===

Create a gmsh msh file from Salome xao file:

```
python3 -m python_magnetgmsh.xao2msh --wd /data/geometries test-Axi.xao --geo test.yaml mesh --group CoolingChannels
python3 -m python_magnetgmsh.xao2msh --wd /data/geometries M9_HLtest-Axi.xao --geo M9_HLtest.yaml mesh --group CoolingChannels
python3 -m python_magnetgmsh.xao2msh --wd /data/geometries Pancakes-pancake-Axi.xao --geo HTS-pancake-test.yaml [mesh []]
```

Credits
=======

This package was created with
[Cookiecutter](https://github.com/audreyr/cookiecutter) and the
[audreyr/cookiecutter-pypackage](https://github.com/audreyr/cookiecutter-pypackage)
project template.
