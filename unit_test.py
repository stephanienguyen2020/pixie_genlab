import unittest
from system import System
from objects import Patient, Nurse
import pytest
from bson import ObjectId


def test_ping_database():
    # Add your test logic here
    system = System()
    assert system.ping_database() == True


def test_create_patient():
    # Add your test logic here
    system = System()

    nurse = Nurse("Jane", "Doe", "123", "9am-5pm", "123-456-7890", "locvicvn1234@gmail.com")
    nurse_id = system.create_nurse(nurse)
    assert isinstance(nurse_id, ObjectId)

    first_name = "Alex"
    last_name = "Doan"
    age = 27
    dob = "01/01/1996"
    address = "123 Main St"
    weight = 180
    blood_type = "O+"
    phone = "123-456-7890"
    email = "johndoe@gmail.com"
    gender = "female"
    room_number = "123"
    assign_nurse_id = str(nurse_id)
    order = 1
    note = ""

    patient = Patient(
        first_name,
        last_name,
        age,
        dob,
        address,
        weight,
        blood_type,
        phone,
        email,
        gender,
        room_number,
        assign_nurse_id,
        order,
        note,
    )
    assert isinstance(patient, Patient)
    patient_id = system.create_patient(patient)
    assert isinstance(patient_id, ObjectId)


if __name__ == "__main__":
    pytest.main(["-s", "unit_test.py"])
