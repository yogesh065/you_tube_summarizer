import streamlit as st
from dotenv import load_dotenv
import os
from langchain_groq import ChatGroq
from youtube_transcript_api import YouTubeTranscriptApi
import re 
# Load environment variables from .env file
load_dotenv()

# Get GROQ API Key from environment variables
GROQ_API_KEY = st.secrets["k"]["api_key"]
chat_groq = ChatGroq(
    api_key=GROQ_API_KEY,
    model="llama-3.3-70b-specdec",
    temperature=0,
    max_tokens=7096,
    timeout=None,
    max_retries=3,
)

# Prompt for summarization
prompt = """You are a YouTube Video Summarizer tasked with providing an in-depth analysis of a video's content. Your goal is to generate a comprehensive summary that captures the main points, key arguments, and supporting details within a 750-word limit. Please thoroughly analyze the transcript text provided and offer a detailed summary, ensuring to cover all relevant aspects of the video: """

# Function to extract transcript details from YouTube video
def extract_transcript_details(youtube_video_url):
    try:
        video_id = youtube_video_url.split("=")[1]
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id,languages=("en","hi","mr"))
        
        transcript = " ".join([entry['text'] for entry in transcript_list])
        st.write("Transcript extracted successfully!\n\n", transcript)
        return transcript
        
    except Exception as e:
        st.error(f"Error extracting transcript: {e}")
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
st.title("YouTube Transcript to Detailed Notes Converter")
youtube_link = st.text_input("Enter the YouTube Video URL:")
def extract_video_id(url):
    pattern = r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/watch\?v=|youtu\.be\/)([\w-]{11})"
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None
# Display thumbnail image if URL is provided
if youtube_link:
    video_id = extract_video_id(youtube_link)

    if video_id:
        thumbnail_url = f"https://img.youtube.com/vi/{video_id}/0.jpg"
        st.image(thumbnail_url, use_column_width=True, caption="YouTube Thumbnail")


if st.button("Get Detailed Notes"):
    try:
        transcript_text = extract_transcript_details(youtube_link)
        
        if transcript_text:
            summary = generate_chatgroq_content(transcript_text, prompt)
            if summary:
                st.markdown("## Detailed Notes:")
                st.write(summary)
    except Exception as e :
        st.write("please provide correct you tube link")

st.markdown("---")
st.write("Made By Yogesh Mane!")
