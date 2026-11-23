import re
import urllib.parse
import requests
import streamlit as st
from groq import Groq

st.set_page_config(page_title="كابتن الجيم والعناية", page_icon="💪")

GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")
GIPHY_API_KEY = st.secrets.get("GIPHY_API_KEY", "")

if not GROQ_API_KEY:
    st.error("أضف GROQ_API_KEY في Streamlit Secrets.")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """
أنت كابتن جيم وكالستنكس وعناية شخصية محترف ومساعد.
جاوب بالعربية بشكل واضح ومنظم.
عندما تقترح أو تشرح مجموعة تمارين، اذكر كل تمرين في نقطة واضحة واكتب اسمه العربي واسمه الإنجليزي إن أمكن (مثال: 1. تمرين الضغط (Push-Up): ...).
"""

KNOWN_EXERCISES = [
    ("ضغط", "تمرين الضغط (Push-Up)", "push ups exercise form"),
    ("بوش اب", "تمرين الضغط (Push-Up)", "push ups exercise form"),
    ("push-up", "تمرين الضغط (Push-Up)", "push ups exercise form"),
    ("push up", "تمرين الضغط (Push-Up)", "push ups exercise form"),
    ("سكوات", "تمرين السكوات (Squat)", "squat exercise form"),
    ("قرفصاء", "تمرين السكوات (Squat)", "squat exercise form"),
    ("squat", "تمرين السكوات (Squat)", "squat exercise form"),
    ("عقلة", "تمرين العقلة (Pull-Up)", "pull ups exercise form"),
    ("سحب", "تمرين العقلة (Pull-Up)", "pull ups exercise form"),
    ("pull-up", "تمرين العقلة (Pull-Up)", "pull ups exercise form"),
    ("pull up", "تمرين العقلة (Pull-Up)", "pull ups exercise form"),
    ("متوازي", "تمرين المتوازي (Dips)", "dips exercise form"),
    ("dips", "تمرين المتوازي (Dips)", "dips exercise form"),
    ("بلانك", "تمرين البلانك (Plank)", "plank exercise form"),
    ("plank", "تمرين البلانك (Plank)", "plank exercise form"),
    ("بطن", "تمارين البطن (Abs)", "abs workout form"),
    ("abs", "تمارين البطن (Abs)", "abs workout form"),
    ("لانجز", "تمرين الاندفاع (Lunges)", "lunges exercise form"),
    ("اندفاع", "تمرين الاندفاع (Lunges)", "lunges exercise form"),
    ("lunges", "تمرين الاندفاع (Lunges)", "lunges exercise form"),
    ("ديدليفت", "تمرين الديدليفت (Deadlift)", "deadlift exercise form"),
    ("deadlift", "تمرين الديدليفت (Deadlift)", "deadlift exercise form"),
    ("كتف", "تمارين الكتف (Shoulder Press)", "shoulder workout form"),
    ("بايسبس", "تمرين البايسبس (Bicep Curls)", "bicep curls workout form"),
    ("ترايسبس", "تمرين الترايسبس (Triceps)", "tricep workout form"),
]

BAD_WORDS = (
    "line art",
    "stick",
    "physicalfeed",
    "sketch",
    "coloring",
    "game",
    "gameplay",
    "roblox",
    "minecraft",
    "ps1",
    "ps2",
    "low poly",
    "retro",
    "cartoon",
)


def extract_exercises_from_text(text: str, max_items: int = 4) -> list[dict]:
    lower_text = text.lower()
    found = []
    used_labels = set()

    for keyword, ar_label, en_query in KNOWN_EXERCISES:
        if keyword in lower_text and ar_label not in used_labels:
            used_labels.add(ar_label)
            found.append({"label": ar_label, "query": en_query})
            if len(found) >= max_items:
                break

    if not found:
        en_matches = re.findall(r"[a-zA-Z]{3,}(?:\s+[a-zA-Z0-9]+){0,2}", text)
        for m in en_matches:
            cleaned = re.sub(
                r"\b(3d|gif|video|image|game|workout|exercise)\b",
                "",
                m,
                flags=re.I,
            ).strip()
            if len(cleaned) >= 3:
                found.append(
                    {
                        "label": f"تمرين {cleaned.title()}",
                        "query": f"{cleaned} workout form",
                    }
                )
                break

    return found


@st.cache_data(show_spinner=False, ttl=3600)
def get_gifs_for_query(base_query: str, count: int = 3) -> list[str]:
    if not GIPHY_API_KEY:
        return []

    queries = [
        f"{base_query} 3d",
        f"{base_query} fitness tutorial",
        base_query,
    ]

    urls = []
    seen = set()

    for q in queries:
        try:
            r = requests.get(
                "https://api.giphy.com/v1/gifs/search",
                params={
                    "api_key": GIPHY_API_KEY,
                    "q": q,
                    "limit": 10,
                    "rating": "g",
                    "lang": "en",
                },
                timeout=8,
            )
            if r.status_code != 200:
                continue

            for item in r
