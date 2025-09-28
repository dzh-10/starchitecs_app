import streamlit as st
import json
import os
from PIL import Image
from openai import OpenAI

# --- إعداد Perplexity API ---
API_KEY = "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"
client = OpenAI(api_key=API_KEY, base_url="https://api.perplexity.ai")

def generate_with_perplexity(prompt: str) -> str:
    try:
        response = client.chat.completions.create(
            model="sonar",
            messages=[{"role": "user", "content": prompt}]
        )
        # تحويل النص للـ UTF-8 مع استبدال أي حروف غير قابلة للترميز
        text = response.choices[0].message.content
        if text:
            return text.encode('utf-8', errors='replace').decode('utf-8')
        else:
            return "⚠️ لم أتمكن من توليد شرح."
    except Exception as e:
        return f"❌ خطأ أثناء الاتصال بـ Perplexity: {e}"


# --- إعداد الصفحة ---
st.set_page_config(page_title="Starchitecs 🌟 AI", layout="wide")
st.markdown("<h1 style='text-align: center; color: #4B8BBE;'>📘 Starchitecs 🌟 AI</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #306998;'>منصة تعليمية بالذكاء الاصطناعي</h3>", unsafe_allow_html=True)
st.markdown("---")

# --- الطور والسنة والمادة ---
levels = {"الابتدائي": ["1","2","3","4","5"], "المتوسط": ["1","2","3","4"], "الثانوي": ["1","2","3"]}
subject_map = {
    "اللغة العربية": "arabic",
    "الرياضيات": "math",
    "التربية الإسلامية": "islamic",
    "التربية العلمية والتكنولوجية": "science"
}

level = st.sidebar.selectbox("اختر الطور:", list(levels.keys()))
year = st.sidebar.selectbox("اختر السنة:", levels[level])
subject_ar = st.sidebar.selectbox("اختر المادة:", list(subject_map.keys()))
subject = subject_map[subject_ar]

# --- اسم الطالب ---
student_name = st.sidebar.text_input("أدخل اسمك:", "")

# --- مسار حفظ النقاط ---
scores_file = "scores.json"

# --- دوال حفظ و تحميل النقاط ---
def load_scores():
    if os.path.exists(scores_file):
        with open(scores_file, "r", encoding="utf-8-sig") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_scores(scores):
    with open(scores_file, "w", encoding="utf-8") as f:
        json.dump(scores, f, ensure_ascii=False, indent=2)

# --- session_state ---
if "exercises" not in st.session_state: st.session_state.exercises = []
if "current_index" not in st.session_state: st.session_state.current_index = 0
if "answer" not in st.session_state: st.session_state.answer = None
if "checked" not in st.session_state: st.session_state.checked = False
if "extra_explanation" not in st.session_state: st.session_state.extra_explanation = ""
if "scores" not in st.session_state: st.session_state.scores = load_scores()

# --- تحميل التمارين ---
if st.sidebar.button("📂 تحميل التمارين"):
    file_path = os.path.join("data", "primary" if level=="الابتدائي" else "other", f"year{year}", f"{subject}.json")
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8-sig") as f:
                st.session_state.exercises = json.load(f)
            st.session_state.current_index = 0
            st.session_state.checked = False
            st.success(f"✅ تم تحميل {len(st.session_state.exercises)} تمرين لمادة {subject_ar}")
        except Exception as e:
            st.error(f"⚠️ خطأ أثناء قراءة الملف: {e}")
    else:
        st.error("🚫 الملف غير موجود!")

# --- دالة تحديث النقاط ---
def update_score(student, correct):
    if student:
        if student not in st.session_state.scores:
            st.session_state.scores[student] = 0
        if correct:
            st.session_state.scores[student] += 10
        save_scores(st.session_state.scores)

# --- عرض التمرين الحالي ---
if st.session_state.exercises and student_name:
    ex = st.session_state.exercises[st.session_state.current_index]
    st.markdown(f"### ✏️ السؤال {st.session_state.current_index + 1}: {ex['question']}")

    if ex.get("image"):
        image_path = os.path.join("data", "primary" if level=="الابتدائي" else "other", f"year{year}", ex["image"])
        if os.path.exists(image_path):
            img = Image.open(image_path)
            st.image(img, caption="الصورة التوضيحية", use_column_width=True)

    options = ["-- اختر الإجابة --"] + ex["options"]
    choice = st.radio("اختر الإجابة:", options, index=0)
    st.session_state.answer = choice if choice != "-- اختر الإجابة --" else None

    btn_cols = st.columns(2)
    if btn_cols[0].button("✅ تصحيح"):
        st.session_state.checked = True
        correct = st.session_state.answer == ex["answer"]
        update_score(student_name, correct)
    if btn_cols[1].button("➡️ التمرين التالي"):
        st.session_state.current_index += 1
        st.session_state.checked = False
        st.session_state.answer = None
        st.session_state.extra_explanation = ""
        if st.session_state.current_index >= len(st.session_state.exercises):
            st.session_state.current_index = 0
            st.success("🎉 انتهت جميع التمارين. سيتم إعادة البداية.")

    if st.session_state.checked and st.session_state.answer:
        if st.session_state.answer == ex["answer"]:
            st.success("🎉 إجابة صحيحة!")
        else:
            st.error(f"❌ إجابة خاطئة! الجواب الصحيح: {ex['answer']}")
        st.info("📖 الشرح: " + ex["explanation"])

        if st.button("🤖 طلب شرح إضافي من Perplexity"):
            prompt = f"اشرح هذا الدرس بالعربية:\nالسؤال: {ex['question']}\nالجواب الصحيح: {ex['answer']}\nالشرح الأصلي: {ex['explanation']}"
            st.session_state.extra_explanation = generate_with_perplexity(prompt)

        if st.session_state.extra_explanation:
            st.success("📘 شرح إضافي (من AI):")
            st.write(st.session_state.extra_explanation)

# --- عرض لوحة الشرف ---
if st.session_state.scores:
    st.markdown("---")
    st.markdown("## 🏆 لوحة الشرف")
    leaderboard = sorted(st.session_state.scores.items(), key=lambda x: x[1], reverse=True)
    for rank, (student, score) in enumerate(leaderboard, start=1):
        st.write(f"{rank}. {student}: {score} نقطة")
