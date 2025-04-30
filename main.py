import streamlit as st
import pandas as pd
from datetime import datetime
import os
import hashlib
from dotenv import load_dotenv
from pathlib import Path

# Import our custom modules
from db import GarmentDatabase
from gemini_chat import GeminiChatbot
import utils
import admin_panel

# Load environment variables
load_dotenv()

# Set up static file serving
static_dir = Path(__file__).parent / "static"
if not static_dir.exists():
    os.makedirs(static_dir / "images", exist_ok=True)

# Page configuration
st.set_page_config(
    page_title="Indian Dress Assistant",
    page_icon="🪔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Create a function to get the full URL for static files
def get_static_url(path):
    """Get the full URL for a static file."""
    return f"static/{path}"

# Initialize session state
def initialize_session_state():
    """Initialize session state variables if they don't exist."""
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "selected_category" not in st.session_state:
        st.session_state.selected_category = "All"
    if "garment_data" not in st.session_state:
        st.session_state.garment_data = None
    if "response_cache" not in st.session_state:
        st.session_state.response_cache = {}

initialize_session_state()

# Authentication function
def check_password():
    """Returns `True` if the user had the correct password."""
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets.get("admin_password", "admin123"):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Clear password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct
        return True

# Custom CSS
st.markdown("""
<style>
    .main {
        padding-top: 2rem;
    }
    .stTextInput > div > div > input {
        padding: 15px;
        font-size: 16px;
    }
    .chat-container {
        height: 500px;
        overflow-y: auto;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    .stButton > button {
        width: 100%;
        padding: 10px;
    }
    /* Custom styles for chat message product section */
    .element-container img {
        max-width: 300px;
        margin: 10px auto;
        display: block;
        border-radius: 8px;
    }
    .stMarkdown div[data-testid="stMarkdownContainer"] > p {
        margin-bottom: 1rem;
    }
    .stMarkdown div[data-testid="stMarkdownContainer"] h3 {
        margin-top: 2rem;
        color: #1f1f1f;
    }
    /* Styling for product links */
    .stMarkdown div[data-testid="stMarkdownContainer"] a {
        display: inline-block;
        padding: 8px 16px;
        background-color: #FF4B4B;
        color: white !important;
        text-decoration: none;
        border-radius: 20px;
        margin: 8px 0;
        font-weight: bold;
    }
    .stMarkdown div[data-testid="stMarkdownContainer"] a:hover {
        background-color: #FF3333;
        text-decoration: none;
    }
    /* Add to existing CSS */
    .local-image {
        max-width: 100%;
        height: auto;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize database and chatbot
@st.cache_resource
def init_database():
    return GarmentDatabase()

@st.cache_resource
def init_chatbot():
    return GeminiChatbot()

db = init_database()
chatbot = init_chatbot()

# Page Selection in Sidebar
page = st.sidebar.radio("Navigation", ["Chat Assistant", "Admin Panel"])

if page == "Chat Assistant":
    # Sidebar
    with st.sidebar:
        st.title("Indian Dress Chatbot")
        st.image("https://cdn-icons-png.flaticon.com/512/4090/4090358.png", width=100)
        
        st.subheader("Filter by Category")
        categories = ["All"] + db.get_all_categories()
        selected_category = st.selectbox("Select Category", categories, index=0)
        
        if selected_category != st.session_state.selected_category:
            st.session_state.selected_category = selected_category
            
            # Update garment data based on selected category
            if selected_category == "All":
                st.session_state.garment_data = db.get_all_garments()
            else:
                st.session_state.garment_data = db.get_garments_by_category(selected_category)
        
        # Add occasion filter
        st.subheader("Filter by Occasion")
        occasions = ["All", "Wedding", "Festival", "Casual", "Formal", "Party"]
        selected_occasion = st.selectbox("Select Occasion", occasions, index=0)
        
        if "selected_occasion" not in st.session_state or selected_occasion != st.session_state.selected_occasion:
            st.session_state.selected_occasion = selected_occasion
            
            # Update garment data based on selected occasion (if not "All")
            if selected_occasion != "All":
                if selected_category != "All":
                    # Filter by both category and occasion
                    st.session_state.garment_data = db.get_garments_by_criteria({
                        "category": selected_category,
                        "occasion": selected_occasion
                    })
                else:
                    # Filter by occasion only
                    st.session_state.garment_data = db.get_garments_by_criteria({
                        "occasion": selected_occasion
                    })
        
        st.divider()
        
        # Recent chat history in sidebar
        st.subheader("Recent Conversations")
        recent_chats = db.get_recent_chat_history(limit=5)
        
        if not recent_chats.empty:
            for _, chat in recent_chats.iterrows():
                with st.expander(f"{chat['user_message'][:30]}...", expanded=False):
                    st.write("**You:** " + chat["user_message"])
                    st.write("**Bot:** " + chat["bot_response"])
                    st.caption(f"Time: {chat['timestamp']}")
        else:
            st.write("No conversation history yet.")
            
        st.divider()
        
        # About section
        with st.expander("About", expanded=False):
            st.write("""
            This Indian Dress Chatbot uses Gemini Pro API to provide intelligent 
            responses about traditional and modern Indian garments. The app is built with Streamlit 
            and uses SQLite for data storage.
            """)

    # Main content
    st.title("🪔 Indian Dress Assistant")
    st.write("Ask me anything about traditional and modern Indian garments!")

    # Display chat history
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.chat_history:
            utils.display_chat_message(message)

    # User input
    with st.container():
        col1, col2 = st.columns([5, 1])
        
        with col1:
            # Initialize the session state for user input if not exists
            if "user_input" not in st.session_state:
                st.session_state.user_input = ""

            user_input = st.text_input(
                "Type your message here...", 
                key="user_input",
                placeholder="e.g., I'm attending an Indian wedding, what should I wear?",
                value=st.session_state.user_input
            )
        
        with col2:
            send_button = st.button("Send")

    # Process user input
    if send_button and user_input:
        # Check cache first
        cache_key = user_input.lower().strip()
        cached_response = st.session_state.response_cache.get(cache_key)
        
        if cached_response:
            # Use cached response
            user_message = utils.format_chat_message("user", user_input)
            bot_message = utils.format_chat_message("assistant", cached_response)
            st.session_state.chat_history.extend([user_message, bot_message])
        else:
            # Add user message to chat history
            user_message = utils.format_chat_message("user", user_input)
            st.session_state.chat_history.append(user_message)
            
            with st.spinner("Thinking..."):
                # Get garment suggestions from Gemini with a timeout
                suggestion_text, suggested_garments = chatbot.suggest_garment(user_input)
                
                # Extract search criteria and search database in parallel
                search_criteria = chatbot.extract_search_criteria(user_input)
                relevant_garments = db.get_garments_by_criteria(search_criteria)
                
                # Generate response
                if not relevant_garments.empty:
                    response_text = chatbot.generate_response(user_input, relevant_garments)
                else:
                    response_text = "No matching items found in our collection, but here's a suggestion...\n\n" + suggestion_text
                
                # Cache the response
                st.session_state.response_cache[cache_key] = response_text
                
                # Add bot response to chat history
                bot_message = utils.format_chat_message("assistant", response_text)
                st.session_state.chat_history.append(bot_message)
                
                # Save to database asynchronously
                import threading
                threading.Thread(target=db.save_chat_history, 
                               args=(user_input, response_text)).start()
        
        # Set flag to clear input on next rerun
        st.session_state.clear_input = True
        st.rerun()
            
    # Display garment results if category is selected
    if st.session_state.selected_category != "All" and st.session_state.garment_data is not None:
        st.subheader(f"Browsing: {st.session_state.selected_category}")
        utils.display_garment_results(st.session_state.garment_data)

else:  # Admin Panel
    if check_password():
        admin_panel.admin_page()
    
# Footer
st.divider()
st.caption("Indian Dress Assistant powered by Gemini Pro API | © 2024")

# Close database connection when app is done
def on_shutdown():
    db.close()

# Register shutdown handler
try:
    st._on_script_stop(on_shutdown)
except:
    # Fallback for older Streamlit versions
    pass




