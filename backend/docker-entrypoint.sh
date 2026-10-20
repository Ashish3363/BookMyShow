#!/usr/bin/env bash
# Backend container start script.
# Phase: Docker.
# Will hold, in order:
#   1. python -m scripts.wait_for_db
#   2. alembic upgrade head
#   3. start FastAPI with uvicorn
