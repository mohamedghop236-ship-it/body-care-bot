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
    "ضغط": "push ups 3d workout",
    "بوش اب": "push ups 3d workout",
    "سكوات": "squat 3d workout",
    "قرفصاء": "squat 3d workout",
    "عقلة": "pull ups 3d workout",
    "متوازي": "dips 3d workout",
    "بلانك": "plank 3d workout",
    "بطن": "abs 3d workout",
    "لانجز": "lunges 3d workout",
    "كالستنكس": "calisthenics 3d workout",
}

BAD_WORDS = ("line art", "stick", "physicalfeed", "sketch", "coloring")


def get_3d_gif(text: str):
    if not GIPHY_API_KEY:
        return None

    lower_text = text.lower()
    query = None

    for ar_word, en_query in EXERCISE_MAP.items():
        if ar_word in lower_text:
            query = en_query
            break

    if not query:
        en_part = re.findall(r"[a-zA-Z]{3,}(?:\s+[a-zA-Z0-9]+){0,3}", text)
        if en_part:
            query = f"{en_part[0]} 3d workout"

    if not query:
        return None

    try:
        r = requests.get(
            "https://api.giphy.com/v1/gifs/search",
            params={
                "api_key": GIPHY_API_KEY,
                "q": query,
                "limit": 8,
                "rating": "g",
                "lang": "en",
            },
            timeout=8,
        )
        if r.status_code != 200:
            return None

        for item in r.json().get("data", []):
            title = (item.get("title") or "").lower()
            if any(b in title for b in BAD_WORDS):
                continue
            imgs = item.get("images", {})
            url = (
                imgs.get("downsized_medium", {}).get("url")
                or imgs.get("fixed_height", {}).get("url")
                or imgs.get("original", {}).get("url")
            )
            if url:
                return url
    except Exception:
        return None

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
            st.image(m["gif"], caption="GIF 3D", use_container_width=True)

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
        gif_url = get_3d_gif(f"{prompt} {reply}")
        if gif_url:
            st.image(gif_url, caption="GIF 3D", use_container_width=True)

    st.session_state.messages.append({"role": "assistant", "content": reply, "gif": gif_url})
