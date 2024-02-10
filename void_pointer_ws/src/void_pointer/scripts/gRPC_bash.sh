#!/bin/bash

# Directory containing proto files
PROTO_DIR=./proto
# Output directory for generated Python bindings
PYTHON_OUT_DIR=app/void_pointer_ws/src/void_pointer/proto/proto_gen

# Create the output directory if it doesn't exist
mkdir -p ${PYTHON_OUT_DIR}

# Generate Python bindings
protoc -I=${PROTO_DIR} --python_out=${PYTHON_OUT_DIR} ${PROTO_DIR}/*.proto

# Optionally, adjust permissions and ownership here
