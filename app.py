import re
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
جاوب بالعربية بشكل واضح ومفيد، واذكر اسم التمرين بوضوح عند شرح أي تمرين.
"""

EXERCISE_MAP = {
    "ضغط": "push ups exercise form",
    "بوش اب": "push ups exercise form",
    "سكوات": "squat exercise form",
    "قرفصاء": "squat exercise form",
    "عقلة": "pull ups exercise form",
    "متوازي": "dips exercise form",
    "بلانك": "plank exercise form",
    "بطن": "abs workout form",
    "لانجز": "lunges exercise form",
    "كالستنكس": "calisthenics workout form",
}

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


def get_exercise_gif(text: str):
    if not GIPHY_API_KEY:
        return None

    lower_text = text.lower()
    base_query = None

    for ar_word, en_query in EXERCISE_MAP.items():
        if ar_word in lower_text:
            base_query = en_query
            break

    if not base_query:
        en_part = re.findall(r"[a-zA-Z]{3,}(?:\s+[a-zA-Z0-9]+){0,3}", text)
        if en_part:
            clean_en = re.sub(r"\b(3d|gif|video|image|game)\b", "", en_part[0], flags=re.I).strip()
            if len(clean_en) >= 3:
                base_query = f"{clean_en} workout form"

    if not base_query:
        return None

    queries = [
        f"{base_query} 3d muscle",
        f"{base_query} fitness tutorial",
        base_query,
    ]

    for q in queries:
        try:
            r = requests.get(
                "https://api.giphy.com/v1/gifs/search",
                params={
                    "api_key": GIPHY_API_KEY,
                    "q": q,
                    "limit": 12,
                    "rating": "g",
                    "lang": "en",
                },
                timeout=8,
            )
            if r.status_code != 200:
                continue

            best_url = None
            best_score = -1

            for item in r.json().get("data", []):
                title = (item.get("title") or "").lower()
                if any(b in title for b in BAD_WORDS):
                    continue

                imgs = item.get("images", {})
                orig = imgs.get("original", {})
                url = orig.get("url") or imgs.get("downsized_large", {}).get("url")
                if not url:
                    continue

                try:
                    w = int(orig.get("width") or 0)
                    h = int(orig.get("height") or 0)
                except ValueError:
                    w, h = 0, 0

                # تجنب الصور الصغيرة جداً أو الضيقة للغاية
                if w < 250 or h < 180:
                    continue

                score = 0
                if w >= 400:
                    score += 2
                if any(k in title for k in ("workout", "exercise", "gym", "muscle", "fitness", "form")):
                    score += 3
                if "3d" in title:
                    score += 2

                if score > best_score:
                    best_score = score
                    best_url = url

            if best_url:
                return best_url
        except Exception:
            continue

    return None


if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("💪 كابتن الجيم والعناية")

with st.expander("📷 الكاميرا ورفع الصور", expanded=False):
    uploaded = st.file_uploader("ارفع صورة", type=["png", "jpg", "jpeg", "webp"])
    cam = st.camera_input("التقط صورة")
    if uploaded:
        st.image(uploaded, use_container_width=True)
    elif cam:
        st.image(cam, use_container_width=True)

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m.get("gif"):
            st.image(m["gif"], caption="توضيح أداء التمرين", width=420)

prompt = st.chat_input("...اكتب تمرينك أو سؤالك هنا")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    msgs = [{"role": "system", "content": SYSTEM_PROMPT}] + [
        {"role": x["role"], "content": x["content"]} for x in st.session_state.messages
    ]

    with st.chat_message("assistant"):
        try:
            resp = client.chat.completions.create(
                model="qwen/qwen3.8-27b",
                max_tokens=700,
                messages=msgs,
            )
            reply = resp.choices[0].message.content or ""
        except Exception as e:
            st.error(f"خطأ: {e}")
            st.stop()

        st.markdown(reply)
        gif_url = get_exercise_gif(f"{prompt} {reply}")
        if gif_url:
            st.image(gif_url, caption="توضيح أداء التمرين", width=420)

    st.session_state.messages.append({"role": "assistant", "content": reply, "gif": gif_url})
