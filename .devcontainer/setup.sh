#!/bin/bash

# 1. Update pip (optional but good practice)
python3 -m pip install --upgrade pip

# 2. Install dependencies
python3 -m pip install -r backend/requirements.dev.txt
python3 -m pip install -r frontend/requirements.dev.txt
# cd frontend-js
# npm install
# cd ..

# 3. Install opencode
curl -fsSL https://opencode.ai/install | bash