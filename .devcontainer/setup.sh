#!/bin/bash

# 1. Update pip (optional but good practice)
python3 -m pip install --upgrade pip

# 2. Install dependencies
python3 -m pip install -r backend/requirements.dev.txt
python3 -m pip install -r frontend/requirements.dev.txt
# cd frontend-js
# npm install
# cd ..

# 3. Install docker
sudo rm -f /etc/apt/sources.list.d/yarn.list
sudo curl -fsSL https://get.docker.com | sh
sudo sudo service docker start || true
sudo usermod -aG docker vscode && getent group docker


# 4. Install and upgrade opencode
curl -fsSL https://opencode.ai/install | bash
opencode upgrade --major   