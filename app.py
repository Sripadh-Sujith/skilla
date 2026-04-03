import streamlit as st
from groq import Groq

# --- CONFIGURATION ---
GROQ_API_KEY = st.secrets["api_key"]

st.set_page_config(
    page_title="Skilla AI Interviewer",
    page_icon="favicon.png",
    layout="centered"
)

# --- SESSION STATE ---
if "page" not in st.session_state:
    st.session_state.page = "setup"

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "role" not in st.session_state:
    st.session_state.role = ""

if "difficulty" not in st.session_state:
    st.session_state.difficulty = "Medium"


# --- PAGE 1: SETUP ---
def show_setup_page():
    st.title("🤖 AI Interview Simulator")
    st.write("Prepare for your dream job with real-time AI feedback.")

    with st.container(border=True):
        role = st.text_input(
            "What role are you interviewing for?",
            placeholder="e.g. Software Engineer, Data Scientist"
        )

        difficulty = st.select_slider(
            "Select Interview Difficulty",
            options=["Easy", "Medium", "Hard", "Expert"]
        )

        if st.button("Start Interview", use_container_width=True):
            if not GROQ_API_KEY:
                st.error("Add your Groq API key in secrets.toml")
            elif not role:
                st.warning("Please enter a role.")
            else:
                st.session_state.role = role
                st.session_state.difficulty = difficulty
                st.session_state.page = "chat"
                st.session_state.chat_history = []

                system_prompt = f"""
You are Skilla, a professional AI interviewer.

Role: {role}
Difficulty: {difficulty}

Rules:
- Introduce yourself as Skilla
- Start immediately
- Ask questions like:
  Question 1: <question>

- After each answer:
  - Give short feedback
  - Ask next question like:
    Question 2: <question>

- Keep it natural and professional
"""

                st.session_state.chat_history.append({
                    "role": "system",
                    "content": system_prompt
                })

                generate_initial_question()
                st.rerun()


def generate_initial_question():
    client = Groq(api_key=GROQ_API_KEY)

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=st.session_state.chat_history
        )

        msg = completion.choices[0].message.content

        st.session_state.chat_history.append({
            "role": "assistant",
            "content": msg
        })

    except Exception as e:
        st.error(f"Error starting interview: {str(e)}")


# --- PAGE 2: CHAT ---
def show_chat_page():
    st.title("💼 Interviewing with Skilla")
    st.caption(f"{st.session_state.role} • {st.session_state.difficulty}")

    # Chat history
    for message in st.session_state.chat_history:
        if message["role"] != "system":
            avatar = "🤖" if message["role"] == "assistant" else "👤"
            with st.chat_message(message["role"], avatar=avatar):
                st.markdown(message["content"])

    # Input
    if prompt := st.chat_input("Your answer..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar="🤖"):
            try:
                client = Groq(api_key=GROQ_API_KEY)

                response_placeholder = st.empty()
                full_response = ""

                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=st.session_state.chat_history,
                    stream=True
                )

                for chunk in completion:
                    content = chunk.choices[0].delta.content
                    if content:
                        full_response += content
                        response_placeholder.markdown(full_response + "▌")

                response_placeholder.markdown(full_response)

                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": full_response
                })

            except Exception as e:
                st.error(f"Error: {str(e)}")

    # 🔴 EXIT BUTTON (BOTTOM)
    st.markdown("---")
    if st.button("🚪 Exit", use_container_width=False):
        st.session_state.page = "setup"
        st.session_state.chat_history = []
        st.session_state.role = ""
        st.session_state.difficulty = "Medium"
        st.rerun()


# --- ROUTER ---
if st.session_state.page == "setup":
    show_setup_page()
else:
    show_chat_page()
