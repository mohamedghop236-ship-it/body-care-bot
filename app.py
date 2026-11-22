import os, json, streamlit as st
from groq import Groq

st.set_page_config(page_title="كابتن الجيم والعناية", page_icon="💪")
st.title("💪 كابتن الجيم والعناية")

api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    st.error("اضبط GROQ_API_KEY أولاً في التيرمنال.")
    st.stop()

client = Groq(api_key=api_key)
log_file = "gym_log.json"
system_msg = {"role": "system", "content": "أنت كابتن جيم ولياقة وعناية شخصية عملي ومشجع باللغة العربية. تابع تقدم المستخدم وقدم خطط تمارين وتغذية وعناية واضحة ومختصرة."}

if "messages" not in st.session_state:
    if os.path.exists(log_file):
        loaded = json.load(open(log_file, encoding="utf-8"))
        st.session_state.messages = [m for m in loaded if m.get("role") != "system"]
    else:
        st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

prompt = st.chat_input("اكتب تمرينك أو سؤالك هنا...")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    api_msgs = [system_msg] + st.session_state.messages[-12:]
    res = client.chat.completions.create(model="qwen/qwen3.8-27b", max_tokens=700, messages=api_msgs)
    reply = res.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": reply})
    with st.chat_message("assistant"):
        st.markdown(reply)
    json.dump([system_msg] + st.session_state.messages, open(log_file, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
