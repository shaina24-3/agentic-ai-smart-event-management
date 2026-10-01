# Event Safety, Capacity Limits & Overcrowding Rules

## 1. Safety Alerts & Maximum Capacity Adherence
- **Strict Seating Cap:** Under campus and municipal fire safety codes, event attendee capacity can NEVER exceed the designated seating capacity of the assigned venue.
- **Safety Violation Alert:** If an organizer attempts to create an event with participant capacity greater than the venue's certified limit, the system must trigger a **SAFETY ALERT**:
  > *"Safety Violation: Requested capacity ({capacity}) exceeds the venue's maximum safety threshold ({venue_capacity}). Please reduce capacity or select a larger venue."*
- **Standing Room Prohibited:** Standing-room only is strictly prohibited in all indoor venues for emergency evacuation readiness.

## 2. Duplicate Registration Prevention
- **One Seat Per Person:** A user cannot register more than once for the same event.
- **Security Check:** System enforces unique constraint checks on user ID and event ID. If a user tries to book again, an alert is returned:
  > *"Duplicate Booking: You are already registered for this event. Check your dashboard for booking status."*

## 3. Emergency Evacuation & Health Protocol
- All venue entrances, exits, and fire escape pathways must remain completely unobstructed by stage gear or extra seating.
- First aid kits and emergency contacts are positioned at the entrance of each auditorium.
