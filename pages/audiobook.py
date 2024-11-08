import streamlit as st
import requests
from bs4 import BeautifulSoup as bs
import re

def get_mp3_links(url):
    try:
        r = requests.get(url)
        soup = bs(r.content, 'html.parser')
        mp3_links = []
        for a in soup.find_all('a', href=re.compile(r'http.*\.mp3')):
            mp3_links.append(a['href'])
        return mp3_links
    except Exception as e:
        st.error(f"An error occurred while fetching the MP3 links: {e}")
        return []

def audiobook_main():
    st.title("📚 Audiobook Downloader and Player")
    
    # Initialize session state variables if they don't exist
    if 'mp3_links' not in st.session_state:
        st.session_state.mp3_links = []
    if 'audio_data' not in st.session_state:
        st.session_state.audio_data = {}
    if 'bookname' not in st.session_state:
        st.session_state.bookname = ''
    if 'url' not in st.session_state:
        st.session_state.url = ''

    # User inputs
    url = st.text_input("Enter the URL of the audiobook page:", value=st.session_state.url)
    bookname = st.text_input("Enter the book name (optional):", value=st.session_state.bookname)
    
    fetch_button = st.button("Fetch Audiobook")
    
    if fetch_button and url:
        with st.spinner("Fetching audiobook..."):
            mp3_links = get_mp3_links(url)
            if mp3_links:
                st.session_state.mp3_links = mp3_links
                st.session_state.bookname = bookname
                st.session_state.url = url
                st.session_state.audio_data = {}  # Reset audio data
                st.success(f"Found {len(mp3_links)} MP3 file(s).")
            else:
                st.warning("No MP3 files found at the provided URL.")
    elif not url and fetch_button:
        st.error("Please enter a valid URL.")
    
    # Display audiobooks if we have links
    if st.session_state.mp3_links:
        for idx, link in enumerate(st.session_state.mp3_links, 1):
            filename = link.split('/')[-1]
            if st.session_state.bookname:
                filename = f"{st.session_state.bookname}_{filename}"
            st.write(f"### {idx}. {filename}")
            
            # Check if we already have the audio data
            if link not in st.session_state.audio_data:
                try:
                    doc = requests.get(link)
                    audio_bytes = doc.content
                    st.session_state.audio_data[link] = audio_bytes
                except Exception as e:
                    st.error(f"Failed to load {filename}: {e}")
                    continue  # Skip to the next link
            else:
                audio_bytes = st.session_state.audio_data[link]
            
            # Create download and audio player widgets
            col1, col2 = st.columns([1, 5])
            with col1:
                st.download_button(
                    label="Download",
                    data=audio_bytes,
                    file_name=filename,
                    mime='audio/mpeg',
                    key=f"download_{link}"
                )
            with col2:
                st.audio(audio_bytes, format='audio/mp3', start_time=0)  # Removed 'key' parameter

if __name__ == "__main__":
    audiobook_main()
