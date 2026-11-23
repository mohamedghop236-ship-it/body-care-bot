import base64
import os
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

# قاموس صور GIF لتمارين شائعة (يمكنك إضافة أو تعديل الروابط حسب رغبتك)
EXERCISE_GIFS = {
    "ضغط": "https://media.giphy.com/media/7Yeze6y8B6q3e/giphy.gif",
    "push": "https://media.giphy.com/media/7Yeze6y8B6q3e/giphy.gif",
    "سكوات": "https://media.giphy.com/media/1qfK1oq6X8a2U/giphy.gif",
    "squat": "https://media.giphy.com/media/1qfK1oq6X8a2U/giphy.gif",
    "بلانك": "https://media.giphy.com/media/3o7TKV58in42Y5T2mY/giphy.gif",
    "plank": "https://media.giphy.com/media/3o7TKV58in42Y5T2mY/giphy.gif",
    "عقلة": "https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif",
    "pull": "https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif",
    "معدة": "https://media.giphy.com/media/26AHONQ79FdWZhI0o/giphy.gif",
    "abs": "https://media.giphy.com/media/26AHONQ79FdWZhI0o/giphy.gif",
}


def find_exercise_gif(text: str):
    lowered = text.lower()
    for key, url in EXERCISE_GIFS.items():
        if key in lowered:
            return url
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
            st.image(m["gif_url"], caption="طريقة أداء التمرين", use_container_width=True)

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
    gif_url = find_exercise_gif(reply + " " + prompt)

    st.session_state.messages.append(
        {"role": "assistant", "content": reply, "gif_url": gif_url}
    )
    with st.chat_message("assistant"):
        st.markdown(reply)
        if gif_url:
            st.image(gif_url, caption="طريقة أداء التمرين", use_container_width=True)
