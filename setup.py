#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open("README.md") as readme_file:
    readme = readme_file.read()


requirements = [
    "xmltodict>=0.14.2",
    "gmsh>=4.13.1",
    "pyyaml>=6.0",
    "python_magnetgeo>=0.8.0,<2.0.0",  # Add version constraint!
    "numpy>=1.24.0"
]

setup_requirements = ["pytest-runner"]
test_requirements = ["pytest>=3"]

setup(
    author="Christophe Trophime",
    author_email="christophe.trophime@lncmi.cnrs.fr",
    python_requires=">=3.9"
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    description="Python Magnet Geometry contains maget geometrical models",
    entry_points={
        "console_scripts": [
            "python_magnetgmsh=python_magnetgmsh.cli:main",
            "python_xao2gmsh=python_magnetgmsh.xao2msh:main",
        ]
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme,
    include_package_data=True,
    keywords="python_magnetgmsh",
    name="python_magnetgmsh",
    packages=find_packages(include=["python_magnetgmsh", "python_magnetgmsh.*"]),
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/Trophime/python_magnetgmsh",
    version="0.1.0",
    zip_safe=False,
)
