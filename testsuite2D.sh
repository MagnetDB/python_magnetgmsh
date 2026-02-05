#!/bin/bash
#

# set -euo pipefail
#TODO: make optionnal set -x

DEBUG=""
TestWD="/data/geometries"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --debug)
            DEBUG="--debug"
            shift
            ;;
        *)
            TestWD="$1"
            shift
            ;;
    esac
done

# Enable verbose mode if debug is set
if [ -n "$DEBUG" ]; then
    set -x
fi

# Check if TestWD directory exists
if [ ! -d "$TestWD" ]; then
    echo "Error: Directory '$TestWD' does not exist"
    exit 1
fi

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


echo "2D Mesh generation with Gmsh"
for test in ${Tests2D}; do
    echo -en "${test} : " 
    if [ ! -f "${TestWD}/${test}.yaml" ]; then
        echo -e "\033[33mSKIPPED\033[39m (file not found)"
        continue
    fi
    python -m python_magnetgmsh.m2d.Bitter2D ${test}.yaml --wd ${TestWD} --mesh > ${test}_mesh2D_gmsh.log 2>&1
    status=$?
    if [ "$status" != "0" ]; then
	    echo_failure
      exit 1
    else
	    echo_success
    fi
done

for test in ${Tests2D}; do
    echo -en "${test} : " 
    python -m python_magnetgmsh.m2d.Bitter2Dquarter ${test}.yaml --wd ${TestWD} --mesh > ${test}_mesh2D_gmsh.log 2>&1
    status=$?
    if [ "$status" != "0" ]; then
	    echo_failure
      exit 1
    else
	    echo_success
    fi
done

