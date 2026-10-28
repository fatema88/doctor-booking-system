# Use Cases

## Actors

| Actor | Description |
|-------|-------------|
| **Patient** | Views doctor availability, books and cancels appointments. |
| **Doctor** | Manages availability and accepts or declines appointment requests. |

**Appointment statuses:** `Pending`, `Accepted`, `Declined`, `Cancelled`

**Limit:** a patient can have at most **N = 3** upcoming appointments (future `Pending` + `Accepted`).

---

## Summary

| ID | Use case | Actor | Requirement |
|----|----------|-------|:-----------:|
| UC1 | Set availability | Doctor | R1 |
| UC2 | View doctor availability | Patient | R1 |
| UC3 | Book an appointment | Patient | R2, R4 |
| UC4 | Accept or decline a request | Doctor | R3 |
| UC5 | View my appointments | Patient | R2, R3 |
| UC6 | Cancel an appointment | Patient | R4 |

---

## UC1: Set availability

- **Actor:** Doctor
- **Goal:** Define the days and times when the doctor can see patients.
- **Main flow:**
  1. The doctor chooses a day and a time slot.
  2. The system saves the slot as `Available`.

## UC2: View doctor availability

- **Actor:** Patient
- **Goal:** See when a doctor is free.
- **Main flow:**
  1. The patient selects a doctor.
  2. The system shows the days and times of all `Available` slots.
- **Alternative flow:** The doctor has no available slots. The system shows "No available times".
- **Related requirement:** R6 (times shown within 2 seconds).

## UC3: Book an appointment

- **Actor:** Patient
- **Goal:** Request an appointment in an available slot.
- **Main flow:**
  1. The patient selects an available slot.
  2. The system counts the patient's upcoming `Pending` and `Accepted` appointments.
  3. The count is less than N, so the system creates the appointment with status `Pending`.
  4. The system marks the slot as booked and confirms the request to the patient.
- **Alternative flows:**
  - **Limit reached:** the count is already N. The system rejects the booking and shows "Maximum upcoming appointments reached".
  - **Slot taken:** the slot is no longer available. The system asks the patient to choose another slot.

## UC4: Accept or decline a request

- **Actor:** Doctor
- **Goal:** Respond to a pending appointment request.
- **Main flow:**
  1. The doctor views the pending requests.
  2. The doctor selects a request and chooses **Accept** or **Decline**.
  3. The system updates the status to `Accepted` or `Declined`.
- **Alternative flow:** If the doctor declines, the slot becomes `Available` again and the appointment no longer counts toward N.

## UC5: View my appointments

- **Actor:** Patient
- **Goal:** Check the status of own appointments.
- **Main flow:**
  1. The patient opens "My appointments".
  2. The system lists the patient's appointments with date, time, doctor and status.

## UC6: Cancel an appointment

- **Actor:** Patient
- **Goal:** Cancel an upcoming appointment.
- **Main flow:**
  1. The patient selects the appointment and chooses **Cancel**.
  2. The system sets the status to `Cancelled` and frees the slot.
