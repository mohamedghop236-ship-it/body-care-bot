import re
import requests
import streamlit as st
from groq import Groq

st.set_page_config(
    page_title="كابتن الجيم والعناية",
    page_icon="💪",
    layout="centered",
)

# --- قراءة المفاتيح من Streamlit Secrets ---
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")
GIPHY_API_KEY = st.secrets.get("GIPHY_API_KEY", "")

if not GROQ_API_KEY:
    st.error("يرجى إضافة GROQ_API_KEY داخل إعدادات Secrets في Streamlit Cloud.")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """
أنت كابتن لياقة بدنية وكالستنكس وجيم وعناية شخصية محترف، ودود ومباشر.
قدم خطط تمارين عملية، وتوضيحاً واضحاً للعضلات المستهدفة ونصائح الأداء الصحيح والتغذية.
عندما يسأل المستخدم عن تمرين معين، اذكر اسم التمرين بوضوح في ردك.
أجب باللغة العربية بشكل منظم ومفيد.
"""

# --- قاموس ترجمة شائع لتحسين البحث عن GIF ثلاثي الأبعاد ---
ARABIC_TO_EN_EXERCISES = {
    "ضغط": "push ups",
    "تمرين ضغط": "push ups",
    "بوش اب": "push ups",
    "سكوات": "squat",
    "قرفصاء": "squat",
    "عقلة": "pull ups",
    "سحب": "pull ups",
    "متوازي": "dips workout",
    "بلانك": "plank exercise",
    "بطن": "abs workout",
    "كرانش": "crunches workout",
    "لانجز": "lunges workout",
    "اندفاع": "lunges workout",
    "ديدليفت": "deadlift workout",
    "كتف": "shoulder workout",
    "بايسبس": "bicep curls workout",
    "ترايسبس": "tricep workout",
    "كالستنكس": "calisthenics workout",
}

BLOCKED_KEYWORDS = (
    "line art",
    "line drawing",
    "stick figure",
    "stickman",
    "physicalfeed",
    "sketch",
    "coloring",
)


def extract_exercise_query(user_text: str, assistant_reply: str) -> str:
    combined = f"{user_text} {assistant_reply}".lower()

    for ar_term, en_term in ARABIC_TO_EN_EXERCISES.items():
        if ar_term in combined:
            return en_term

    en_matches = re.findall(r"[a-zA-Z][a-zA-Z\s\-]{2,30}", user_text)
    if en_matches:
        cleaned = re.sub(r"\b(gif|3d|video|image|صورة|تمرين|عايز|عاوز|وريني)\b", "", en_matches[0], flags=re.I).strip()
        if len(cleaned) >= 3:
            return cleaned

    cleaned_ar = re.sub(r"(عايز|عاوز|وريني|اظهرلي|شرح|تمرين|اتمرن|عن|في|بالله|لو سمحت)", " ", user_text).strip()
    return cleaned_ar[:35] if cleaned_ar else "3d fitness workout"


def fetch_exercise_gif(exercise_query: str) -> str | None:
    if not GIPHY_API_KEY:
        return None

    base_q = exercise_query.strip()
    queries = [
        f"{base_q} 3d animation workout",
        f"{base_q} 3d exercise",
        f"{base_q} 3d muscle workout",
        f"{base_q} workout animation",
    ]

    headers = {"User-Agent": "Mozilla/5.0"}

    for q in queries:
        try:
            resp = requests.get(
                "https://api.giphy.com/v1/gifs/search",
                params={
                    "api_key": GIPHY_API_KEY,
                    "q": q,
                    "limit": 10,
                    "rating": "g",
                    "lang": "en",
                },
                headers=headers,
                timeout=8,
            )
            if resp.status_code != 200:
                continue

            results = resp.json().get("data", [])
            # تفضيل النتائج التي تحتوي على كلمات 3D أو animation ولا تحتوي على رسوم خطية
            scored_results = []
            for item in results:
                title = (item.get("title") or "").lower()
                if any(bad in title for bad in BLOCKED_KEYWORDS):
                    continue

                images = item.get("images", {})
                gif_url = (
                    images.get("downsized_medium", {}).get("url")
                    or images.get("fixed_height", {}).get("url")
                    or images.get("original", {}).get("url")
                )
                if not gif_url:
                    continue

                score = 0
                if "3d" in title:
                    score += 3
                if "workout" in title or "exercise" in title:
                    score += 2
                if "animation" in title or "fitness" in title:
                    score += 1

                scored_results.append((score, gif_url))

            if scored_results:
                scored_results.sort(key=lambda x: x[0], reverse=True)
                return scored_results[0][1]

        except Exception:
            continue

    return None


# --- تهيئة سجل المحادثة لكل مستخدم ---
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("💪 كابتن الجيم والعناية")
st.caption("اسأل عن تمارين الكالستنكس والجيم والدايت، واحصل على شرح وصورة GIF ثلاثية الأبعاد للتوضيح.")

# --- أدوات مساعدة للصور والكاميرا ---
with st.expander("📷 إرفاق صورة أو التقاط صورة بالكاميرا (اختياري)"):
    uploaded_img = st.file_uploader("ارفع صورة", type=["png", "jpg", "jpeg", "webp"])
    camera_img = st.camera_input("التقط صورة")
    if uploaded_img is not None:
        st.image(uploaded_img, caption="الصورة المرفوعة", use_container_width=True)
    elif camera_img is not None:
        st.image(camera_img, caption="الصورة الملتقطة", use_container_width=True)

# --- عرض الرسائل السابقة ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("gif_url"):
            st.image(msg["gif_url"], caption="صورة GIF توضيحية لأداء التمرين (3D)", use_container_width=True)
