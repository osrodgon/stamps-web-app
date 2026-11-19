FROM mcr.microsoft.com/devcontainers/python:1-3.13-bookworm

# Remove any entry from Yarn if not needed
RUN rm -f /etc/apt/sources.list.d/yarn.list \
    && sed -i '/dl\.yarnpkg\.com/d' /etc/apt/sources.list /etc/apt/sources.list.d/* 2>/dev/null || true