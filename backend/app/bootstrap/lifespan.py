"""Startup and shutdown work.

Phase: Step 2 (cities and cinemas APIs).
Will hold: the lifespan function. Startup: connect PostgreSQL.
Shutdown: close connections. Later phases add Redis and Elasticsearch here.
"""

#startup and shutdown hook.

from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    #Startup: database connection goes here 
    yield
    #Shutdown: database close connections goes here