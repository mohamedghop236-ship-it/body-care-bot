import re
import requests
import streamlit as st
from groq import Groq

st.set_page_config(page_title="كابتن الجيم والعناية", page_icon="💪")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])
GIPHY_KEY = st.secrets.get("GIPHY_API_KEY", "")

EXERCISES = [
    ("ضغط", "تمرين الضغط (Push-Up)", "push ups workout"),
    ("سكوات", "تمرين السكوات (Squat)", "squat workout"),
    ("عقلة", "تمرين العقلة (Pull-Up)", "pull ups workout"),
    ("متوازي", "تمرين المتوازي (Dips)", "dips workout"),
    ("بلانك", "تمرين البلانك (Plank)", "plank workout"),
    ("بطن", "تمارين البطن (Abs)", "abs workout"),
]

@st.cache_data(ttl=3600)
def fetch_gif(q):
    if not GIPHY_KEY:
        return None
    try:
        r = requests.get("https://api.giphy.com/v1/gifs/search", params={"api_key": GIPHY_KEY, "q": q, "limit": 5, "rating": "g"}, timeout=6)
        for item in r.json().get("data", []):
            title = (item.get("title") or "").lower()
            if any(w in title for w in ("stick", "line art", "physicalfeed", "game", "roblox", "minecraft")):
                continue
            url = item.get("images", {}).get("original", {}).get("url")
            if url:
                return url
    except Exception:
        pass
    return None

def show_exercises(txt):
    low = txt.lower()
    shown = 0
    for key, label, query in EXERCISES:
        if key in low:
            st.markdown(f"**{label}**")
            g = fetch_gif(query)
            if g:
                st.image(g, width=380)
            shown += 1
            if shown >= 4:
                break

if "msgs" not in st.session_state:
    st.session_state.msgs = []

st.title("💪 كابتن الجيم والعناية")

with st.expander("📷 الكاميرا ورفع الصور", expanded=False):
    up = st.file_uploader("ارفع صورة", type=["png", "jpg", "jpeg", "webp"])
    cam = st.camera_input("التقط صورة")
    if up:
        st.image(up, use_container_width=True)
    elif cam:
        st.image(cam, use_container_width=True)

for m in st.session_state.msgs:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            show_exercises(m["content"])

prompt = st.chat_input("...اكتب تمرينك أو سؤالك هنا")
if prompt:
    st.session_state.msgs.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    api_msgs = [{"role": "system", "content": "أنت كابتن جيم وكالستنكس وعناية شخصية محترف. جاوب بالعربية واذكر أسماء التمارين بوضوح."}] + st.session_state.msgs
    with st.chat_message("assistant"):
        res = client.chat.completions.create(model="qwen/qwen3.8-27b", max_tokens=700, messages=api_msgs)
        reply = res.choices[0].message.content or ""
        st.markdown(reply)
        show_exercises(f"{prompt} {reply}")

    st.session_state.msgs.append({"role": "assistant", "content": reply})
