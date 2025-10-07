#!/bin/bash
#

# set -euo pipefail
#TODO: make optionnal set -x

TestWD="/data/geometries"
Tests2D="M9_Be"
#Tests2D="M9_Be M9Bitters M9_HLtest"

echo_success() {
  echo -en "[\033[32m  OK  \033[39m]"
  echo 
  return 0
}

echo_failure() {
  echo -en "[\033[31mFAILED\033[39m]"
  echo 
  return 1
}

echo "2D CAD generation"
for test in ${Tests2D}; do
    echo -en "${test} : " 
    python -m python_magnetgmsh.Bitter2D ${test}.yaml --wd ${TestWD} --thickslit > ${test}_gmsh.log 2>&1
    status=$?
    if [ "$status" != "0" ]; then
	    echo_failure
      exit 1
    else
	    echo_success
    fi
done

echo "2D Mesh generation with Gmsh"
for test in ${Tests2D}; do
    echo -en "${test} : " 
    python -m python_magnetgmsh.Bitter2D ${test}.yaml --wd ${TestWD} --thickslit --mesh > ${test}_mesh_gmsh.log 2>&1
    status=$?
    if [ "$status" != "0" ]; then
	    echo_failure
      exit 1
    else
	    echo_success
    fi
done

echo "2D CAD generation"
for test in ${Tests2D}; do
    echo -en "${test} : " 
    python -m python_magnetgmsh.Bitter2Dquarter ${test}.yaml --wd ${TestWD} --thickslit > ${test}_gmsh.log 2>&1
    status=$?
    if [ "$status" != "0" ]; then
	    echo_failure
      exit 1
    else
	    echo_success
    fi
done

echo "2D Mesh generation with Gmsh"
for test in ${Tests2D}; do
    echo -en "${test} : " 
    python -m python_magnetgmsh.Bitter2Dquarter ${test}.yaml --wd ${TestWD} --thickslit --mesh > ${test}_mesh_gmsh.log 2>&1
    status=$?
    if [ "$status" != "0" ]; then
	    echo_failure
      exit 1
    else
	    echo_success
    fi
done

