import streamlit as st
from groq import Groq
import time

# --- CONFIGURATION ---
# Replace the empty string below with your actual Groq API Key
GROQ_API_KEY = st.secrets["api_key"] 

# Set page config to hide default sidebar navigation
st.set_page_config(
    page_title="Skilla AI Interviewer",
    page_icon="favicon.png",
    initial_sidebar_state="expanded",
    layout="centered"
)

# --- INITIALIZATION & SESSION STATE ---
if "page" not in st.session_state:
    st.session_state.page = "setup"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "role" not in st.session_state:
    st.session_state.role = ""
if "difficulty" not in st.session_state:
    st.session_state.difficulty = "Medium"

# --- THEME MANAGEMENT (FIXED DARK MODE) ---
# Enforcing a dark theme via custom CSS
theme_css = """
    <style>
        /* Hide multipage nav */
        [data-testid="stSidebarNav"] {
            display: none;
        }
        
        /* Permanent Dark Theme Application */
        .stApp {
            background-color: #0e1117;
            color: #ffffff;
        }
        
        .stChatMessage {
            border-radius: 10px;
            background-color: #1e2128;
            margin-bottom: 10px;
            color: #ffffff;
        }
        
        /* Ensuring sidebar matches theme */
        [data-testid="stSidebar"] {
            background-color: #161b22;
        }

        /* Fix input colors for dark mode */
        div[data-baseweb="input"] > div {
            background-color: #262730 !important;
            color: white !important;
        }
        
        /* Button styling */
        .stButton>button {
            border-radius: 8px;
            background-color: #262730;
            color: white;
            border: 1px solid #4a4a4a;
        }
        
        .stButton>button:hover {
            border-color: #ff4b4b;
            color: #ff4b4b;
        }
    </style>
"""
st.markdown(theme_css, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Settings")
    st.caption("Theme: Dark Mode (Fixed)")
    
    st.divider()
    
    if st.session_state.page == "chat":
        st.info(f"Interviewer: **Skilla**\n\nTarget Role: **{st.session_state.role}**")
        if st.button("🚪 Exit Interview", use_container_width=True):
            st.session_state.page = "setup"
            st.session_state.chat_history = []
            st.rerun()

# --- PAGE 1: SETUP ---
def show_setup_page():
    st.title("🤖 AI Interview Simulator")
    st.write("Prepare for your dream job with real-time AI feedback.")
    
    with st.container(border=True):
        role = st.text_input("What role are you interviewing for?", placeholder="e.g. Software Engineer, Data Scientist")
        difficulty = st.select_slider("Select Interview Difficulty", options=["Easy", "Medium", "Hard", "Expert"])
        
        if st.button("Start Interview", use_container_width=True):
            if not GROQ_API_KEY:
                st.error("Please add your Groq API Key to the 'GROQ_API_KEY' variable in the code.")
            elif not role:
                st.warning("Please enter a target role.")
            else:
                st.session_state.role = role
                st.session_state.difficulty = difficulty
                st.session_state.page = "chat"
                
                # Initial System Message defining "Skilla"
                system_prompt = (
                    f"Your name is Skilla. You are a professional, polite, yet rigorous technical interviewer. "
                    f"Conduct a {difficulty} level interview for the role of {role}. "
                    f"You must start the interview immediately by introducing yourself as Skilla and "
                    f"asking the first relevant technical or behavioral question. Do not wait for the user to speak first."
                )
                
                st.session_state.chat_history.append({"role": "system", "content": system_prompt})
                
                # Trigger the first AI response automatically
                generate_initial_question()
                st.rerun()

def generate_initial_question():
    """Helper to get the first question from Skilla without user input."""
    client = Groq(api_key=GROQ_API_KEY)
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=st.session_state.chat_history,
            stream=False
        )
        first_msg = completion.choices[0].message.content
        st.session_state.chat_history.append({"role": "assistant", "content": first_msg})
    except Exception as e:
        st.error(f"Error starting interview: {str(e)}")

# --- PAGE 2: CHAT INTERFACE ---
def show_chat_page():
    st.title(f"💼 Interviewing with Skilla")
    st.caption(f"Role: {st.session_state.role} | Level: {st.session_state.difficulty}")

    # Display Chat History
    for message in st.session_state.chat_history:
        if message["role"] != "system":
            avatar = "🤖" if message["role"] == "assistant" else "👤"
            with st.chat_message(message["role"], avatar=avatar):
                st.markdown(message["content"])

    # Chat Input
    if prompt := st.chat_input("Your answer..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        # Generate AI Response
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
                st.session_state.chat_history.append({"role": "assistant", "content": full_response})
            
            except Exception as e:
                st.error(f"Error connecting to Groq: {str(e)}")

# --- ROUTER ---
if st.session_state.page == "setup":
    show_setup_page()
else:
    show_chat_page()