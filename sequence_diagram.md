# Sequence Diagram

```mermaid

sequenceDiagram
    actor Patient
    participant Doctor
    participant TimeSlot
    participant Appointment

    Patient->>Doctor: viewAvailability()
    Doctor->>TimeSlot: Check available slots
    TimeSlot-->>Doctor: Available time slots
    Doctor-->>Patient: Display availability

    Patient->>Patient: Check upcoming appointments

    alt Patient has 3 upcoming appointments
        Patient-->>Patient: Reject booking
    else Patient has fewer than 3 appointments
        Patient->>TimeSlot: Select available slot
        TimeSlot-->>Patient: Confirm slot availability

        alt Slot is available
            Patient->>Appointment: bookAppointment()
            Appointment->>Appointment: Create appointment with Pending status
            Appointment->>TimeSlot: Mark slot as unavailable
            Appointment-->>Patient: Booking request confirmed
        else Slot is unavailable
            TimeSlot-->>Patient: Ask patient to select another slot
        end
    end

    Doctor->>Appointment: acceptAppointment() or declineAppointment()

    alt Doctor accepts
        Appointment->>Appointment: accept()
        Appointment-->>Patient: Appointment Accepted
    else Doctor declines
        Appointment->>Appointment: decline()
        Appointment->>TimeSlot: Release slot
        Appointment-->>Patient: Appointment Declined
    end

    opt Patient cancels appointment
        Patient->>Appointment: cancel()
        Appointment->>Appointment: cancel()
        Appointment->>TimeSlot: Release slot
        Appointment-->>Patient: Cancellation confirmed
    end
