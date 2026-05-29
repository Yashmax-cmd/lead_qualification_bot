# pyrefly: ignore [missing-import]
import os
import sys
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError
import requests
import pandas as pd
import time

# Set up page configurations
st.set_page_config(
    page_title="Sales Intel - AI CRM Assistant", 
    page_icon="💼", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===================================================
# DYNAMIC API URL CONFIGURATION (CODESPACES AWARE)
# ===================================================
# Get API_URL from multiple sources in order of priority:
# 1. Streamlit secrets
# 2. Environment variables
# 3. User input in sidebar
# 4. Default

DEFAULT_API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/analyze")
API_URL = DEFAULT_API_URL

try:
    API_URL = st.secrets.get("API_URL", DEFAULT_API_URL)
except StreamlitSecretNotFoundError:
    API_URL = DEFAULT_API_URL

# Display API configuration in sidebar
st.sidebar.markdown("### ⚙️ API Configuration")
API_URL = st.sidebar.text_input(
    "Backend API Endpoint URL",
    value=API_URL,
    help="Update this if your FastAPI backend is on a different host or port. For Codespaces, use your dynamically assigned URL."
)
st.sidebar.markdown(f"**Current API:** `{API_URL}`")

if API_URL.startswith("http://127.0.0.1") or API_URL.startswith("http://localhost"):
    st.sidebar.warning("⚠️ Using localhost. For deployment, update the API URL above.")

# Custom CSS for rich aesthetics and styling
st.markdown("""
<style>
    .reportview-container {
        background: #f8f9fa;
    }
    .metric-card {
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1rem;
        font-weight: bold;
    }
    .hot-card {
        background: linear-gradient(135deg, #ff416c, #ff4b2b);
        box-shadow: 0 4px 15px rgba(255, 75, 43, 0.3);
    }
    .warm-card {
        background: linear-gradient(135deg, #f7971e, #ffd200);
        box-shadow: 0 4px 15px rgba(247, 151, 30, 0.3);
        color: #111 !important;
    }
    .cold-card {
        background: linear-gradient(135deg, #36d1dc, #5b86e5);
        box-shadow: 0 4px 15px rgba(91, 134, 229, 0.3);
    }
    .chat-bubble {
        padding: 1rem 1.5rem;
        border-radius: 18px;
        margin-bottom: 0.8rem;
        display: inline-block;
        max-width: 80%;
    }
    .user-bubble {
        background-color: #007bff;
        color: white;
        float: right;
        border-bottom-right-radius: 2px;
    }
    .assistant-bubble {
        background-color: #f1f3f5;
        color: #212529;
        float: left;
        border-bottom-left-radius: 2px;
    }
    .clear-float {
        clear: both;
    }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# SESSION STATE INITIALIZATION
# --------------------------------------------------
if "prediction_history" not in st.session_state:
    st.session_state.prediction_history = []

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am your AI CRM Sales Intelligence Assistant. Send me a customer inquiry text and fill out the CRM parameters in the sidebar to qualify the lead."}
    ]

# --------------------------------------------------
# SIDEBAR - CRM CONFIGURATION & TABULAR INPUTS
# --------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.title("📋 CRM Lead Attributes")
st.sidebar.markdown("Provide tabular customer metrics to combine with the DistilBERT text analysis.")

total_visits = st.sidebar.slider("Total Website Visits", min_value=0, max_value=50, value=5, step=1)
time_on_website = st.sidebar.slider("Time Spent on Website (sec)", min_value=0, max_value=3600, value=600, step=10)
page_views = st.sidebar.slider("Page Views Per Visit", min_value=0.0, max_value=15.0, value=3.0, step=0.1)

source = st.sidebar.selectbox(
    "Lead Acquisition Source",
    options=['Organic Search', 'Direct Traffic', 'Google Campaigns', 'Referral Sites', 'Unknown']
)

last_activity = st.sidebar.selectbox(
    "Last CRM Activity",
    options=['Email Opened', 'SMS Sent', 'Page Visited on Website', 'Email Bounced', 'Unknown']
)

occupation = st.sidebar.selectbox(
    "Lead Occupation Status",
    options=['Working Professional', 'Student', 'Unemployed', 'Businessman', 'Unknown']
)

# --------------------------------------------------
# MAIN PAGE LAYOUT
# --------------------------------------------------
st.title("💼 AI Sales Intelligence CRM Assistant")
st.markdown("Contextual NLP Lead Qualification Classifier powered by fine-tuned DistilBERT and MLOps.")

tab1, tab2 = st.tabs(["💬 AI Assistant", "📊 CRM Analytics & History"])

# Tab 1: Chatbot Conversational Interface
with tab1:
    # Display conversation messages
    for msg in st.session_state.messages:
        role = msg["role"]
        bubble_cls = "user-bubble" if role == "user" else "assistant-bubble"
        st.markdown(f"""
        <div class="chat-bubble {bubble_cls}">
            {msg["content"]}
        </div>
        <div class="clear-float"></div>
        """, unsafe_allow_html=True)
        
        # If there's structured prediction data attached, display it beautifully
        if "structured_data" in msg:
            data = msg["structured_data"]
            col1, col2 = st.columns([1, 2])
            
            with col1:
                # Prediction Colored Card
                card_class = "cold-card"
                if data["prediction"] == "Hot Lead":
                    card_class = "hot-card"
                elif data["prediction"] == "Warm Lead":
                    card_class = "warm-card"
                
                st.markdown(f"""
                <div class="metric-card {card_class}">
                    <h3 style="margin: 0; color: inherit;">{data["prediction"]}</h3>
                    <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; color: inherit;">Confidence: {data["confidence"]}</p>
                </div>
                """, unsafe_allow_html=True)
                
                st.metric("Intent Classification", data["intent"])
                st.metric("Urgency Priority Scale", data["urgency"])
                
            with col2:
                st.markdown("#### 🔍 Explainable AI (XAI) Reasonings:")
                for r in data["reason"]:
                    st.markdown(f"- {r}")
            st.markdown("---")

    # User chat input box
    user_input = st.chat_input("Enter customer inquiry text (e.g. 'We need demo and pricing urgently')...")
    
    if user_input:
        # Append user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Post request to FastAPI backend
        payload = {
            "customer_response": user_input,
            "total_visits": float(total_visits),
            "time_on_website": float(time_on_website),
            "page_views": float(page_views),
            "source": source,
            "last_activity": last_activity,
            "occupation": occupation
        }
        
        # Simulate typing animation
        with st.spinner("Analyzing intent and tabular CRM metrics..."):
            try:
                response = requests.post(API_URL, json=payload, timeout=30)
                if response.status_code == 200:
                    result = response.json()
                    
                    # Store structured result in session history
                    history_entry = {
                        "timestamp": time.strftime("%H:%M:%S"),
                        "inquiry": user_input,
                        "visits": total_visits,
                        "time_on_site": time_on_website,
                        "occupation": occupation,
                        "prediction": result["prediction"],
                        "confidence": result["confidence"],
                        "intent": result["intent"],
                        "urgency": result["urgency"]
                    }
                    st.session_state.prediction_history.append(history_entry)
                    
                    # Append assistant conversational response and attach structured results
                    assistant_msg = f"I have analyzed this lead. It classifies as a **{result['prediction']}**."
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": assistant_msg,
                        "structured_data": result
                    })
                    
                else:
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": f"⚠️ Error from API backend: Status {response.status_code}\n\n```\n{response.text}\n```"
                    })
            except requests.exceptions.ConnectionError as e:
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": f"❌ Failed to connect to backend API at `{API_URL}`.\n\n**Troubleshooting:**\n- Check API URL in the sidebar\n- Ensure FastAPI backend is running\n- For Codespaces: Update API URL with your dynamic URL\n\n**Error:** {str(e)}"
                })
            except requests.exceptions.Timeout:
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": "⏱️ Request timeout. Backend API took too long to respond. Please try again."
                })
            except Exception as e:
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": f"⚠️ An unexpected error occurred:\n\n```\n{str(e)}\n```"
                })
        
        # Rerun to update chat bubbles view
        st.rerun()

# Tab 2: Prediction logs and charts dashboard
with tab2:
    if not st.session_state.prediction_history:
        st.info("📌 No leads classified in this session yet. Interact with the Chatbot in the first tab to build analytics.")
    else:
        df_history = pd.DataFrame(st.session_state.prediction_history)
        
        # Dashboard metrics row
        st.subheader("📈 Lead Analytics Overview")
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            st.metric("Total Leads Processed", len(df_history))
        with col_m2:
            hot_count = len(df_history[df_history["prediction"] == "Hot Lead"])
            st.metric("Hot Leads 🔥", hot_count)
        with col_m3:
            conversion_rate = f"{(hot_count / len(df_history)) * 100:.1f}%"
            st.metric("Potential Conversion Rate", conversion_rate)
        with col_m4:
            # Numeric conversion of confidence strings (e.g. "95.6%") for average
            conf_vals = df_history["confidence"].str.replace("%", "").astype(float)
            st.metric("Avg Classifier Confidence", f"{conf_vals.mean():.1f}%")
            
        st.markdown("---")
        
        # Charts Row
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.subheader("Lead Classification Distribution")
            class_counts = df_history["prediction"].value_counts()
            st.bar_chart(class_counts)
            
        with col_c2:
            st.subheader("Intent Category Segmentation")
            intent_counts = df_history["intent"].value_counts()
            st.bar_chart(intent_counts)
            
        st.markdown("---")
        
        # Logs Table
        st.subheader("📋 Prediction Log History")
        st.dataframe(
            df_history[["timestamp", "inquiry", "visits", "time_on_site", "occupation", "prediction", "confidence", "intent", "urgency"]], 
            use_container_width=True
        )
