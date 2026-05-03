

import openai
import json
import os
import sys

openai.api_key = "find_the_cource_API_key_from_moodle"  # assume API key is set




# ──────────────────────────────────────────────────────────────────────
# Function schemas the model may invoke
# ──────────────────────────────────────────────────────────────────────
ALLOWED_TOPICS = [
    "dosage",
    "how_to_take",
    "side_effects",
    "interactions",
    "contraindications",
    "missed_dose",
]

FUNCTION_SCHEMAS = []
MEDICINES = ["aspirin", "ibuprofen", "paracetamol",
             "amoxicillin", "metformin", "lisinopril"]

for med in MEDICINES:
    FUNCTION_SCHEMAS.append({
        "name": f"get_{med}_info",
        "description": f"Get information about using {med.capitalize()}.",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": (
                        "Optional. One of: dosage, how_to_take, side_effects, "
                        "interactions, contraindications, missed_dose. "
                        "If omitted, the function returns all topics."
                    ),
                    "enum": ALLOWED_TOPICS
                }
            },
            "required": []           # topic is optional
        }
    })

# ──────────────────────────────────────────────────────────────────────
# 2️⃣  Imaginary knowledge base
# ──────────────────────────────────────────────────────────────────────
MEDICINE_DATA = {
    "aspirin": {
        "dosage": "Adults: 325–650 mg every 4–6 h (max 4 g/day).",
        "how_to_take": "Take with food or a full glass of water.",
        "side_effects": "Gastric irritation, heartburn; rare bleeding.",
        "interactions": "Warfarin, corticosteroids, alcohol ↑ bleeding risk.",
        "contraindications": "Peptic-ulcer disease, aspirin allergy, viral illness in children (Reye risk).",
        "missed_dose": "Take when remembered unless it’s almost time for the next dose."
    },
    "ibuprofen": {
        "dosage": "Adults: 200–400 mg every 4–6 h. Max 1.2 g/day OTC or 3.2 g/day Rx.",
        "how_to_take": "Best with food or milk to reduce GI upset.",
        "side_effects": "Dyspepsia, dizziness, fluid retention; rare GI bleed.",
        "interactions": "May blunt aspirin’s antiplatelet effect; ↑ GI-bleed risk with anticoagulants.",
        "contraindications": "Active GI bleed/ulcer, severe heart failure, 3rd-trimester pregnancy.",
        "missed_dose": "Take promptly; skip if near next dose—do not double."
    },
    "paracetamol": {
        "dosage": "Adults: 500–1000 mg every 4–6 h (max 4 g/day; 3 g chronic).",
        "how_to_take": "With or without food; glass of water advised.",
        "side_effects": "Well-tolerated; rash rare; hepatotoxic at high dose.",
        "interactions": "Alcohol ↑ hepatotoxicity; chronic use ↑ warfarin INR.",
        "contraindications": "Severe hepatic impairment.",
        "missed_dose": "Take when remembered unless close to next dose."
    },
    "amoxicillin": {
        "dosage": "500 mg every 8 h or 875 mg every 12 h (typical adult).",
        "how_to_take": "May be taken with or without food.",
        "side_effects": "Diarrhea, nausea, rash.",
        "interactions": "May ↓ OCP efficacy; ↑ warfarin effect.",
        "contraindications": "Penicillin allergy; mono (↑ rash).",
        "missed_dose": "Take ASAP; skip if almost time for next dose."
    },
    "metformin": {
        "dosage": "Start 500 mg once–twice daily with meals; max 2–2.55 g/day.",
        "how_to_take": "Always with meals.",
        "side_effects": "GI upset, B₁₂ deficiency; very rare lactic acidosis.",
        "interactions": "Contrast media ↑ acidosis risk; cimetidine ↓ clearance.",
        "contraindications": "eGFR < 30 mL/min, severe hepatic disease.",
        "missed_dose": "Take when remembered unless close to next dose."
    },
    "lisinopril": {
        "dosage": "Hypertension: 10–40 mg once daily.",
        "how_to_take": "Same time daily, with or without food.",
        "side_effects": "Dry cough, dizziness, hyperkalemia; rare angioedema.",
        "interactions": "K⁺ supplements/spironolactone ↑ hyperkalemia risk.",
        "contraindications": "Pregnancy, prior ACE-induced angioedema.",
        "missed_dose": "Take ASAP; skip if near next dose."
    }
}

# ──────────────────────────────────────────────────────────────────────
# 3️⃣  Build the six Python functions exposed to the model
# ──────────────────────────────────────────────────────────────────────
def _build_medicine_fn(med_name: str):
    def _fn(args):
        topic = args.get("topic")
        if not topic:
            return "\n".join(
                f"{k.replace('_', ' ').title()}: {v}"
                for k, v in MEDICINE_DATA[med_name].items()
            )
        return MEDICINE_DATA[med_name].get(topic, "Topic not found.")
    return _fn

LOCAL_FUNCTIONS = {
    f"get_{m}_info": _build_medicine_fn(m) for m in MEDICINES
}

# ──────────────────────────────────────────────────────────────────────
# Persistent conversation loop :
# ──────────────────────────────────────────────────────────────────────



SYSTEM_MESSAGE = {
    "role": "system",
    "content": (
        "You are a professional and friendly pharmacist assistant. "
        "You ONLY answer questions about these six medicines: "
        "aspirin, ibuprofen, paracetamol, amoxicillin, metformin, lisinopril. "
        "You MUST always call the appropriate function to retrieve information before answering. "
        "Never answer from memory or guess — only use what the function returns. "
        "If the user asks about anything outside these six medicines, "
        "politely let them know you can only help with these specific medications. "
        "Always be professional, clear, and kind."
    )
}


response = openai.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    tools=[{"type": "function", "function": schema} for schema in FUNCTION_SCHEMAS],
    tool_choice="auto"  # let the model decide whether to call a function
)
assistet_message = response.choices[0].message