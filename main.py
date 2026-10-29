"""
Doctor Appointment Booking System  (single file, command-line)

Based on: use_cases.md, class_diagram.md, sequence_diagram.md, requirements.txt
Run:  python main.py
Data is saved automatically to data.json (next to this file).
"""

import json
import os
import time
from datetime import datetime, timedelta

# ----------------------------------------------------------------- settings
N = 3                                   # R4: max upcoming appointments
DATE_FMT = "%Y-%m-%d %H:%M"
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")

PENDING, ACCEPTED, DECLINED, CANCELLED = "Pending", "Accepted", "Declined", "Cancelled"


def fmt(dt):
    return dt.strftime(DATE_FMT)


def parse(text):
    return datetime.strptime(text.strip(), DATE_FMT)


# ------------------------------------------------------------------ classes
class TimeSlot:
    def __init__(self, slot_id, doctor_id, start_time, end_time, is_available=True):
        self.slot_id = slot_id
        self.doctor_id = doctor_id
        self.start_time = start_time
        self.end_time = end_time
        self.is_available = is_available

    def to_dict(self):
        return {"slot_id": self.slot_id, "doctor_id": self.doctor_id,
                "start_time": fmt(self.start_time), "end_time": fmt(self.end_time),
                "is_available": self.is_available}

    @staticmethod
    def from_dict(d):
        return TimeSlot(d["slot_id"], d["doctor_id"], parse(d["start_time"]),
                        parse(d["end_time"]), d["is_available"])


class MedicalRecord:
    def __init__(self, record_id, patient_id, medical_data):
        self.record_id = record_id
        self.patient_id = patient_id
        self.medical_data = medical_data

    def to_dict(self):
        return self.__dict__.copy()

    @staticmethod
    def from_dict(d):
        return MedicalRecord(d["record_id"], d["patient_id"], d["medical_data"])


class Appointment:
    def __init__(self, appointment_id, patient_id, doctor_id, slot, status=PENDING):
        self.appointment_id = appointment_id
        self.patient_id = patient_id
        self.doctor_id = doctor_id
        self.slot = slot
        self.status = status

    @property
    def appointment_time(self):
        return self.slot.start_time

    def is_upcoming(self, now=None):
        """Counts toward N: future + (Pending or Accepted)."""
        now = now or datetime.now()
        return self.appointment_time > now and self.status in (PENDING, ACCEPTED)

    def accept(self):
        if self.status != PENDING:
            raise ValueError("Only a Pending appointment can be accepted.")
        self.status = ACCEPTED

    def decline(self):
        if self.status != PENDING:
            raise ValueError("Only a Pending appointment can be declined.")
        self.status = DECLINED
        self.slot.is_available = True          # slot becomes Available again

    def cancel(self):
        if self.status not in (PENDING, ACCEPTED):
            raise ValueError("This appointment cannot be cancelled.")
        if self.appointment_time <= datetime.now():
            raise ValueError("Only upcoming appointments can be cancelled.")
        self.status = CANCELLED
        self.slot.is_available = True          # free the slot

    def to_dict(self):
        return {"appointment_id": self.appointment_id, "patient_id": self.patient_id,
                "doctor_id": self.doctor_id, "slot_id": self.slot.slot_id,
                "status": self.status}


class Doctor:
    def __init__(self, doctor_id, name):
        self.doctor_id = doctor_id
        self.name = name
        self.slots = []                        # TimeSlot objects (Doctor defines TimeSlot)

    def set_availability(self, slot_id, start_time, minutes=30):          # UC1
        if start_time <= datetime.now():
            raise ValueError("Availability must be in the future.")
        end_time = start_time + timedelta(minutes=minutes)
        for s in self.slots:
            if s.start_time < end_time and start_time < s.end_time:
                raise ValueError("This overlaps an existing slot.")
        slot = TimeSlot(slot_id, self.doctor_id, start_time, end_time, True)
        self.slots.append(slot)
        return slot

    def available_slots(self):
        now = datetime.now()
        return sorted((s for s in self.slots if s.is_available and s.start_time > now),
                      key=lambda s: s.start_time)

    def accept_appointment(self, appointment):                            # UC4
        appointment.accept()

    def decline_appointment(self, appointment):                           # UC4
        appointment.decline()

    def to_dict(self):
        return {"doctor_id": self.doctor_id, "name": self.name,
                "slots": [s.to_dict() for s in self.slots]}


class Patient:
    def __init__(self, patient_id, name):
        self.patient_id = patient_id
        self.name = name
        self.appointments = []
        self.records = []

    def upcoming_count(self):
        return sum(1 for a in self.appointments if a.is_upcoming())

    def to_dict(self):
        return {"patient_id": self.patient_id, "name": self.name}


# ------------------------------------------------------------------- system
class BookingSystem:
    def __init__(self):
        self.doctors = {}
        self.patients = {}
        self.appointments = {}
        self.slots = {}
        self.records = {}
        self.counters = {"D": 0, "P": 0, "S": 0, "A": 0, "R": 0}

    def new_id(self, prefix):
        self.counters[prefix] += 1
        return f"{prefix}{self.counters[prefix]}"

    # ---- registration
    def add_doctor(self, name):
        d = Doctor(self.new_id("D"), name)
        self.doctors[d.doctor_id] = d
        return d

    def add_patient(self, name):
        p = Patient(self.new_id("P"), name)
        self.patients[p.patient_id] = p
        return p

    # ---- UC1
    def set_availability(self, doctor, start_time, minutes=30):
        slot = doctor.set_availability(self.new_id("S"), start_time, minutes)
        self.slots[slot.slot_id] = slot
        return slot

    # ---- UC2 (R1, R6)
    def view_availability(self, doctor):
        start = time.perf_counter()
        slots = doctor.available_slots()
        elapsed = time.perf_counter() - start
        return slots, elapsed

    # ---- UC3 (R2, R4) : follows the sequence diagram order
    def book_appointment(self, patient, doctor, slot_id):
        if patient.upcoming_count() >= N:                       # limit check first
            raise ValueError("Maximum upcoming appointments reached.")
        slot = self.slots.get(slot_id)
        if slot is None or slot.doctor_id != doctor.doctor_id:
            raise ValueError("Slot not found for this doctor.")
        if not slot.is_available or slot.start_time <= datetime.now():
            raise ValueError("Slot is no longer available. Please choose another slot.")
        appt = Appointment(self.new_id("A"), patient.patient_id, doctor.doctor_id, slot, PENDING)
        slot.is_available = False                               # mark slot as booked
        self.appointments[appt.appointment_id] = appt
        patient.appointments.append(appt)
        return appt

    # ---- UC4 helpers
    def pending_for(self, doctor):
        return sorted((a for a in self.appointments.values()
                       if a.doctor_id == doctor.doctor_id and a.status == PENDING
                       and a.appointment_time > datetime.now()),
                      key=lambda a: a.appointment_time)

    # ---- medical records (R5: staff = doctors only)
    def doctor_can_access(self, doctor, patient):
        return any(a.doctor_id == doctor.doctor_id and a.status in (PENDING, ACCEPTED)
                   for a in patient.appointments)

    def add_record(self, doctor, patient, data):
        if not self.doctor_can_access(doctor, patient):
            raise PermissionError("Access denied: authorized staff only.")
        r = MedicalRecord(self.new_id("R"), patient.patient_id, data)
        self.records[r.record_id] = r
        patient.records.append(r)
        return r

    def view_records(self, doctor, patient):
        if not self.doctor_can_access(doctor, patient):
            raise PermissionError("Access denied: authorized staff only.")
        return patient.records

    # ---- persistence
    def save(self):
        data = {
            "counters": self.counters,
            "doctors": [d.to_dict() for d in self.doctors.values()],
            "patients": [p.to_dict() for p in self.patients.values()],
            "appointments": [a.to_dict() for a in self.appointments.values()],
            "records": [r.to_dict() for r in self.records.values()],
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load(self):
        if not os.path.exists(DATA_FILE):
            return False
        with open(DATA_FILE, encoding="utf-8") as f:
            data = json.load(f)
        self.counters = data["counters"]
        for d in data["doctors"]:
            doc = Doctor(d["doctor_id"], d["name"])
            for s in d["slots"]:
                slot = TimeSlot.from_dict(s)
                doc.slots.append(slot)
                self.slots[slot.slot_id] = slot
            self.doctors[doc.doctor_id] = doc
        for p in data["patients"]:
            self.patients[p["patient_id"]] = Patient(p["patient_id"], p["name"])
        for a in data["appointments"]:
            appt = Appointment(a["appointment_id"], a["patient_id"], a["doctor_id"],
                               self.slots[a["slot_id"]], a["status"])
            self.appointments[appt.appointment_id] = appt
            self.patients[appt.patient_id].appointments.append(appt)
        for r in data["records"]:
            rec = MedicalRecord.from_dict(r)
            self.records[rec.record_id] = rec
            self.patients[rec.patient_id].records.append(rec)
        return True


# ---------------------------------------------------------------------- CLI
def ask(prompt):
    return input(prompt).strip()


def pick(options, label):
    """options: dict id -> object with .name"""
    if not options:
        print(f"No {label}s registered yet.")
        return None
    for k, v in options.items():
        print(f"  {k}: {v.name}")
    key = ask(f"Enter {label} ID: ").upper()
    if key not in options:
        print("Invalid ID.")
        return None
    return options[key]


def show_slots(slots):
    if not slots:
        print("No available times.")
        return
    print(f"{'Slot':<6}{'Start':<18}{'End':<18}")
    for s in slots:
        print(f"{s.slot_id:<6}{fmt(s.start_time):<18}{fmt(s.end_time):<18}")


def show_appointments(system, appts):
    if not appts:
        print("No appointments.")
        return
    print(f"{'ID':<6}{'Date/Time':<18}{'Doctor':<20}{'Status':<10}")
    for a in sorted(appts, key=lambda x: x.appointment_time):
        doc = system.doctors[a.doctor_id].name
        print(f"{a.appointment_id:<6}{fmt(a.appointment_time):<18}{doc:<20}{a.status:<10}")


def patient_menu(system, patient):
    while True:
        print(f"\n--- Patient: {patient.name} ({patient.patient_id}) | "
              f"upcoming {patient.upcoming_count()}/{N} ---")
        print("1. View doctor availability")
        print("2. Book an appointment")
        print("3. View my appointments")
        print("4. Cancel an appointment")
        print("0. Back")
        c = ask("Choice: ")
        try:
            if c == "1":                                                  # UC2
                doc = pick(system.doctors, "doctor")
                if doc:
                    slots, elapsed = system.view_availability(doc)
                    show_slots(slots)
                    print(f"(loaded in {elapsed:.4f}s)")
            elif c == "2":                                                # UC3
                doc = pick(system.doctors, "doctor")
                if doc:
                    slots, _ = system.view_availability(doc)
                    show_slots(slots)
                    if slots:
                        sid = ask("Slot ID to book: ").upper()
                        a = system.book_appointment(patient, doc, sid)
                        system.save()
                        print(f"Booking request confirmed: {a.appointment_id} "
                              f"on {fmt(a.appointment_time)} (status {a.status}).")
            elif c == "3":                                                # UC5
                show_appointments(system, patient.appointments)
            elif c == "4":                                                # UC6
                upcoming = [a for a in patient.appointments if a.is_upcoming()]
                show_appointments(system, upcoming)
                if upcoming:
                    aid = ask("Appointment ID to cancel: ").upper()
                    appt = next((a for a in upcoming if a.appointment_id == aid), None)
                    if not appt:
                        print("Appointment not found.")
                    else:
                        appt.cancel()
                        system.save()
                        print("Cancellation confirmed.")
            elif c == "0":
                return
            else:
                print("Invalid choice.")
        except (ValueError, PermissionError) as e:
            print("Error:", e)


def doctor_menu(system, doctor):
    while True:
        print(f"\n--- Doctor: {doctor.name} ({doctor.doctor_id}) ---")
        print("1. Set availability")
        print("2. View my available slots")
        print("3. Accept / decline pending requests")
        print("4. Add medical record for a patient")
        print("5. View a patient's medical records")
        print("0. Back")
        c = ask("Choice: ")
        try:
            if c == "1":                                                  # UC1
                t = parse(ask(f"Start time ({DATE_FMT}): "))
                m = ask("Duration in minutes [30]: ")
                slot = system.set_availability(doctor, t, int(m) if m else 30)
                system.save()
                print(f"Slot {slot.slot_id} saved: {fmt(slot.start_time)} -> {fmt(slot.end_time)}")
            elif c == "2":
                show_slots(doctor.available_slots())
            elif c == "3":                                                # UC4
                pending = system.pending_for(doctor)
                if not pending:
                    print("No pending requests.")
                    continue
                for a in pending:
                    pname = system.patients[a.patient_id].name
                    print(f"  {a.appointment_id}: {pname} at {fmt(a.appointment_time)}")
                aid = ask("Appointment ID: ").upper()
                appt = next((a for a in pending if a.appointment_id == aid), None)
                if not appt:
                    print("Appointment not found.")
                    continue
                act = ask("(A)ccept or (D)ecline: ").lower()
                if act == "a":
                    doctor.accept_appointment(appt)
                    print("Appointment Accepted.")
                elif act == "d":
                    doctor.decline_appointment(appt)
                    print("Appointment Declined. Slot is available again.")
                else:
                    print("Invalid choice.")
                    continue
                system.save()
            elif c in ("4", "5"):                                         # R5
                pat = pick(system.patients, "patient")
                if not pat:
                    continue
                if c == "4":
                    r = system.add_record(doctor, pat, ask("Medical data: "))
                    system.save()
                    print(f"Record {r.record_id} added.")
                else:
                    recs = system.view_records(doctor, pat)
                    if not recs:
                        print("No records.")
                    for r in recs:
                        print(f"  {r.record_id}: {r.medical_data}")
            elif c == "0":
                return
            else:
                print("Invalid choice.")
        except (ValueError, PermissionError) as e:
            print("Error:", e)


def seed(system):
    """Demo data so the program is usable on first run."""
    d1 = system.add_doctor("Dr. Ali")
    d2 = system.add_doctor("Dr. Mona")
    system.add_patient("Fatma")
    system.add_patient("Nawal")
    base = datetime.now().replace(minute=0, second=0, microsecond=0) + timedelta(days=1, hours=1)
    for i in range(4):
        system.set_availability(d1, base + timedelta(hours=i))
    for i in range(2):
        system.set_availability(d2, base + timedelta(days=1, hours=i))
    system.save()


def main():
    system = BookingSystem()
    if not system.load():
        seed(system)
        print("Demo data created (2 doctors, 2 patients).")

    while True:
        print("\n===== Doctor Appointment Booking System =====")
        print("1. Login as Patient")
        print("2. Login as Doctor")
        print("3. Register new Patient")
        print("4. Register new Doctor")
        print("0. Exit")
        c = ask("Choice: ")
        if c == "1":
            p = pick(system.patients, "patient")
            if p:
                patient_menu(system, p)
        elif c == "2":
            d = pick(system.doctors, "doctor")
            if d:
                doctor_menu(system, d)
        elif c == "3":
            name = ask("Name: ")
            if name:
                p = system.add_patient(name)
                system.save()
                print(f"Registered. Your ID is {p.patient_id}")
        elif c == "4":
            name = ask("Name: ")
            if name:
                d = system.add_doctor(name)
                system.save()
                print(f"Registered. Your ID is {d.doctor_id}")
        elif c == "0":
            print("Goodbye!")
            break
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()
