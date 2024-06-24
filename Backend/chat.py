import google.generativeai as genai
from pymongo import MongoClient
from hume import HumeVoiceClient, MicrophoneInterface
import os
from system import System
from datetime import datetime
import asyncio
import requests
import json
from dotenv import load_dotenv
from record import Record 
import openai
from openai import OpenAI
load_dotenv(override=True)


class Chat:
    def __init__(self, patient_id):
        if not patient_id:
            raise ValueError("Patient ID is required")
        self.patient_id = patient_id
        self.client = MongoClient(os.getenv("MONGODB_URI"))

    async def record_streaming(self):
        # Retrieve the Hume API key from the environment variables
        HUME_API_KEY = os.getenv("HUME_API_KEY")
        # Connect and authenticate with Hume
        client = HumeVoiceClient(HUME_API_KEY)

        # Start streaming EVI over your device's microphone and speakers 
        async with client.connect(config_id=os.getenv("HUME_CONFIG_ID")) as socket:
            await MicrophoneInterface.start(socket )
        
    def list_chats(self): 
        # Retrieve the Hume API key from the environment variables
        HUME_API_KEY = os.getenv("HUME_API_KEY")
        # Connect and authenticate with Hume
        headers = {
        "X-Hume-Api-Key": HUME_API_KEY
        }
        response = requests.get("https://api.hume.ai/v0/evi/chats", headers=headers, params={"page_size": 45, "page_number": 1})

        return [chat["id"] for chat in response.json()["chats_page"]]

    def get_latest_chat_id(self):
        return self.list_chats()[-1]

    def list_chat_messages(self, chat_id): 
        # Retrieve the Hume API key from the environment variables
        HUME_API_KEY = os.getenv("HUME_API_KEY")
        # Connect and authenticate with Hume
        headers = {
        "X-Hume-Api-Key": HUME_API_KEY
        }
        response = requests.get(f"https://api.hume.ai/v0/evi/chats/{chat_id}", headers=headers)
        result = response.json()
        start_timestamp = result["start_timestamp"]
        end_timestamp = result["end_timestamp"]
        events_page = result["events_page"]
        if events_page:
            emotion_features_dict = json.loads(events_page[0]["emotion_features"])
        else:
            emotion_features_dict = {}

        conversation = []
    
        for event in events_page:
            message = event["message_text"]
            role = event["role"]
            conversation.append({"role": role, "message": message})
            if event["emotion_features"]:
                event_dict = json.loads(event["emotion_features"])
                for key, value in event_dict.items():
                    if key in emotion_features_dict:
                        emotion_features_dict[key] += float(value)
                    else:
                        emotion_features_dict[key] = float(value)

        return {"start_timestamp": start_timestamp, "end_timestamp": end_timestamp, "conversation": conversation, "emotion_features": emotion_features_dict}

    def chat(self):
        try:
            while True:
                asyncio.run(self.record_streaming())
        except KeyboardInterrupt:
            print("Conversation recorded. Processing conversation...")
            self.process_conversation()
            print("Conversation processed. Exiting...")
            return
        
    def process_conversation(self):
        conversation = ""
        emotion_dict = {}
        chat_id = self.get_latest_chat_id()
        chat_messages = self.list_chat_messages(chat_id)
        for message in chat_messages["conversation"]:
            if message["role"] == "USER":
                conversation += "Patient: " + message["message"] + "\n" 
            else: 
                conversation += "Nurse: " + message["message"] + "\n"

        if conversation == "":
            print("No conversation recorded. Exiting...")
            return
        emotion_features = chat_messages["emotion_features"]
        self.client = MongoClient(os.getenv("MONGODB_URI"))
        system = System()
        patient_info = system.get_patient(self.patient_id)
        top_5_emotions = sorted(emotion_features, key=emotion_features.get, reverse=True)[:5]
        for emotion in top_5_emotions:
            emotion_dict[emotion] = round(emotion_features[emotion], 2)
        # emotion_dict = json.dumps(emotion_dict)

        print("Conversation: ", conversation)
        print("Top 5 emotions: ", emotion_dict)

      
        API_BASE = "https://api.01.ai/v1"
        API_KEY = "your key"
        client = OpenAI(
            api_key=API_KEY,
            base_url=API_BASE
        )
        
        completion = client.chat.completions.create(
            model="yi-large",
            messages=[{"role": "user", "content": "From these emotion, determine if there are any negative emotions. Only return True or False.\n {}".format(
                emotion_dict
            )}]
        )
        emotion_result = completion.choices[0].message.content.strip()
        print("Should visit or not based on emotion: ", emotion_result)


        # genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
        # model = genai.GenerativeModel("gemini-1.0-pro-latest")
        # response = model.generate_content(
        #     "From these emotion, determine if there are any negative emotion. Only return True or False.\n {}".format(
        #         emotion_dict
        #     )
        # )

        # emotion_result = response.text


        print("Should visit or not based on emotion: ", emotion_result)

        completion_summary = client.chat.completions.create(
            model="yi-large",
            messages=[{"role": "user", "content": "From the conversation, generate a summarized note on patient's health. Don't overlook anything. Return the summary in 1 line. \n {}".format(
                conversation
            )}]
        )
        summary_result = completion_summary.choices[0].message.content.strip()
        print("Should visit or not based on emotion: ", summary_result)



        # genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
        # model = genai.GenerativeModel("gemini-1.0-pro-latest")
        today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # response = model.generate_content(
        #     "From the conversation, generate a summarized note on patient's health. Don't overlook anything. Return the summary in 1 line. \n {}".format(
        #         conversation
        #     )
        # )

        # summary_result = response.text
        # print("Summary of patient's health: ", summary_result)

        priority_summary = client.chat.completions.create(
            model="yi-large",
            messages=[{"role": "user", "content": "Process the priority of the patient from scale 1-10 based on the conversation and priority.  Return in format <priority number> \n Conversation: {} \n Emotion: {}".format(conversation, emotion_dict)}]
        )

        priority_result = priority_summary.choices[0].message.content.strip()

        # response = model.generate_content("Process the priority of the patient from scale 1-10 based on the conversation and priority.  Return in format <priority number> \n Conversation: {} \n Emotion: {}".format(conversation, emotion_dict))
        # priority_result = response.text
        priority_result = int(priority_result)

        print("Priority of the patient: ", str(priority_result))

        self.save_to_db(patient_info, conversation, top_5_emotions)

        notes_str = summary_result
        assert system.update_patient_order(self.patient_id, str(priority_result), notes_str) == "Patient order updated"

        system = System()
        system.update_patient_order(self.patient_id, str(priority_result), notes_str)
        
        record = Record(conversation)
        record.update_record(self.patient_id, {"content": conversation, "note": notes_str, "timestamp": today, "emotions": emotion_dict, "priority": priority_result})
        
        nurse_id = patient_info["assign_nurse_id"]

        if emotion_result == "True":
            system.send_email(nurse_id, self.patient_id)
            print("Email sent to nurse")
        
        return conversation

    def save_to_db(self, patient_info, conversation, emotions):
        patient_id = patient_info["_id"]
        patient_name = patient_info["first_name"] + " " + patient_info["last_name"]
        content = conversation
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        processed = False

        result = self.client["nursecheck"]["documents"].insert_one(
            {
                "timestamp": timestamp,
                "patient_id": patient_id,
                "patient_name": patient_name,
                "content": content,
                "emotions": emotions,
                "processed": processed,
            }
        )

        return result.inserted_id


if __name__ == "__main__":
    PATIENT_ID = "662eda3d515f741c72939ecf"
    system = System()
    patient_info = system.get_patient(PATIENT_ID)
    if patient_info:
        chat = Chat(PATIENT_ID)
        chat.chat()
    else:
        patient_id = input("Enter the patient ID: ")
        chat = Chat(patient_id)
        chat.chat()

    


