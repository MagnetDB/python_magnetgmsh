#!/bin/bash
#

# set -euo pipefail
#TODO: make optionnal set -x

TestWD="/data/geometries"
#TestsAxi="test M9_Be M9Bitters M9_HLtest Oxford1 Oxford HTS-dblpancake-test2 HTS-pancake-test2 HTS-tape-test2 MNougat"
TestsAxi="M9_Be M9Bitters M9_HLtest"

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

echo "Axi CAD generation"
for test in ${TestsAxi}; do
    echo -en "${test} : " 
    python -m python_magnetgmsh.cli ${test}.yaml --wd ${TestWD} --thickslit > ${test}_gmsh.log 2>&1
    status=$?
    if [ "$status" != "0" ]; then
	    echo_failure
      exit 1
    else
	    echo_success
    fi
done

echo "Axi CAD generation with Air"
for test in ${TestsAxi}; do
    echo -en "${test} : " 
    python -m python_magnetgmsh.cli ${test}.yaml --wd ${TestWD} --thickslit --air 10 6 > ${test}_withAir_gmsh.log 2>&1
    status=$?
    if [ "$status" != "0" ]; then
	    echo_failure
      exit 1
    else
	    echo_success
    fi
done

echo "Axi Mesh generation with Gmsh"
for test in ${TestsAxi}; do
    echo -en "${test} : " 
    python -m python_magnetgmsh.cli ${test}.yaml --wd ${TestWD} --thickslit --mesh > ${test}_mesh_gmsh.log 2>&1
    status=$?
    if [ "$status" != "0" ]; then
	    echo_failure
      exit 1
    else
	    echo_success
    fi
done

echo "Axi Mesh generation with Gmsh (with Air)"
for test in ${TestsAxi}; do
    echo -en "${test} : " 
    python -m python_magnetgmsh.cli ${test}.yaml --wd ${TestWD} --thickslit --air 10 6 --mesh > ${test}_withAir_mesh_gmsh.log 2>&1
    status=$?
    if [ "$status" != "0" ]; then
	    echo_failure
    else
	    echo_success
    fi
done
