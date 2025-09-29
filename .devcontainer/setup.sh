#!/bin/bash

# 1. Update pip (optional but good practice)
python3 -m pip install --upgrade pip

# 2. Install dependencies
python3 -m pip install -r backend/requirements.txt
python3 -m pip install -r frontend/requirements.txt