# Backend image.
# Phase: Docker.
# Will hold:
#   1. Python 3.12 slim base, install uv
#   2. Copy pyproject.toml and uv.lock, run uv sync (cached layer)
#   3. Copy app code
#   4. Run as a non-root user
#   5. ENTRYPOINT docker-entrypoint.sh
