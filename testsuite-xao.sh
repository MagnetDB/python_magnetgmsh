#!/bin/bash
#

# set -euo pipefail
#TODO: make optionnal set -x

TestYAML="/data/geometries"
TestWD="/data/cad"
DEBUG=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --yaml)
            TestYAML="$2"
            shift 2
            ;;
        --cad)
            TestWD="$2"
            shift 2
            ;;
        --debug)
            DEBUG="--debug"
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --yaml PATH   Path to YAML directory (default: /data/geometries)"
            echo "  --wd PATH     Working directory (default: /data/cad)"
            echo "  --debug       Enable debug mode"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
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

# Check if TestWD directory exists
if [ ! -d "$TestYAML" ]; then
    echo "Error: Directory '$TestYAML' does not exist"
    exit 1
fi

TestsAxi="test M9_Be M9Bitters M9_HLtest Oxford1 Oxford HTS-dblpancake-test2 HTS-pancake-test2 HTS-tape-test2 Nougat MNougat"

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

echo_skip() {
  echo -en "[\033[30m SKIP \033[39m]"
  echo 
  return 0
}

echo "Axi Mesh generation with Gmsh"
for test in ${TestsAxi}; do
    echo -en "${test} : "
    if [ -f ${TestWD}/${test}-Axi.xao ]; then  
        python -m python_magnetgmsh.xao2msh ${test}-Axi.xao --geo ${TestYAML}/${test}.yaml --wd ${TestWD} mesh --group CoolingChannels > ${test}-xao_mesh.log 2>&1
        status=$?
        if [ "$status" != "0" ]; then
	        echo_failure
          exit 1
        else
	        echo_success
        fi
    else
        echo_skip
    fi
done

echo "Axi Mesh generation with Gmsh (with Air)"
for test in ${TestsAxi}; do
    echo -en "${test} : " 
    if [ -f ${TestWD}/${test}-Axi_withAir.xao ]; then  
        python -m python_magnetgmsh.xao2msh ${test}-Axi_withAir.xao --geo${TestYAML}/${test}.yaml --wd ${TestWD} mesh --group CoolingChannels > ${test}-xao_withAir_mesh.log 2>&1
        status=$?
        if [ "$status" != "0" ]; then
	        echo_failure
          exit 1
        else
	        echo_success
        fi
    else
        echo_skip
    fi
done
