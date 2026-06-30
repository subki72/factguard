"""
Groq AI Analyzer — Core analysis engine.

Sends text to Groq API (Llama-3) with a carefully crafted prompt
to evaluate objectivity, detect bias/manipulation, and identify
buzzer indicators in political narratives.

Why Groq? ADR-001: Free tier, extremely fast inference, no self-hosting cost.
"""

import json
import os

from groq import Groq

# Skor thresholds (BR6 — fixed)
LABEL_THRESHOLDS = {
    "OBJEKTIF": (70, 100),
    "CENDERUNG_BIAS": (40, 69),
    "SANGAT_MANIPULATIF": (0, 39),
}

SYSTEM_PROMPT = """Kamu adalah analis objektivitas berita politik profesional. Tugasmu menganalisis teks narasi politik dan memberikan penilaian objektivitas.

DEFINISI OBJEKTIVITAS:
Teks dianggap objektif jika menyajikan fakta yang dapat diverifikasi, tanpa opini pribadi yang tidak ditandai, tanpa framing tendensius, dan tanpa manipulasi emosional. Mirip konsep grounding pada RAG — klaim yang grounded pada sumber fakta kredibel dianggap lebih objektif.

INDIKATOR MANIPULASI YANG HARUS DIDETEKSI:
1. Framing Tendensius — memilih fakta tertentu saja
2. Clickbait / Judul Misleading
3. Logical Fallacy — strawman, ad hominem, false dilemma, dll
4. Emotional Manipulation — fear-mongering, outrage bait
5. Cherry-Picking — memilih data yang mendukung narasi saja
6. Hoax / Fabricated News — informasi yang dikarang

INDIKATOR BUZZER:
- Pola bahasa repetitif dan terkoordinasi
- Framing yang sangat satu arah tanpa nuansa
- Penggunaan hashtag atau slogan kampanye
- Serangan ad hominem terhadap pihak tertentu
- Bahasa emosional yang berlebihan

ATURAN OUTPUT:
1. Berikan skor 0-100 (100 = sangat objektif, 0 = sangat manipulatif)
2. Label: OBJEKTIF (70-100), CENDERUNG_BIAS (40-69), SANGAT_MANIPULATIF (0-39)
3. Berikan penjelasan detail MENGAPA teks mendapat skor tersebut
4. Highlight kalimat/frasa spesifik yang bermasalah (jika ada)
5. List indikator buzzer yang terdeteksi (jika ada)

RESPOND HANYA DALAM FORMAT JSON BERIKUT (tanpa markdown, tanpa backtick):
{
  "score": <integer 0-100>,
  "label": "<OBJEKTIF|CENDERUNG_BIAS|SANGAT_MANIPULATIF>",
  "reasoning": "<penjelasan detail dalam Bahasa Indonesia>",
  "highlighted_issues": ["<kalimat/frasa bermasalah 1>", "..."],
  "buzzer_indicators": ["<indikator 1>", "..."]
}"""


async def analyze_text(text: str, language: str = "id") -> dict:
    """
    Analyze text for objectivity using Groq API.

    Args:
        text: The text to analyze.
        language: Detected language ('id' or 'en').

    Returns:
        Dict with score, label, reasoning, highlighted_issues, buzzer_indicators.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY belum diset di environment variables.")

    client = Groq(api_key=api_key)

    # Adjust user prompt based on language
    lang_note = ""
    if language == "en":
        lang_note = " (Teks ini dalam Bahasa Inggris, tetapi berikan analisis dan penjelasan dalam Bahasa Indonesia.)"

    user_prompt = f"Analisis objektivitas teks berikut{lang_note}:\n\n{text}"

    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        model="llama-3.3-70b-versatile",
        temperature=0.1,  # Low temperature for consistent, deterministic analysis
        max_tokens=2048,
        response_format={"type": "json_object"},
    )

    response_text = chat_completion.choices[0].message.content

    # Parse the JSON response
    try:
        result = json.loads(response_text)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Groq mengembalikan response yang bukan JSON valid: {response_text[:200]}..."
        ) from e

    # Validate required fields
    required_fields = ["score", "label", "reasoning"]
    for field in required_fields:
        if field not in result:
            raise ValueError(f"Groq response tidak mengandung field '{field}'.")

    # Ensure score is within bounds
    result["score"] = max(0, min(100, int(result["score"])))

    # Ensure label matches score (override if Groq gave wrong label)
    for label, (low, high) in LABEL_THRESHOLDS.items():
        if low <= result["score"] <= high:
            result["label"] = label
            break

    # Ensure lists exist
    result.setdefault("highlighted_issues", [])
    result.setdefault("buzzer_indicators", [])

    return result
