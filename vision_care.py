import os, sys, json
from groq import Groq
sys.stdout.reconfigure(encoding="utf-8")

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
log_file = "gym_log.json"
history = json.load(open(log_file, encoding="utf-8")) if os.path.exists(log_file) else [{"role": "system", "content": "أنت كابتن جيم ولياقة عملي وداعم باللغة العربية. اسأل أسئلة مركزة، تابع تقدم المستخدم بناءً على السجل السابق، وقدّم خطط تمارين وتغذية واضحة ومختصرة."}]

while True:
    user_msg = input("\nأنت (اكتب خروج للإنهاء): ").strip()
    if not user_msg or user_msg.lower() in ["exit", "quit", "خروج"]:
        break
    history.append({"role": "user", "content": user_msg})
    res = client.chat.completions.create(model="qwen/qwen3.8-27b", max_tokens=700, messages=history[-12:])
    reply = res.choices[0].message.content
    print("\nالكابتن:\n" + reply)
    history.append({"role": "assistant", "content": reply})
    json.dump(history, open(log_file, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
