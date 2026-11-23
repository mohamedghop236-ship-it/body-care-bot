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
جاوب بالعربية بشكل واضح ومرتب، واذكر أسماء التمارين بوضوح عند اقتراح أو شرح أي تمرين.
"""

# كل عنصر: (كلمات البحث في النص، اسم التمرين الواضح، استعلام بحث دقيق، كلمات مستبعدة إضافية)
EXERCISE_CATALOG = [
    (
        ("ضغط", "بوش اب", "push up", "push-up"),
        "تمرين الضغط (Push-Up)",
        "push up workout form",
    ),
    (
        ("سكوات", "قرفصاء", "squat"),
        "تمرين السكوات (Squat)",
        "bodyweight squat exercise form",
    ),
    (
        ("عقلة", "سحب", "pull up", "pull-up"),
        "تمرين العقلة (Pull-Up)",
        "pull up exercise workout",
    ),
    (
        ("متوازي", "dips"),
        "تمرين المتوازي (Dips)",
        "tricep dips exercise workout",
    ),
    (
        ("بلانك", "plank"),
        "تمرين البلانك (Plank)",
        "plank core exercise form",
    ),
    (
        ("بطن", "كرانش", "abs", "crunch"),
        "تمارين البطن (Abs)",
        "abs workout exercise",
    ),
    (
        ("لانجز", "اندفاع", "lunge"),
        "تمرين الاندفاع (Lunges)",
        "lunges leg exercise form",
    ),
]

BLOCKED_TERMS = (
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
    "anime",
    "meme",
)


@st.cache_data(show_spinner=False, ttl=3600)
def find_clean_gif(query: str) -> str | None:
    if not GIPHY_API_KEY:
        return None

    try:
        resp = requests.get(
            "https://api.giphy.com/v1/gifs/search",
            params={
                "api_key": GIPHY_API_KEY,
                "q": query,
                "limit": 15,
                "rating": "g",
                "lang": "en",
            },
            timeout=8,
        )
        if resp.status_code != 200:
            return None

        best_url = None
        best_score = -10

        for item in resp.json().get("data", []):
            title = (item.get("title") or "").lower()
            if any(bad in title for bad in BLOCKED_TERMS):
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

            if w < 240 or h < 160:
                continue

            score = 0
            if w >= 400:
                score += 2
            if any(word in title for word in ("workout", "exercise", "gym", "fitness", "form")):
                score += 3
            if "push" in query and "push" in title:
                score += 2
            if "squat" in query and "squat" in title:
                score += 2
            if "pull" in query and "pull" in title:
                score += 2
            if "plank" in query and "plank" in title:
                score += 2
            if "dip" in query and "dip" in title:
                score += 2

            if score > best_score:
                best_score = score
                best_url = url

        return best_url
    except Exception:
        return None


def display_exercises_for_message(text: str):
    lower_txt = text.lower()
    matched = []

    for triggers, title_label, search_q in EXERCISE_CATALOG:
        if any(t in lower_txt for t in triggers):
            matched.append((title_label, search_q))
        if len(matched) >= 4:
            break

    if not matched:
        return

    st.markdown("---")
    st.markdown("### 🏋️ التمارين المقترحة وطريقة أدائها")

    for idx, (title_label, search_q) in enumerate(matched, start=1):
        st.markdown(f"**{idx}. {title_label}**")
        gif_url = find_clean_gif(search_q)
        if gif_url:
            st.image(gif_url, caption=f"طريقة أداء {title_label}", width=400)
        else:
            st.caption("لم تتوفر صورة واضحة لهذا التمرين حالياً.")


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
        if m["role"] == "assistant":
            display_exercises_for_message(m["content"])

prompt = st.chat_input("...اكتب تمرينك أو سؤالك هنا")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    api_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + [
        {"role": x["role"], "content": x["content"]} for x in st.session_state.messages
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
            st.error(f"حدث خطأ: {e}")
            st.stop()

        st.markdown(reply)
        display_exercises_for_message(f"{prompt}\n{reply}")

    st.session_state.messages.append({"role": "assistant", "content": reply})
