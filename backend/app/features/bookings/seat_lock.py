"""Seat lock.

Phase: Booking.
Will hold: hold seats in Redis for 10 minutes (TTL) while the user pays.
The lock ends on its own if payment does not finish.
"""
