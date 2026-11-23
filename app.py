import streamlit as st
from groq import Groq

st.set_page_config(page_title="كابتن الجيم والعناية", page_icon="💪")

GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")
if not GROQ_API_KEY:
    st.error("يرجى إضافة GROQ_API_KEY داخل إعدادات Secrets في Streamlit Cloud.")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """
أنت كابتن لياقة بدنية وكالستنكس وجيم وعناية شخصية محترف، ودود ومباشر.
قدم خطط تمارين عملية، وتوضيحاً واضحاً للعضلات المستهدفة ونصائح الأداء الصحيح والتغذية والعناية الشخصية.
أجب باللغة العربية بشكل منظم وسهل التطبيق.
"""

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

prompt = st.chat_input("...اكتب تمرينك أو سؤالك هنا")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    api_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + [
        {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
    ]

    with st.chat_message("assistant"):
        try:
            res = client.chat.completions.create(
                model="qwen/qwen3.8-27b",
                max_tokens=700,
                messages=api_messages,
            )
            reply = res.choices[0].message.content or ""
        except Exception as e:
            st.error(f"حدث خطأ أثناء الاتصال بالخادم: {e}")
            st.stop()

        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
