from openai import AsyncOpenAI
from app.config import settings
import json

client = AsyncOpenAI(
    api_key=settings.groq_api_key,
    base_url=settings.groq_base_url
)

async def judge(input_payload, expected_behaviour, actual_output, rules):
    response = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", 
                   "content": f'''You are an evaluator for an AI system.

                    Rubric rules the output must satisfy: {rules}
                    User input sent to the system: {input_payload}
                    Expected behaviour: {expected_behaviour}
                    Actual output received: {actual_output}

                    Evaluate whether the actual output satisfies ALL rubric rules and matches the expected behaviour.

                    Respond in JSON only:
                    {{"passed": true/false, "violations": ["rule it broke", ...], "reasoning": "one paragraph explanation"}}'''}]
        )

    raw = response.choices[0].message.content
    raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(raw)