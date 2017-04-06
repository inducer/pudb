#!/bin/bash

if [ -z "$COVERAGE" ]; then
	echo "coverage is not selected for this build"
	exit 0
fi

echo "uploading coverage"

eval "codecov --token=$COVERAGE"