#!/usr/bin/env bash

# Change to script dir
cd "${0%/*}"

# Change to CSS dir
cd ../oneplus/static/css/

sass ./[!_]*.scss
