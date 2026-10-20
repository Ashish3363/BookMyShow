"""Wait for the database.

Phase: Docker.
Will hold: retries the PostgreSQL connection until it answers, then exits.
Used by docker-entrypoint.sh before migrations run.
"""
