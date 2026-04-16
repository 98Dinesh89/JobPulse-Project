import json
from groq import Groq
from analyzer import SKILL_TAXONOMY

client = Groq(api_key="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")


def extract_resume_entities(resume_text):
    allowed_skills = []
    for _, skills in SKILL_TAXONOMY.items():
        allowed_skills.extend(skills)

    prompt = f"""
    You are an OCR-noise tolerant resume parser.

    The resume text may contain OCR mistakes.
    Your task is to infer and map skills ONLY to the closest valid names from this taxonomy.

    Allowed taxonomy skills:
    {allowed_skills}

    Rules:
    - Return ONLY exact taxonomy names
    - Fix OCR spelling mistakes
    - Use semantic inference
    - Prioritize technical skills over soft skills.
    - Infer soft skills if explicitly stated or infer them from other projects/activities.
    - No extra skills outside taxonomy

    Resume OCR Text:
    {resume_text}

    Return JSON only:
    {{
        "skills": []
    }}
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
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
        print(f"[llm_extractor] JSON parse failed: {e}\nRaw content: {content}")
        return {"skills": []}