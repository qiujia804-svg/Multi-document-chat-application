import streamlit as st

def get_custom_css(theme: str) -> str:
    """Get custom CSS styles based on theme"""
    if theme == "light":
        return """
        <style>
        /* Main theme colors */
        .stApp {
            background-color: #FFFFFF;
        }
        
        /* Chat message styles */
        .chat-message {
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
            display: flex;
            flex-direction: column;
        }
        
        .user-message {
            background-color: #E3F2FD;
        }
        
        .assistant-message {
            background-color: #F5F5F5;
        }
        
        /* Sidebar styles */
        .css-1d391kg {
            background-color: #FAFAFA;
        }
        
        /* File upload area */
        .uploadedFile {
            background-color: #E8F5E9;
            border: 2px dashed #4CAF50;
        }
        
        /* Progress bar */
        .stProgress > div > div > div > div {
            background-color: #4CAF50;
        }
        
        /* Buttons */
        .stButton > button {
            color: white;
            background-color: #2196F3;
            border-radius: 4px;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            background-color: #1976D2;
            transform: translateY(-2px);
        }
        
        /* Expander */
        .streamlit-expanderHeader {
            background-color: #F5F5F5;
            border-radius: 4px;
        }
        
        /* Status indicators */
        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 5px;
        }
        
        .status-success {
            background-color: #4CAF50;
        }
        
        .status-error {
            background-color: #F44336;
        }
        
        /* Document processing progress */
        .progress-container {
            margin: 1rem 0;
        }
        
        /* Chat container */
        .chat-container {
            height: 500px;
            overflow-y: auto;
            padding: 1rem;
            background-color: #FAFAFA;
            border-radius: 0.5rem;
            margin: 1rem 0;
        }
        
        /* Message metadata */
        .message-metadata {
            font-size: 0.8rem;
            color: #666;
            margin-top: 0.5rem;
        }
        </style>
        """
    else:  # Dark theme
        return """
        <style>
        /* Main theme colors */
        .stApp {
            background-color: #1E1E1E;
        }
        
        /* Chat message styles */
        .chat-message {
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
            display: flex;
            flex-direction: column;
        }
        
        .user-message {
            background-color: #2D2D30;
        }
        
        .assistant-message {
            background-color: #252526;
        }
        
        /* Sidebar styles */
        .css-1d391kg {
            background-color: #252526;
        }
        
        /* File upload area */
        .uploadedFile {
            background-color: #2D2D30;
            border: 2px dashed #007ACC;
        }
        
        /* Progress bar */
        .stProgress > div > div > div > div {
            background-color: #007ACC;
        }
        
        /* Buttons */
        .stButton > button {
            color: white;
            background-color: #007ACC;
            border-radius: 4px;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            background-color: #005a9e;
            transform: translateY(-2px);
        }
        
        /* Expander */
        .streamlit-expanderHeader {
            background-color: #2D2D30;
            border-radius: 4px;
        }
        
        /* Status indicators */
        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 5px;
        }
        
        .status-success {
            background-color: #4CAF50;
        }
        
        .status-error {
            background-color: #F44336;
        }
        
        /* Document processing progress */
        .progress-container {
            margin: 1rem 0;
        }
        
        /* Chat container */
        .chat-container {
            height: 500px;
            overflow-y: auto;
            padding: 1rem;
            background-color: #1E1E1E;
            border-radius: 0.5rem;
            margin: 1rem 0;
        }
        
        /* Message metadata */
        .message-metadata {
            font-size: 0.8rem;
            color: #999;
            margin-top: 0.5rem;
        }
        </style>
        """

def apply_custom_styles(theme: str = "light"):
    """Apply custom styles to streamlit app"""
    st.markdown(get_custom_css(theme), unsafe_allow_html=True)

def render_status_indicator(status: bool, text: str):
    """Render a status indicator with text"""
    status_class = "status-success" if status else "status-error"
    st.markdown(
        f"""
        <div>
            <span class="status-indicator {status_class}"></span>
            {text}
        </div>
        """,
        unsafe_allow_html=True
    )

def render_chat_message(role: str, content: str, metadata: dict = None):
    """Render a chat message with optional metadata"""
    message_class = f"chat-message {'user-message' if role == 'user' else 'assistant-message'}"
    
    with st.container():
        st.markdown(
            f"""
            <div class="{message_class}">
                <div class="message-content">{content}</div>
                {f'<div class="message-metadata">{metadata}</div>' if metadata else ''}
            </div>
            """,
            unsafe_allow_html=True
        )

def render_progress_bar(label: str, progress: float):
    """Render a custom progress bar"""
    st.markdown(
        f"""
        <div class="progress-container">
            <p>{label}</p>
            <div class="stProgress">
                <div style="width: {progress}%"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )