import os
import streamlit as st
from typing import Dict, Optional
from groq import Groq
from gtts import gTTS  # Import for text-to-speech conversion
from io import BytesIO

# Streamlit page configuration
st.set_page_config(layout="wide", page_title="Podcast Topic Generator with Audio", initial_sidebar_state="expanded")

# Supported models
SUPPORTED_MODELS: Dict[str, str] = {
    "Llama 3.2 1B (Preview)": "llama-3.2-1b-preview",
    "Llama 3 70B": "llama3-70b-8192",
    "Llama 3 8B": "llama3-8b-8192",
    "Mixtral 8x7B": "mixtral-8x7b-32768",
    "Gemma 2 9B": "gemma2-9b-it",
    "LLaVA 1.5 7B": "llava-v1.5-7b-4096-preview",
}

MAX_TOKENS: int = 1000

# Initialize Groq client with API key
@st.cache_resource
def get_groq_client() -> Optional[Groq]:
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        st.error("GROQ_API_KEY not found in environment variables. Please set it and restart the app.")
        return None
    return Groq(api_key=groq_api_key)

client = get_groq_client()

# Sidebar - Model Configuration
st.sidebar.image("p2.PNG")
st.sidebar.title("Model Configuration")
selected_model = st.sidebar.selectbox("Choose an AI Model", list(SUPPORTED_MODELS.keys()))

# Sidebar - Temperature Slider
st.sidebar.subheader("Temperature")
temperature = st.sidebar.slider("Set temperature for response variability:", min_value=0.0, max_value=1.0, value=0.7)

# Sidebar - Podcast Topic Input
st.sidebar.subheader("Podcast Topic")
podcast_topic = st.sidebar.text_area("Enter your podcast topic:")

# Option to select the expanded podcast prompt
st.sidebar.subheader("Podcast Prompt Type")
prompt_type = st.sidebar.selectbox("Choose prompt type:", ["Default", "Expanded"])

# Podcast script prompts
default_prompt = """
Generate a podcast script based on the following topic: "{topic}". The podcast should follow this structure:
1. Introduction: Briefly introduce the topic, why it's relevant.
2. Discussion Outline:
    - Explore the basics: Define the core concepts or ideas.
    - Deep dive into key points: Discuss the main challenges or exciting aspects.
    - Solutions and insights: Offer tips or solutions to address the issues.
    - Debate or agreement on challenges: Explore different viewpoints or emphasize the biggest challenges.
    - Practical takeaways: Summarize the key lessons or insights.
3. Closing Remarks: Conclude with a call to action or final thought.
"""

expanded_prompt = """
Expanded Prompt for Podcast Creation:
Topic: "{topic}"
Speaker: 1
Introduction: The speaker starts by introducing the topic, outlining the main idea, and providing a brief explanation of why it is relevant, timely, or exciting in today’s context. They may touch on recent trends, key statistics, or important developments related to the subject to spark the listener’s interest.
Discussion Outline:
1. Exploring the Basics: Define the core concepts or ideas.
2. Deep Dive into Key Points: Discuss the main challenges or exciting aspects.
3. Sharing Insights and Solutions: Offer tips or solutions to address the issues.
4. Exploring Challenges and Offering Perspectives: Explore different viewpoints or emphasize the biggest challenges.
5. Practical Takeaways: Summarize the key lessons or insights.
6. Closing Remarks: Conclude with a call to action or final thought.
"""

# Initialize session state for selected agent and agent output
if 'podcast_script' not in st.session_state:
    st.session_state.podcast_script = None
if 'audio_data' not in st.session_state:
    st.session_state.audio_data = None

# Function to get response from Groq API
def get_groq_response(prompt: str) -> str:
    try:
        response = client.chat.completions.create(
            model=SUPPORTED_MODELS[selected_model],
            messages=[
                {"role": "system", "content": "You are an AI assistant that generates podcasts."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=MAX_TOKENS
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Error: {e}")
        return ""

# Function to generate text-to-speech audio from the podcast script
def generate_audio(text: str) -> BytesIO:
    tts = gTTS(text)
    audio_buffer = BytesIO()
    tts.write_to_fp(audio_buffer)
    audio_buffer.seek(0)
    return audio_buffer

# Generate the selected podcast prompt
if prompt_type == "Expanded":
    podcast_prompt = expanded_prompt.format(topic=podcast_topic)
else:
    podcast_prompt = default_prompt.format(topic=podcast_topic)

# Submit button for generating podcast script
if st.sidebar.button("Generate Podcast Script"):
    if client:
        # Use spinner while waiting for the response
        with st.spinner("Generating podcast script..."):
            st.session_state.podcast_script = get_groq_response(podcast_prompt)
        
        # Use spinner while generating audio
        if st.session_state.podcast_script:
            with st.spinner("Generating podcast audio..."):
                st.session_state.audio_data = generate_audio(st.session_state.podcast_script)
    else:
        st.error("Groq client not initialized.")

# Main content area
st.image("p1.png")
st.title("Podcast Generator with Audio Playback")

# Display the generated podcast script
if st.session_state.podcast_script:
    st.subheader("Generated Podcast Script")
    st.write(st.session_state.podcast_script)

    # Display audio player if the audio was generated
    if st.session_state.audio_data:
        st.subheader("Audio Playback")
        st.audio(st.session_state.audio_data, format="audio/mp3")

        # Offer download link for the generated audio
        st.download_button(
            label="Download Podcast Audio",
            data=st.session_state.audio_data,
            file_name=f"{podcast_topic}_podcast.mp3",
            mime="audio/mp3"
        )
st.info("build by darryl - enter topic, wait 30 secoands for audio script in podcast style")
