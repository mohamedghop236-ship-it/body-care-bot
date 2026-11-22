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

system_msg = {
    "role": "system",
    "content": (
        "أنت كابتن جيم ولياقة وعناية شخصية عملي ومشجع باللغة العربية. "
        "تابع تقدم المستخدم وقدم خطط تمارين وتغذية وعناية واضحة ومختصرة."
    ),
}

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

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

    api_msgs = [system_msg] + st.session_state.messages[-12:]
    if selected_image is not None:
        api_msgs[-1] = {"role": "user", "content": user_content}

    res = client.chat.completions.create(
        model="qwen/qwen3.8-27b",
        max_tokens=700,
        messages=api_msgs,
    )
    reply = res.choices[0].message.content

    st.session_state.messages.append({"role": "assistant", "content": reply})
    with st.chat_message("assistant"):
        st.markdown(reply)
