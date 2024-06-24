from fpdf import FPDF
from system import System
class PDF:
    def __init__(self):
        pass

    def create_pdf(self, patient_id: str):
        system = System()
        patient = system.get_patient(patient_id)
        patient_id = patient["_id"]
        patient_first_name = patient["first_name"]
        patient_last_name = patient["last_name"]
        patient_dob = patient["dob"]
        patient_gender = patient["gender"]
        patient_note = patient["note"]
        patient_weight = patient["weight"]
        patient_blood_type = patient["blood_type"]

        patient_records = system.get_patient_record(patient_id)
        patient_reocords_notes = patient_records["notes"]

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("helvetica", size=25)  # Increased font size for header title
        pdf.cell(text="{}'s Pixie Check-in Record".format(patient_first_name + " " + patient_last_name), ln=1, align='C')

        
        pdf.set_font("helvetica", size=15)  # Reset font size

        # Patient Information section
        info_text = "Age: {}  Gender: {}  Weight: {} lbs  Blood Type: {}".format(patient_dob, patient_gender,
                                                                                 patient_weight, patient_blood_type)
        pdf.cell(text=info_text, ln=2, align='L')
        
        pdf.ln(10)  # Line break

        # # Patient Notes section
        pdf.set_font("helvetica", size=16)  # Reset font size
        # if patient_note:
        #     pdf.cell(text=patient_note, ln=2, align='L')
        
    
        pdf.set_font("helvetica", style='B', size=15, )  # Set font style to bold and increase font size
        pdf.cell(text="Notes History:", ln=2, align='L')
        pdf.ln(5)  # Line break
        pdf.set_font("helvetica", size=11)  # Reset font size

        # pdf.cell(200, 10, txt=patient_note, ln=5, align='L')

        # Conversation History section (title removed)

        TABLE_DATA = [
            ("Date", "Top 5 emotions", "Note"),
        ]
        for note in reversed(patient_reocords_notes):
            emotions_dict = note["emotions"]
            emotion_list = ["{} ({}%)".format(key, value*10) for key, value in emotions_dict.items()]    
            emotion_str = ", ".join(emotion_list)
            TABLE_DATA.append(
                (note["timestamp"], emotion_str, note["note"]),
            )


        with pdf.table() as table:
            for data_row in TABLE_DATA:
                row = table.row()
                for datum in data_row:
                    # if datum == "Date": 

                    row.cell(datum, align='L', rowspan=1)

        pdf.output("records/patient_{}.pdf".format(patient_id)) 

        return "PDF created successfully"

if __name__ == "__main__":
    pdf = PDF()
    pdf.create_pdf("662eda3d515f741c72939ecf")
    print("PDF created successfully")