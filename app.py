import streamlit as st
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Import orchestrator safely
try:
    from agents.orchestrator import orchestrate_tourism_query
    AGENTS_READY = True
except Exception as e:
    AGENTS_READY = False
    st.error(f"Agent loading failed: {e}")

# Page config
st.set_page_config(
    page_title="✈️ Inkle.ai Tourism AI Assistant",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS: Background gradient, container, chat bubbles, sidebar style
st.markdown(
    """
    <style>
    /* Page background gradient */
    .stApp {
        background: linear-gradient(135deg, #74ebd5 0%, #ACB6E5 100%);
        min-height: 100vh;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        color: #2c3e50;
    }
    /* Center container with shadow and padding */
    .app-container {
        max-width: 800px;
        margin: 3rem auto 4rem;
        background: rgba(255, 255, 255, 0.95);
        box-shadow: 0 15px 40px rgba(0,0,0,0.18);
        border-radius: 20px;
        padding: 2rem 3rem;
    }
    /* Title style */
    .app-title {
        font-weight: 900;
        font-size: 3.3rem;
        color: #34495e;
        text-align: center;
        margin-bottom: 2rem;
        letter-spacing: 2px;
    }
    /* User message bubble */
    .user-msg {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border-radius: 20px 20px 0 20px;
        padding: 1rem 1.5rem;
        margin: 0.75rem 0 0.75rem 25%;
        max-width: 70%;
        box-shadow: 0 6px 15px rgba(118, 75, 162, 0.5);
        float: right;
        clear: both;
    }
    /* AI message bubble */
    .ai-msg {
        background: linear-gradient(135deg, #f093fb, #f5576c);
        color: white;
        border-radius: 20px 20px 20px 0;
        padding: 1rem 1.5rem;
        margin: 0.75rem 25% 0.75rem 0;
        max-width: 70%;
        box-shadow: 0 6px 15px rgba(240, 83, 117, 0.5);
        float: left;
        clear: both;
    }
    /* Scrollable chat container */
    .chat-box {
        max-height: 480px;
        overflow-y: auto;
        padding-right: 1rem;
        margin-bottom: 1.5rem;
    }
    /* Sidebar style */
    [data-testid="stSidebar"] {
        background-color: rgba(44, 62, 80, 0.95);
        color: white;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    [data-testid="stSidebar"] .css-1d391kg {
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Sidebar content with system status and usage instructions
with st.sidebar:
    st.title("🛠️ System Status")
    if AGENTS_READY:
        st.success("✅ All agents loaded and ready!")
        st.markdown("### Features")
        st.markdown("- Real-time weather (Open-Meteo API)")
        st.markdown("- Global attractions (OpenStreetMap)")
        st.markdown("- AI coordination (OpenAI GPT-4o-mini)")
    else:
        st.error("❌ Agents failed to load — check logs")

    st.markdown("---")
    st.header("📝 How To Use")
    st.markdown(
        """
        • Ask for weather: *Weather in Paris*  
        • Ask for attractions: *Attractions in Tokyo*  
        • Get travel plans: *Plan my trip to London*  

        Use full city names or include country for best accuracy.
        """
    )

    st.markdown("---")
    st.markdown(
        "<div style='font-size: 0.8rem; color: #bbb; text-align: center;'>"
        "Built for Inkle.ai AI Internship &mdash; Multi-Agent Tourism System"
        "</div>",
        unsafe_allow_html=True,
    )

# Main application container centered
st.markdown('<div class="app-container">', unsafe_allow_html=True)

# Application main title
st.markdown('<div class="app-title">✈️ Inkle.ai Tourism AI Assistant</div>', unsafe_allow_html=True)

# Chat messages container with scroll
st.markdown('<div class="chat-box">', unsafe_allow_html=True)

# Display chat messages as styled bubbles
for msg in st.session_state.get("messages", []):
    bubble_class = "user-msg" if msg["role"] == "user" else "ai-msg"
    st.markdown(f'<div class="{bubble_class}">{msg["content"]}</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Initialize controlled input in session_state
if "input_text" not in st.session_state:
    st.session_state.input_text = ""

# Form with stable controlled input and no immediate clear_on_submit
with st.form("chat_form"):
    user_text = st.text_area(
        "Type your travel question here…",
        height=80,
        value=st.session_state.input_text,
        placeholder='E.g., "Weather in Paris" or "Top attractions in Tokyo"',
        key="input_area"
    )
    submitted = st.form_submit_button("Send ✈️")

if submitted and user_text.strip():
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Save input to session state for consistency
    st.session_state.input_text = user_text.strip()

    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": st.session_state.input_text})

    with st.spinner("🤖 Planning your perfect trip..."):
        try:
            res = orchestrate_tourism_query(st.session_state.input_text)
            if res.get("status") == "success":
                ai_reply = res.get("response", "Sorry, no response generated.")
            else:
                ai_reply = f"⚠️ {res.get('response', 'Unknown error')}"
        except Exception as ex:
            ai_reply = f"❌ Internal error: {ex}"

    # Append AI response
    st.session_state.messages.append({"role": "assistant", "content": ai_reply})

    # Clear input box after processing (only after AI response appended)
    st.session_state.input_text = ""

# Footer with branding text
st.markdown(
    """
    <footer style="margin-top:3rem; text-align:center; font-size:0.9rem; color:#444;">
      Inkle.ai Multi-Agent Tourism System &mdash; Powered by OpenAI GPT-4o-mini, Open-Meteo & OpenStreetMap APIs
    </footer>
    """,
    unsafe_allow_html=True
)

st.markdown('</div>', unsafe_allow_html=True)  # Close main container div
