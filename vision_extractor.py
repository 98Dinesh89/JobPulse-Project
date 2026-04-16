import base64
import json
from groq import Groq

client = Groq(api_key="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")


def extract_skills_from_image(uploaded_file):
    image_bytes = uploaded_file.read()
    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    prompt = """
    Analyze this resume image.

    Extract:
    - technical skills
    - frameworks
    - databases
    - cloud/devops tools
    - methodologies

    Prioritize technical skills over soft skills.

    Return ONLY JSON:
    {
        "skills": []
    }
    """

    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        temperature=0
    )

    content = response.choices[0].message.content.strip()
    content = content.replace("```json", "").replace("```", "").strip()

    start = content.find("{")
    end = content.rfind("}") + 1

    if start != -1 and end != -1:
        content = content[start:end]

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"[vision_extractor] JSON parse failed: {e}\nRaw content: {content}")
        return {"skills": []}