import streamlit as st
from dotenv import load_dotenv
import os
from langchain_groq import ChatGroq
from youtube_transcript_api import YouTubeTranscriptApi
import re
import os
import datetime
from glob import glob
import logging
from pathlib import Path
logger=logging.getLogger()
# Load environment variables from .env file
load_dotenv()

# Set wide layout first
st.set_page_config(
    page_title="Video Summarizer with Yogesh",
    page_icon="🎥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Get GROQ API Key from environment variables
GROQ_API_KEY = st.secrets["k"]["api_key"]
chat_groq = ChatGroq(
    api_key=GROQ_API_KEY,
    model="llama-3.3-70b-specdec",
    temperature=.8,
    max_tokens=7096,
    timeout=None,
    max_retries=3,
)

# Prompt for summarization
prompt = """You are a YouTube Video Summarizer tasked with providing an in-depth analysis of a video's content. Your goal is to generate a comprehensive summary that captures the main points, key arguments, and supporting details within a 750-word limit. Please thoroughly analyze the transcript text provided and offer a detailed summary, ensuring to cover all relevant aspects of the video: """
# Add these new imports at the top


def save_and_manage_files(summary_content, transcript_content):
    """Save files and maintain only last 50 entries"""
    try:
        save_dir = Path("saved_files")
        save_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save summary
        summary_path = save_dir / f"summary_{timestamp}.md"
        summary_path.write_text(summary_content, encoding='utf-8')
        
        # Save transcript
        transcript_path = save_dir / f"transcript_{timestamp}.txt"
        transcript_path.write_text(transcript_content, encoding='utf-8')
        
        # Cleanup old files
        all_files = sorted(save_dir.glob("*"), key=os.path.getctime)
        while len(all_files) > 50:
            oldest = all_files.pop(0)
            oldest.unlink()
            st.toast(f"Deleted old file: {oldest.name}", icon="🗑️")
            
        return True
        
    except Exception as e:
        st.error(f"Failed to save files: {str(e)}")
        logger.error(f"File save error: {str(e)}")
        return False

# Function to extract video ID using regex
def extract_video_id(url):
    pattern = r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/watch\?v=|youtu\.be\/)([\w-]{11})"
    match = re.search(pattern, url)
    return match.group(1) if match else None

# Function to extract transcript details from YouTube video
def extract_transcript_details(youtube_video_url):
    try:
        video_id = extract_video_id(youtube_video_url)
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=('mr','hi','en'))
        return " ".join([entry['text'] for entry in transcript_list])
    except Exception as e:
        logger.info("this is the error while fetching data from you tube",str(e))
        print("this is exception",str(e))
        
        st.info("Video Summarization is currently supported for Hindi, English, and Marathi languages only. Please provide a video URL with content in one of these languages.")
        return None

# Function to generate summary using ChatGroq
def generate_chatgroq_content(transcript_text, prompt):
    try:
        messages = [
            ("system", "You are a helpful assistant tasked with summarizing YouTube transcripts."),
            ("human", prompt + transcript_text[:7000]),
        ]
        response = chat_groq.invoke(messages)
        return response.content
    except Exception as e:
        st.error(f"Error generating summary: {e}")
        return None

# Streamlit App Interface
st.title("🎥 Video Content Summarizer with Yogesh")

# Initialize session state
if 'transcript_text' not in st.session_state:
    st.session_state.transcript_text = None

# Split layout into two columns
col1, col2 = st.columns([1, 2], gap="large")

with col1:
    with st.container(border=True):
        st.header("Input Section")
        with st.form(key="url_form"):
            youtube_link = st.text_input("YouTube Video URL (with subtitles):", placeholder="https://youtube.com/watch?v=...")
            submitted = st.form_submit_button("Analyze Video")
            
        if submitted and youtube_link:
            with st.spinner("Processing video..."):
                video_id = extract_video_id(youtube_link)
                if video_id:
                    # Store transcript in session state
                    st.session_state.transcript_text = extract_transcript_details(youtube_link)
                    # Display thumbnail in right column
                    col2.image(
                        f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
                        use_container_width=True,
                        caption="Video Thumbnail"
                    )

with col2:
    if st.session_state.transcript_text:
        with st.container():
            st.subheader("Analysis Results")
            tab1, tab2 = st.tabs(["📝 Summary", "📜 Full Transcript"])
            
            with tab1:
                summary = generate_chatgroq_content(st.session_state.transcript_text, prompt)
                if summary:
                         # Save files to directory
                    save_and_manage_files(summary, st.session_state.transcript_text)  # Add this line
                    
                    st.download_button("Download Summary", summary, file_name="video_summary.md")                    
                    st.success("Summary generated successfully!")
                    st.write(summary)

            
            with tab2:
                with st.expander("View Full Transcript", expanded=True):
                    st.write(st.session_state.transcript_text)
                    st.download_button("Download Transcript", st.session_state.transcript_text, file_name="transcript.txt")
    elif submitted:
        st.warning("Could not extract transcript. Please ensure:")
        st.markdown("- The video has subtitles enabled  \n- The language is supported (English/Hindi/Marathi)")

st.markdown("---")
st.caption("Made with ❤️ by Yogesh Mane | v1.2.1")
