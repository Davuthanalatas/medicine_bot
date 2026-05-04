

import openai
import json
import os
import sys
from dotenv import load_dotenv
import os

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")






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



# system message and memory
messages = [
    {
        "role": "system",
        "content": (
            "You are a professional and friendly pharmacist assistant. "
            "You ONLY answer questions about these six medicines: "
            "aspirin, ibuprofen, paracetamol, amoxicillin, metformin, lisinopril. "
            "You MUST always call the appropriate function before answering. "
            "Never answer from memory or guess. "
            "If asked about anything else, politely redirect."
        )
    }
]

print("Pharmacist Bot ready. Type 'exit' or 'quit' to stop.\n")

while True:
    # get user input
    user_input = input("You: ").strip()
    if user_input.lower() in ("exit", "quit"):
        print("Pharmacist: Take care! Goodbye.")
        break

    # add user message to memory
    messages.append({"role": "user", "content": user_input})

    # TODO-1: first API call
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=[{"type": "function", "function": schema} for schema in FUNCTION_SCHEMAS],
        tool_choice="auto"
    )
    assistant_message = response.choices[0].message

    # TODO-2: check if function call or direct answer
    if assistant_message.tool_calls is None:
        # direct answer - out of scope question
        print("Pharmacist:", assistant_message.content)
        messages.append({"role": "assistant", "content": assistant_message.content})

    else:
        # TODO-3: run local lookup
        tool_call = assistant_message.tool_calls[0]
        fn_name = tool_call.function.name
        fn_args = json.loads(tool_call.function.arguments)
        tool_call_id = tool_call.id
        result = LOCAL_FUNCTIONS[fn_name](fn_args)

        # TODO-4: send result back, get final answer
        messages.append(assistant_message)
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": fn_name,
            "content": result
        })

        final_response = openai.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=[{"type": "function", "function": schema} for schema in FUNCTION_SCHEMAS],
        )
        final_answer = final_response.choices[0].message.content
        print("Pharmacist:", final_answer)
        messages.append({"role": "assistant", "content": final_answer})