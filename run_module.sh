#!/bin/bash

if [ -z "$1" ]; then
  echo "Usage: $0 <module_name>"
  exit 1
fi

MODULE_NAME=$1
MODULE_NAME_CAPITALIZED=$(tr '[:lower:]' '[:upper:]' <<< ${MODULE_NAME:0:1})${MODULE_NAME:1}

PYTHON_FILE="src/socialModules/module${MODULE_NAME_CAPITALIZED}.py"
OUTPUT_FILE="/tmp/${MODULE_NAME}.txt"

if [ ! -f "$PYTHON_FILE" ]; then
  echo "Error: Module file not found at $PYTHON_FILE"
  exit 1
fi

python3 "$PYTHON_FILE" 2>&1 | tee "$OUTPUT_FILE"
