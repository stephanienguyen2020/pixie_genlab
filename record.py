from pymongo import MongoClient
import os
from dotenv import load_dotenv
from system import System
from pdf import PDF
import google.generativeai as genai
from datetime import datetime

load_dotenv(override=True)

class Record:
    def __init__(self, conversation=None):
        """
        Args: 
            conversation (list): A list of conversation between nurse and patient. 
        """
        
        if conversation:
            self.conversation = conversation
        else:
            self.conversation = []
        self.client = MongoClient(os.getenv("MONGODB_URI"))
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel('gemini-pro')

    def check_conversation(self, patient_id):
        """Check if the latest conversation is processed or not.
        If not process, process the conversation, change the processed status to True,
        and process.
        """
        system = System()
        conversation_dict = system.get_latest_conversation(patient_id)
        if conversation_dict["processed"]:
            return "Conversation has been processed"
        else:
            return conversation_dict["content"]

    def process_conversation(self, conversation):
        """Process the conversation and output to document DB with timestamp.
        Use Gemini with functional calling to generate a record from a conversation.
        """
        today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        response = self.summarize_conversation(conversation)

        result = response.text

        return {"content": result, "timestamp": today}

    def summarize_conversation(self, conversation):
        """Summarize the conversation. 
        """
        task_description = ("I'm going to give you a list of questions and answers between nurse and patient. "
                            "You will give me a summary of the conversation.")
        response = self.model.generate_content(task_description)

        conversation_data = "\n".join([f"{qa['question']}\n{qa['answer']}" for qa in conversation["content"]])
        query = "Here is the conversation:\n" + conversation_data
        response = self.model.generate_content(query)

        return response.text

    def save_record(self, record):
        """Save the record to document DB. 
        """
        db = self.client.get_database()
        collection_name = "records"

        if collection_name not in db.list_collection_names():
            db.create_collection(collection_name)

        records_collection = db.get_collection(collection_name)

        records_collection.insert_one(record)
    
    def get_record(self, patient_id):
        system = System()
        patient_info = system.get_patient(patient_id)
        patient_id = patient_info["_id"]
        
        result = self.client["nursecheck"]["records"].find_one({"patient_id": patient_id})
        return result


    def update_record(self, patient_id, processed_conversation):
        """Generate a record from a conversation."""
        system = System()
        patient_info = system.get_patient(patient_id)
        patient_id = patient_info["_id"]
        patient_name = patient_info["first_name"] + " " + patient_info["last_name"]
        patient_age = patient_info["age"]
        patient_gender = patient_info["gender"]
        patient_weight = patient_info["weight"]
        patient_blood = patient_info["blood_type"]

        if self.get_record(patient_id):
            record = self.get_record(patient_id)
            record["notes"].append(processed_conversation)
            self.client["nursecheck"]["records"].update_one({"patient_id": patient_id}, {"$set": record})
        else:
            record = {
                "patient_id": patient_id,
                "patient_name": patient_name,
                "age": patient_age,
                "gender": patient_gender,
                "weight": patient_weight,
                "blood_type": patient_blood,
                # "last_updated": processed_conversation["timestamp"],
                "date_created": processed_conversation["timestamp"],
                "notes": [processed_conversation],
                "doctor_id": "789",
            }
            self.client["nursecheck"]["records"].insert_one(record)
        self.generate_record_pdf(patient_id)
        # self.save_record(record)
        return "Record updated successfully"
    
    def generate_record_pdf(self, patient_id):
        pdf = PDF()
        pdf.create_pdf(patient_id)
        return "PDF created successfully"
    
    def generate_record(self, patient_id): 
        conversation = self.check_conversation(patient_id)
        if conversation == "Conversation has been processed":
            return "Conversation has been processed"
        else:
            processed_conversation = self.process_conversation(conversation)
            self.update_record(patient_id, processed_conversation)
            return "Record generated successfully"
        
    def get_latest_record_priority(self, patient_id):
        record = self.get_record(patient_id)
        notes = record["notes"]
        latest_note = notes[-1]
        return latest_note["priority"]
        
if __name__ == "__main__":
    record = Record()
    print(record.generate_record("662d1e3374bc518530842677"))
