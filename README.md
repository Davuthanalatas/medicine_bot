# Pharmacist Bot 💊

A CLI chatbot that answers questions about 6 medicines using OpenAI function calling.

## Medicines covered
aspirin, ibuprofen, paracetamol, amoxicillin, metformin, lisinopril

## Topics available
dosage, how_to_take, side_effects, interactions, contraindications, missed_dose

## How it works
- User asks a question
- OpenAI decides which function to call
- Bot looks up real data from local database
- OpenAI forms the final answer using only that real data
- No hallucination possible

## How to run
1. Add your OpenAI API key to `.env`
2. Install dependencies: `pip install openai python-dotenv`
3. Run: `python medicine_bot_template.py`

## Assignment
SAMK - AI and Data Engineering
Function Calling as Accurate RAG exercise