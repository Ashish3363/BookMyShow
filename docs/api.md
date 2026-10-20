# API

Base path: `/api/v1`

## Step 2 (planned)

| Method | Path | Returns |
|---|---|---|
| GET | `/cities` | All cities |
| GET | `/cities/{city_id}` | One city, 404 if missing |
| GET | `/cinemas?city_id=` | Cinemas, optional city filter |
| GET | `/cinemas/{cinema_id}` | One cinema, 404 if missing |

## Later phases

| Phase | Paths |
|---|---|
| Movies | `/movies`, `/movies/{movie_id}` |
| Shows | `/shows`, `/shows/{show_id}/seats` |
| Booking | `/bookings`, `/bookings/{booking_id}`, `/bookings/{booking_id}/cancel` |
| Auth | `/auth/signup`, `/auth/login`, `/auth/me` |

## Error format

```json
{ "error": { "code": "not_found", "message": "City 9 not found" } }
```
