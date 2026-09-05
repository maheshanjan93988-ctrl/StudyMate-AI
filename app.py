import streamlit as st
import requests
import json
import re
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO


# =========================================================
# PAGE SETTINGS
# =========================================================

st.set_page_config(
    page_title="StudyMate AI",
    page_icon="📚",
    layout="centered"
)


# =========================================================
# LOGIN PAGE
# =========================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:

    st.markdown(
        """
        <style>
        .login-title {
            text-align: center;
            color: #6366f1;
            font-size: 38px;
            font-weight: bold;
            margin-top: 80px;
        }

        .login-subtitle {
            text-align: center;
            color: #777;
            font-size: 18px;
            margin-bottom: 30px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="login-title">📚 StudyMate AI</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="login-subtitle">Your personal AI learning assistant</div>',
        unsafe_allow_html=True
    )

    st.subheader("🔐 Student Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login", use_container_width=True):

        if username.strip() == "student" and password == "1234":
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Invalid username or password")

    # Stop here so the main interface does not appear
    st.stop()


# =========================================================
# CUSTOM UI
# =========================================================

st.markdown(
    """
    <style>
    .main {
        background-color: #f5f7ff;
    }

    .stButton > button {
        background-color: #4f46e5;
        color: white;
        border-radius: 10px;
        border: none;
        padding: 10px 18px;
        font-weight: bold;
    }

    .stButton > button:hover {
        background-color: #3730a3;
        color: white;
    }

    .app-title {
        color: #4f46e5;
        font-size: 38px;
        font-weight: bold;
        text-align: center;
    }

    .app-subtitle {
        text-align: center;
        color: #555;
        font-size: 18px;
        margin-bottom: 25px;
    }

    .info-card {
        padding: 18px;
        border-radius: 15px;
        background-color: #e0e7ff;
        margin-bottom: 15px;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="app-title">📚 StudyMate AI</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="app-subtitle">Learn smarter with your personal AI assistant</div>',
    unsafe_allow_html=True
)


# =========================================================
# SESSION STATE
# =========================================================

default_values = {
    "chat_history": [],
    "explanation": "",
    "quiz_data": [],
    "quiz_submitted": False,
    "quiz_score": 0,
    "plan": "",
    "editing_message": None
}

for key, value in default_values.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header("⚙️ Settings")

    language = st.selectbox(
        "Choose language",
        ["English", "Telugu"]
    )

    level = st.selectbox(
        "Choose learning level",
        ["Beginner", "Intermediate", "Advanced"]
    )

    st.divider()

    st.write("### 👤 Account")
    st.write("Logged in as: **student**")

    if st.button("Logout", key="logout_button"):
        st.session_state.logged_in = False
        st.rerun()

    st.divider()

    if st.button("🗑️ Clear Chat", key="sidebar_clear_chat"):
        st.session_state.chat_history = []
        st.session_state.editing_message = None
        st.rerun()


# =========================================================
# GEMINI AI CONNECTION
# =========================================================

GEMINI_MODEL = "gemini-3.5-flash-lite"


def ask_ai(prompt):
    try:
        api_key = st.secrets["GEMINI_API_KEY"]

        url = (
            "https://generativelanguage.googleapis.com/v1beta/"
            f"models/{GEMINI_MODEL}:generateContent"
        )

        response = requests.post(
            url,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": api_key
            },
            json={
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 2048
                }
            },
            timeout=120
        )

        response.raise_for_status()

        result = response.json()

        return (
            result["candidates"][0]["content"]["parts"][0]["text"]
        ).strip()

    except Exception as error:
        raise Exception(f"Gemini API request failed: {error}")

# =========================================================
# PDF FUNCTION
# =========================================================

def create_pdf(title, content):

    pdf_file = BytesIO()

    pdf = canvas.Canvas(pdf_file, pagesize=A4)
    width, height = A4

    y = height - 50

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, y, title)

    y -= 35
    pdf.setFont("Helvetica", 11)

    for line in content.split("\n"):

        if y < 50:
            pdf.showPage()
            pdf.setFont("Helvetica", 11)
            y = height - 50

        pdf.drawString(50, y, line[:100])
        y -= 16

    pdf.save()
    pdf_file.seek(0)

    return pdf_file


# =========================================================
# USER INPUTS
# =========================================================

topic = st.text_input(
    "📌 Enter a topic you want to learn",
    placeholder="Example: Python loops"
)

st.markdown(
    '<div class="info-card">Choose a topic and use the tabs to learn, practice, and ask questions.</div>',
    unsafe_allow_html=True
)


# =========================================================
# FEATURE TABS
# =========================================================

tab1, tab2, tab3, tab4 = st.tabs(
    ["📖 Explain", "📝 Quiz", "📅 Study Plan", "💬 Ask AI"]
)


# =========================================================
# LANGUAGE INSTRUCTION
# =========================================================

if language == "Telugu":

    language_instruction = """
Answer completely in Telugu.
Use simple Telugu words.
Keep important programming keywords in English.
"""

else:

    language_instruction = """
Answer completely in English.
Use simple and clear language.
"""


# =========================================================
# EXPLANATION TAB
# =========================================================

with tab1:

    if st.button("📖 Explain Topic", key="explain_button"):

        if not topic.strip():
            st.warning("Please enter a topic first.")

        else:

            with st.spinner("Preparing your explanation..."):

                try:

                    explanation = ask_ai(
                        f"""
You are StudyMate AI.

Topic: {topic}
Student level: {level}

{language_instruction}

Explain the topic using:

1. Definition
2. Main concepts
3. Simple example
4. Important points
5. Short summary

Use headings and bullet points.
"""
                    )

                    st.session_state.explanation = explanation

                except Exception as error:

                    st.error("The AI request failed.")
                    st.code(str(error))

    if st.session_state.explanation:

        st.markdown(st.session_state.explanation)

        st.download_button(
            label="⬇️ Download Explanation",
            data=st.session_state.explanation,
            file_name="explanation.txt",
            mime="text/plain",
            key="download_explanation"
        )

        pdf = create_pdf(
            f"StudyMate AI - {topic}",
            st.session_state.explanation
        )

        st.download_button(
            label="📄 Download Explanation PDF",
            data=pdf,
            file_name="explanation.pdf",
            mime="application/pdf",
            key="download_explanation_pdf"
        )


# =========================================================
# QUIZ TAB
# =========================================================

with tab2:

    number_of_questions = st.slider(
        "Number of questions",
        min_value=3,
        max_value=10,
        value=5
    )

    if st.button("📝 Generate Quiz", key="quiz_button"):

        if not topic.strip():
            st.warning("Please enter a topic first.")

        else:

            with st.spinner("Generating quiz..."):

                try:

                    quiz_prompt = f"""
Create a multiple-choice quiz about "{topic}".

Student level: {level}

{language_instruction}

Create exactly {number_of_questions} questions.

Return ONLY valid JSON in this format:

[
  {{
    "question": "Question text",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "answer": 0,
    "explanation": "Short explanation"
  }}
]

The answer must be the option number:
0 for A
1 for B
2 for C
3 for D
"""

                    quiz_response = ask_ai(quiz_prompt)

                    # Remove Markdown code fences if Gemini adds them
                    quiz_response = quiz_response.replace(
                        "```json", ""
                    ).replace("```", "").strip()

                    # Extract JSON array if extra text is returned
                    match = re.search(
                        r"\[.*\]",
                        quiz_response,
                        re.DOTALL
                    )

                    if match:
                        quiz_response = match.group(0)

                    quiz_data = json.loads(quiz_response)

                    if not isinstance(quiz_data, list):
                        raise Exception("Quiz response is not a JSON list.")

                    for question_data in quiz_data:

                        if not all(
                            key in question_data
                            for key in [
                                "question",
                                "options",
                                "answer",
                                "explanation"
                            ]
                        ):
                            raise Exception(
                                "Quiz response has an invalid format."
                            )

                        if len(question_data["options"]) != 4:
                            raise Exception(
                                "Each question must have four options."
                            )

                        if question_data["answer"] not in [0, 1, 2, 3]:
                            raise Exception(
                                "Quiz answer must be 0, 1, 2, or 3."
                            )

                    st.session_state.quiz_data = quiz_data
                    st.session_state.quiz_submitted = False
                    st.session_state.quiz_score = 0

                except Exception as error:

                    st.error("Quiz generation failed.")
                    st.code(str(error))

    if st.session_state.quiz_data:

        st.subheader("📝 Answer the questions")

        selected_answers = []

        for index, question_data in enumerate(
            st.session_state.quiz_data
        ):

            st.write(
                f"**{index + 1}. {question_data['question']}**"
            )

            selected = st.radio(
                "Choose an answer:",
                question_data["options"],
                key=f"quiz_question_{index}"
            )

            selected_index = question_data["options"].index(selected)

            selected_answers.append(selected_index)

        if st.button("✅ Submit Quiz", key="submit_quiz"):

            score = 0

            for index, question_data in enumerate(
                st.session_state.quiz_data
            ):

                if selected_answers[index] == question_data["answer"]:
                    score += 1

            st.session_state.quiz_score = score
            st.session_state.quiz_submitted = True
            st.rerun()

        if st.session_state.quiz_submitted:

            total = len(st.session_state.quiz_data)
            score = st.session_state.quiz_score
            percentage = (score / total) * 100

            st.success(
                f"Your score: {score}/{total} "
                f"({percentage:.1f}%)"
            )

            for index, question_data in enumerate(
                st.session_state.quiz_data
            ):

                correct_index = question_data["answer"]
                correct_option = question_data["options"][correct_index]

                st.write(
                    f"**Question {index + 1} correct answer:** "
                    f"{correct_option}"
                )

                st.caption(question_data["explanation"])


# =========================================================
# STUDY PLAN TAB
# =========================================================

with tab3:

    study_days = st.slider(
        "How many days do you want to study?",
        min_value=1,
        max_value=14,
        value=7
    )

    if st.button("📅 Create Study Plan", key="plan_button"):

        if not topic.strip():
            st.warning("Please enter a topic first.")

        else:

            with st.spinner("Creating your study plan..."):

                try:

                    plan = ask_ai(
                        f"""
Create a {study_days}-day study plan for learning
"{topic}" at the {level} level.

{language_instruction}

For every day include:

- Topic to study
- What to practice
- Approximate study time
- A small task or goal

Keep the plan realistic for a college student.
"""
                    )

                    st.session_state.plan = plan

                except Exception as error:

                    st.error("The study-plan request failed.")
                    st.code(str(error))

    if st.session_state.plan:

        st.markdown(st.session_state.plan)

        st.download_button(
            label="⬇️ Download Study Plan",
            data=st.session_state.plan,
            file_name="study_plan.txt",
            mime="text/plain",
            key="download_plan"
        )


# =========================================================
# ASK AI TAB
# =========================================================

with tab4:

    st.info(
        "Use the chatbox at the bottom to ask follow-up questions."
    )

    st.write(
        "You can ask questions in English or Telugu depending on your selected language."
    )


# =========================================================
# CHAT HISTORY
# =========================================================

st.divider()
st.subheader("💬 Continue learning")

for index, message in enumerate(
    st.session_state.chat_history
):

    with st.chat_message(message["role"]):

        st.markdown(message["content"])

        if message["role"] == "assistant":

            st.download_button(
                label="⬇️ Save Answer",
                data=message["content"],
                file_name=f"answer_{index + 1}.txt",
                mime="text/plain",
                key=f"save_answer_{index}"
            )

        elif message["role"] == "user":

            if st.button(
                "✏️ Edit Question",
                key=f"edit_question_{index}"
            ):

                st.session_state.editing_message = index
                st.rerun()


# =========================================================
# EDIT PREVIOUS QUESTION
# =========================================================

if st.session_state.editing_message is not None:

    edit_index = st.session_state.editing_message

    old_question = st.session_state.chat_history[edit_index].get(
        "question",
        st.session_state.chat_history[edit_index]["content"]
    )

    st.subheader("✏️ Edit your question")

    edited_question = st.text_area(
        "Correct your question here:",
        value=old_question,
        key="edited_question_text"
    )

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "Send Edited Question",
            key="send_edited_question"
        ):

            if not edited_question.strip():

                st.warning("Please enter a question.")

            else:

                # Remove the old question and later messages
                st.session_state.chat_history = (
                    st.session_state.chat_history[:edit_index]
                )

                st.session_state.chat_history.append(
                    {
                        "role": "user",
                        "content": edited_question,
                        "question": edited_question
                    }
                )

                st.session_state.editing_message = None

                with st.spinner("Thinking..."):

                    try:

                        conversation_text = ""

                        for message in st.session_state.chat_history:

                            conversation_text += (
                                f'{message["role"].capitalize()}: '
                                f'{message["content"]}\n'
                            )

                        answer = ask_ai(
                            f"""
You are StudyMate AI.

Topic: {topic}
Student level: {level}

{language_instruction}

Previous conversation:
{conversation_text}

Latest question:
{edited_question}

Answer clearly and simply.
Use examples when useful.
"""
                        )

                        st.session_state.chat_history.append(
                            {
                                "role": "assistant",
                                "content": answer,
                                "question": edited_question
                            }
                        )

                        st.rerun()

                    except Exception as error:

                        st.error("The AI request failed.")
                        st.code(str(error))

    with col2:

        if st.button("Cancel Edit", key="cancel_edit"):

            st.session_state.editing_message = None
            st.rerun()


# =========================================================
# CHAT INPUT
# =========================================================

user_message = st.chat_input(
    "Ask a follow-up question..."
)

if user_message:

    if not topic.strip():

        st.warning("Please enter a topic first.")

    else:

        st.session_state.chat_history.append(
            {
                "role": "user",
                "content": user_message,
                "question": user_message
            }
        )

        conversation_text = ""

        for message in st.session_state.chat_history:

            conversation_text += (
                f'{message["role"].capitalize()}: '
                f'{message["content"]}\n'
            )

        with st.spinner("Thinking..."):

            try:

                answer = ask_ai(
                    f"""
You are StudyMate AI, a helpful personal learning assistant.

Current topic: {topic}
Student level: {level}

{language_instruction}

Previous conversation:
{conversation_text}

Latest student question:
{user_message}

Answer the latest question clearly and simply.
Connect the answer with the previous conversation.
Use examples when useful.
"""
                )

                st.session_state.chat_history.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "question": user_message
                    }
                )

                st.rerun()

            except Exception as error:

                st.error("The AI request failed.")
                st.code(str(error))