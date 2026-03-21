import json
from openai import AsyncOpenAI
from app.config import settings

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


async def extract_from_image(image_url: str) -> dict:
    """
    Use OpenAI Vision to extract title and description from a screenshot.
    """
    prompt = """Analyze this screenshot and extract:

1. TITLE: The main topic or subject (short, under 10 words)

2. DESCRIPTION: Write a concise summary (2-4 sentences) that captures:
   - The KEY INSIGHT or main point being communicated
   - Why it matters or what makes it useful
   - For diagrams/visuals: explain the concept, not just list what's shown

DO NOT just list visual elements or text you see. Instead, synthesize and explain the meaning.

Bad example: "The image shows three circles labeled A, B, C with arrows between them."
Good example: "This illustrates how A triggers B, which then feeds back to C, creating a continuous loop."

Return JSON format:
{"title": "...", "description": "..."}

Return ONLY valid JSON, no markdown."""

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            }
        ],
        max_tokens=1000,
    )

    content = response.choices[0].message.content.strip()

    # Clean up response - remove markdown code blocks if present
    if content.startswith("```"):
        content = content.split("\n", 1)[1]  # Remove first line
        content = content.rsplit("```", 1)[0]  # Remove last ```

    return json.loads(content)
