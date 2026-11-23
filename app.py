import base64
import json
import os
import urllib.parse
import urllib.request
import streamlit as st
from groq import Groq

st.set_page_config(page_title="كابتن الجيم والعناية", page_icon="💪")
st.title("💪 كابتن الجيم والعناية")

api_key = None
try:
    if "GROQ_API_KEY" in st.secrets:
        api_key = st.secrets["GROQ_API_KEY"]
except Exception:
    pass

if not api_key:
    api_key = os.environ.get("GROQ_API_KEY")

if not api_key:
    st.error("اضبط GROQ_API_KEY أولاً في Secrets أو التيرمنال.")
    st.stop()

client = Groq(api_key=api_key)

giphy_key = None
try:
    if "GIPHY_API_KEY" in st.secrets:
        giphy_key = st.secrets["GIPHY_API_KEY"]
except Exception:
    pass

if not giphy_key:
    giphy_key = os.environ.get("GIPHY_API_KEY")


def fetch_exercise_gif(query_text: str):
    lowered = query_text.lower()

    exercise_queries = {
        "ضغط": "push up exercise gif",
        "push": "push up exercise gif",
        "سكوات": "squat exercise gif",
        "squat": "squat exercise gif",
        "بلانك": "plank exercise gif",
        "plank": "plank exercise gif",
        "عقلة": "pull up exercise gif",
        "pull": "pull up exercise gif",
        "معدة": "ab crunch exercise gif",
        "abs": "ab crunch exercise gif",
        "باي": "bicep curl exercise gif",
        "تراي": "tricep dip exercise gif",
        "كتف": "shoulder press exercise gif",
        "رجل": "leg workout exercise gif",
    }

    search_query = None
    for ar_or_en, q in exercise_queries.items():
        if ar_or_en in lowered:
            search_query = q
            break

    if not search_query:
        return None

    if giphy_key:
        encoded = urllib.parse.quote(search_query)
        url = f"https://api.giphy.com/v1/gifs/search?api_key={giphy_key}&q={encoded}&limit=3&rating=g"
        try:
            with urllib.request.urlopen(url, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                items = data.get("data", [])
                for item in items:
                    gif_url = item.get("images", {}).get("original", {}).get("url")
                    if gif_url:
                        return gif_url
        except Exception:
            pass

    return None


system_msg = {
    "role": "system",
    "content": (
        "أنت كابتن جيم ولياقة وعناية شخصية عملي ومشجع باللغة العربية. "
        "تابع تقدم المستخدم وقدم خطط تمارين وتغذية وعناية واضحة ومختصرة. "
        "عند شرح تمرين، اذكر اسمه بوضوح ووضح خطوات الأداء الصحيحة باختصار."
    ),
}

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m.get("gif_url"):
            try:
                st.image(m["gif_url"], caption="صورة GIF متحركة لأداء التمرين", use_container_width=True)
            except Exception:
                pass

photo = st.camera_input("التقط صورة بالكاميرا")
uploaded_img = st.file_uploader("أو ارفع صورة من جهازك", type=["jpg", "jpeg", "png"])
selected_image = photo or uploaded_img

if selected_image is not None:
    st.image(selected_image, caption="الصورة المختارة", use_container_width=True)

prompt = st.chat_input("اكتب تمرينك أو سؤالك هنا...")
if prompt:
    user_text = prompt
    if selected_image is not None:
        img_bytes = selected_image.getvalue()
        img_b64 = base64.b64encode(img_bytes).decode("utf-8")
        mime_type = selected_image.type or "image/jpeg"
        user_content = [
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{img_b64}"},
            },
        ]
    else:
        user_content = prompt

    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    api_msgs = [system_msg] + [
        {"role": msg["role"], "content": msg["content"]}
        for msg in st.session_state.messages[-12:]
    ]
    if selected_image is not None:
        api_msgs[-1] = {"role": "user", "content": user_content}

    res = client.chat.completions.create(
        model="qwen/qwen3.8-27b",
        max_tokens=700,
        messages=api_msgs,
    )
    reply = res.choices[0].message.content
    gif_url = fetch_exercise_gif(prompt + " " + reply)

    st.session_state.messages.append(
        {"role": "assistant", "content": reply, "gif_url": gif_url}
    )
    with st.chat_message("assistant"):
        st.markdown(reply)
        if gif_url:
            try:
                st.image(gif_url, caption="صورة GIF متحركة لأداء التمرين", use_container_width=True)
            except Exception:
                pass
