"""Redis client.

Phase: Booking (seat lock, cache).
Will hold: one shared async Redis connection, opened in bootstrap/lifespan.py.
"""
