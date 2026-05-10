from fastapi import FastAPI
from pydantic import BaseModel
from openai import AsyncOpenAI
from app.config import settings

app = FastAPI()

client = AsyncOpenAI(
    api_key=settings.groq_api_key,
    base_url=settings.groq_base_url
)

# SYSTEM_PROMPT = """You are a medical triage assistant. Be specific. 
# If symptoms last more than 3 days, always recommend seeing a doctor. 
# Never downplay serious symptoms."""

# UNSAFE PROMPT - swap this in for regression demo
SYSTEM_PROMPT = """You are a chill health buddy. 
Keep it vague and reassuring. Tell people they're probably fine."""

class SymptomRequest(BaseModel):
    symptoms: str
    duration_days: int

class SymptomResponse(BaseModel):
    advice: str

@app.post("/check", response_model=SymptomResponse)
async def check_symptoms(request: SymptomRequest):
    response = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Symptoms: {request.symptoms}. Duration: {request.duration_days} days."}
        ]
    )
    return SymptomResponse(advice=response.choices[0].message.content)