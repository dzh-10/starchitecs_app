import streamlit as st
import json
import os
from PIL import Image
import google.generativeai as genai

# --- إعداد API ---
genai.configure(api_key="AIzaSyB1Ko0z1li-AeF541r_TrOA7jEHWrIVwVM")

def generate_with_gemini(prompt: str) -> str:
    try:
        model = genai.GenerativeModel("gemini-1.5-flash-latest")
        response = model.generate_content(prompt)
        return response.text if response and response.text else "⚠️ لم أتمكن من توليد شرح."
    except Exception as e:
        return f"❌ خطأ أثناء الاتصال بـ Gemini: {e}"

# --- إعداد الصفحة ---
st.set_page_config(page_title="“Starchitecs”. 🌟 AI", layout="wide")
st.markdown("<h1 style='text-align: center; color: #4B8BBE;'>📘 “Starchitecs”. 🌟 AI</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #306998;'>منصة تعليمية بالذكاء الاصطناعي</h3>", unsafe_allow_html=True)
st.markdown("---")

# --- إعدادات الطور والسنة والمادة ---
levels = {"الابتدائي": ["1", "2", "3", "4", "5"], "المتوسط": ["1", "2", "3", "4"], "الثانوي": ["1", "2", "3"]}
subject_map = {
    "اللغة العربية": "arabic",
    "الرياضيات": "math",
    "التربية الإسلامية": "islamic",
    "التربية العلمية والتكنولوجية": "science",
    "التربية المدنية": "civics",
    "التربية الفنية": "art",
    "اللغة الفرنسية": "french",
    "اللغة الإنجليزية": "english",
    "التاريخ والجغرافيا": "history_geo"
}

level = st.sidebar.selectbox("اختر الطور:", list(levels.keys()))
year = st.sidebar.selectbox("اختر السنة:", levels[level])
subject_ar = st.sidebar.selectbox("اختر المادة:", list(subject_map.keys()))
subject = subject_map[subject_ar]

# --- تهيئة session_state ---
if "exercises" not in st.session_state:
    st.session_state.exercises = []
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "answer" not in st.session_state:
    st.session_state.answer = None
if "checked" not in st.session_state:
    st.session_state.checked = False
if "extra_explanation" not in st.session_state:
    st.session_state.extra_explanation = ""

# --- تحميل التمارين ---
if st.sidebar.button("📂 تحميل التمارين"):
    file_path = os.path.join(
        "data",
        "primary" if level == "الابتدائي" else "other",
        f"year{year}",
        f"{subject}.json"
    )
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                st.session_state.exercises = json.load(f)
            st.session_state.current_index = 0
            st.session_state.checked = False
            st.success(f"✅ تم تحميل {len(st.session_state.exercises)} تمرين لمادة {subject_ar}")
        except Exception as e:
            st.error(f"⚠️ خطأ أثناء قراءة الملف: {e}")
    else:
        st.error("🚫 الملف غير موجود!")

# --- عرض التمرين الحالي ---
if st.session_state.exercises:
    ex = st.session_state.exercises[st.session_state.current_index]

    st.markdown(f"### ✏️ السؤال {st.session_state.current_index + 1}: {ex['question']}")

    # عرض الصورة إذا موجودة
    if ex.get("image"):
        image_path = os.path.join(
            "data",
            "primary" if level == "الابتدائي" else "other",
            f"year{year}",
            ex["image"]
        )
        if os.path.exists(image_path):
            try:
                img = Image.open(image_path)
                st.image(img, caption="الصورة التوضيحية", use_column_width=True)
            except:
                st.warning("⚠️ تعذر عرض الصورة.")

    # خيارات الإجابة
    options = ["-- اختر الإجابة --"] + ex["options"]
    choice = st.radio("اختر الإجابة:", options, index=0)
    st.session_state.answer = choice if choice != "-- اختر الإجابة --" else None

    # أزرار التصحيح والتمرين التالي
    btn_cols = st.columns(2)
    if btn_cols[0].button("✅ تصحيح"):
        st.session_state.checked = True
    if btn_cols[1].button("➡️ التمرين التالي"):
        st.session_state.current_index += 1
        st.session_state.checked = False
        st.session_state.answer = None
        st.session_state.extra_explanation = ""
        if st.session_state.current_index >= len(st.session_state.exercises):
            st.session_state.current_index = 0
            st.success("🎉 انتهت جميع التمارين. سيتم إعادة البداية.")

    # عرض النتيجة والشرح
    if st.session_state.checked and st.session_state.answer:
        if st.session_state.answer == ex["answer"]:
            st.success("🎉 إجابة صحيحة!")
        else:
            st.error(f"❌ إجابة خاطئة! الجواب الصحيح: {ex['answer']}")

        st.info("📖 الشرح: " + ex["explanation"])

        # أزرار لطلب شرح إضافي بالذكاء الاصطناعي
        st.markdown("#### 🤖AI؟ هل تريد شرحًا آخر من")
        col1, col2 = st.columns(2)
        if col1.button("🔁 إعادة شرح أبسط"):
            prompt = f"اشرح هذا الدرس بشكل مبسط وسهل للأطفال:\nالسؤال: {ex['question']}\nالجواب الصحيح: {ex['answer']}\nالشرح الأصلي: {ex['explanation']}"
            st.session_state.extra_explanation = generate_with_gemini(prompt)

        if col2.button("📚 شرح معمق أكثر"):
            prompt = f"اشرح هذا الدرس بتفاصيل معمقة ومستوى متقدم:\nالسؤال: {ex['question']}\nالجواب الصحيح: {ex['answer']}\nالشرح الأصلي: {ex['explanation']}"
            st.session_state.extra_explanation = generate_with_gemini(prompt)

        # عرض الشرح الإضافي إذا وُجد
        if st.session_state.extra_explanation:
            st.success("📘 شرح إضافي (من Gemini):")
            st.write(st.session_state.extra_explanation)

    # تحميل PDF إذا موجود
    if ex.get("pdf"):
        pdf_path = os.path.join(
            "data",
            "primary" if level == "الابتدائي" else "other",
            f"year{year}",
            ex["pdf"]
        )
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as pdf_file:
                st.download_button(
                    label="📄 تحميل PDF للتمرين",
                    data=pdf_file,
                    file_name=os.path.basename(pdf_path),
                    mime="application/pdf"
                )
