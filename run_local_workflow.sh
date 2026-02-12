#!/bin/bash
set -e

echo "Starting local workflow execution..."

# Step 1: Install dependencies
echo "----------------------------------------------------------------------"
echo "Step 1: Install dependencies"
python -m pip install --upgrade pip
if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
pip install pytest flake8
pip install -e .

# Step 2: Lint with flake8
echo "----------------------------------------------------------------------"
echo "Step 2: Lint with flake8"
# stop the build if there are Python syntax errors or undefined names
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics --exclude=.venv,build,dist,__pycache__
# exit-zero treats all errors as warnings. The GitHub editor is 127 chars wide
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics --exclude=.venv,build,dist,__pycache__

# Step 3: Test with pytest
echo "----------------------------------------------------------------------"
echo "Step 3: Test with pytest"
export PYTHONPATH=src
pytest

echo "----------------------------------------------------------------------"
echo "Local workflow finished successfully!"
