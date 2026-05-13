import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

PLAN_PROMPT = """You are a senior Java Spring Boot developer.
Using ONLY the wiki context below, create a detailed implementation plan.

WIKI CONTEXT:
{context}

REQUIREMENT: {requirement}

Respond in this exact format:

## Affected Classes
List each class that needs to change and why.

## Implementation Plan
For each affected class, list specific changes:
- Method to add/modify
- Field to add/modify
- Logic to implement

## New Classes Needed
List any new classes/interfaces required. Write NONE if not needed.

## Risks & Edge Cases
List potential issues, validation gaps, or edge cases to handle.

Be specific — reference actual class names and method names from the context."""


def generate_plan(requirement: str, context: str) -> dict:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{
            "role": "user",
            "content": PLAN_PROMPT.format(
                context=context,
                requirement=requirement
            )
        }],
        max_tokens=800,
        temperature=0.2
    )
    return {
        "plan":          response.choices[0].message.content.strip(),
        "prompt_tokens": response.usage.prompt_tokens,
        "output_tokens": response.usage.completion_tokens,
        "total_tokens":  response.usage.total_tokens
    }