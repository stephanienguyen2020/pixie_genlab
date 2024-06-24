from pymongo import MongoClient
import os
from dotenv import load_dotenv
from objects import Patient, Nurse
import qrcode
import google.generativeai as genai
from bson import ObjectId
import resend

load_dotenv(override=True)


class System:
    def __init__(self):
        self.client = MongoClient(os.getenv("MONGODB_URI"))

    def ping_database(self):
        """Check if the database is connected"""
        try:
            self.client.admin.command("ping")
            return True
        except Exception as e:
            return False

    def create_patient(self, patient_info: Patient):
        """Create a new patient in the database

        Args:
            patient_info (Patient): The patient information

        Returns:
            str: The patient ID"""
        if self.find_patient(
            patient_info.first_name,
            patient_info.last_name,
            patient_info.dob,
            patient_info.email,
        ):
            print("Patient already exists")
            return self.get_patient(
                self.find_patient(
                    patient_info.first_name,
                    patient_info.last_name,
                    patient_info.dob,
                    patient_info.email,
                )["_id"]
            )["_id"]
        else:
            result = self.client["nursecheck"]["patients"].insert_one(
                patient_info.to_dict()
            )
            patient_id = result.inserted_id
            assert self.generate_qr_code(
                patient_id
            ) == "QR code generated for patient {}".format(patient_id)
            return patient_id

    def find_patient(self, first_name, last_name, dob, email):
        patient = self.client["nursecheck"]["patients"].find_one(
            {
                "first_name ": first_name,
                "last_name": last_name,
                "dob": dob,
                "email": email,
            }
        )
        return patient

    def get_patient(self, patient_id):
        """Get the patient information from the database

        Args:
            patient_id (str): The patient ID

        Returns:
            dict: The patient information"""
        patient = self.client["nursecheck"]["patients"].find_one(
            {"_id": ObjectId(patient_id)}
        )
        return patient

    def get_patient_record(self, patient_id):
        """Get the patient record from the database

        Args:
            patient_id (str): The patient ID"""
        patient = self.client["nursecheck"]["records"].find_one(
            {"patient_id": patient_id}
        )
        return patient

    def update_patient_record(self, patient_id, new_note, timestamp):
        """Update the patient record in the database

        Args:
            patient_id (str): The patient ID
            new_note (str): The new note
            timestamp (str): The timestamp"""
        patient = self.get_patient_record(patient_id)
        patient["notes"].append({"content": new_note, "timestamp": timestamp})
        self.client["nursecheck"]["records"].update_one(
            {"patient_id": patient_id}, {"$set": patient}
        )
        return "Patient record updated"

    def delete_patient(self, patient_id):
        """Delete the patient from the database

        Args:
            patient_id (str): The patient ID"""
        self.client["nursecheck"]["patients"].delete_one({"_id": patient_id})
        self.delete_qr_code(patient_id)
        return "Patient deleted"

    def generate_qr_code(self, patient_id: str):
        """Generate a QR code for the patient"""
        img = qrcode.make(patient_id)

        img.save("qr_code/patient_{}_qrcode.png".format(patient_id))
        return "QR code generated for patient {}".format(patient_id)

    def delete_qr_code(self, patient_id):
        """Delete the QR code for the patient"""
        os.remove("qr_code/patient_{}_qrcode.png".format(patient_id))

    def show_qr_code(self, patient_id):
        """Show the QR code for the patient"""
        img = qrcode.make(patient_id)
        img.show()
        return "QR code shown for patient {}".format(patient_id)

    def get_all_patients(self):
        """Retrieve all patients from the database"""
        patients = self.client["nursecheck"]["patients"].find()
        return [patient for patient in patients]

    def get_all_documents(self):
        """Retrieve all documents from the database"""
        documents = self.client["nursecheck"]["documents"].find()
        return [document for document in documents]

    def retrieve_conversations(self, patient_id):
        """Retrieve the conversation between nurse and patient from the database"""
        documents = self.get_all_documents()
        conversations = [
            document
            for document in documents
            if document["patient_id"] == ObjectId(patient_id)
        ]
        return conversations

    def get_latest_conversation(self, patient_id):
        """Retrieve the latest conversation between nurse and patient from the database"""
        conversations = self.retrieve_conversations(patient_id)
        return conversations[-1]

    def convert_dict_to_text(self, conversation):
        """Convert the conversation from dictionary to text"""
        content = conversation["content"]
        text = ""
        for c in content:
            text += c["question"] + "\n"
            text += c["answer"] + "\n"
        return text

    def update_patient_order(self, patient_id, order, note):
        """Update the order of the patient"""
        patient = self.get_patient(patient_id)
        patient["order"] = order
        patient["note"] = note
        self.client["nursecheck"]["patients"].update_one(
            {"_id": patient_id}, {"$set": patient}
        )
        return "Patient order updated"

    def process_patient(self, patient_id):
        """Process the patient information"""
        patient = self.get_patient(patient_id)
        if patient["process"] is True:
            patient["process"] = False
        else:
            patient["process"] = True
        self.client["nursecheck"]["patients"].update_one(
            {"_id": ObjectId(patient_id)}, {"$set": patient}
        )

    def check_patients_order(self):
        """Check the order of the patients"""
        patients = self.get_all_patients()
        # patients = [patient for patient in patients if patient["assign_nurse_id"] == nurse_id]
        sort_order = sorted(patients, key=lambda x: x["order"], reverse=True)
        # handle duplicate

        print("Patients order:")

        result_dict = set()

        
        return sort_order

    def create_nurse(self, nurse_info: Nurse):
        """Create a new nurse in the database"""
        if self.find_nurse(
            nurse_info.first_name,
            nurse_info.last_name,
            nurse_info.age,
            nurse_info.phone,
        ):
            print("Nurse already exists")
            return self.get_nurse(
                self.find_nurse(
                    nurse_info.first_name,
                    nurse_info.last_name,
                    nurse_info.age,
                    nurse_info.phone,
                )["_id"]
            )["_id"]
        else:
            result = self.client["nursecheck"]["nurses"].insert_one(
                nurse_info.to_dict()
            )
            return result.inserted_id

    def get_nurse(self, nurse_id):
        """Get the nurse information from the database"""
        nurse = self.client["nursecheck"]["nurses"].find_one(
            {"_id": ObjectId(nurse_id)}
        )
        return nurse

    def get_all_nurses(self):
        """Retrieve all nurses from the database"""
        nurses = self.client["nursecheck"]["nurses"].find()
        return [nurse for nurse in nurses]

    def delete_nurse(self, nurse_id):
        """Delete the nurse from the database"""
        self.client["nursecheck"]["nurses"].delete_one({"_id": ObjectId(nurse_id)})
        return "Nurse deleted"

    def update_nurse(self, nurse_id, nurse_info):
        """Update the nurse information in the database"""
        self.client["nursecheck"]["nurses"].update_one(
            {"_id": ObjectId(nurse_id)}, {"$set": nurse_info}
        )
        return "Nurse information updated"

    def find_nurse(self, first_name, last_name, age, phone):
        """Find the nurse in the database"""
        nurse = self.client["nursecheck"]["nurses"].find_one(
            {
                "first_name": first_name,
                "last_name": last_name,
                "age": age,
                "phone": phone,
            }
        )
        return nurse

    def assign_patient_to_nurse(self, patient_id, nurse_id):
        """Assign the patient to a nurse"""
        patient = self.get_patient(patient_id)
        patient["assign_nurse_id"] = nurse_id
        self.client["nursecheck"]["patients"].update_one(
            {"_id": ObjectId(patient_id)}, {"$set": patient}
        )
        return "Patient assigned to nurse"

    def send_email(self, nurse_id, patient_id):
        """Send an email to the patient"""
        nurse = self.get_nurse(nurse_id)
        patient = self.get_patient(patient_id)
        email = nurse["email"]
        resend.api_key = os.getenv("RESEND_API_KEY")

        title = "Urgent care alert for nurse {}".format(nurse["first_name"] + " " + nurse["last_name"])

        r = resend.Emails.send(
            {
                "from": "onboarding@resend.dev",
                "to": str(email),
                "subject": title,
                "html": """
                        <html>
                            <ul>
                                <li> Patient: {} (ID: {})</li>
                                <li> Status: Emergent </li>
                                <li> Action Required: Immediate attention needed. Review patient details promptly and proceed with urgent care protocols. </li>
                            </ul>
                        </html>
                        """.format(patient["first_name"] + " " + patient["last_name"], patient_id),
            }
        )
