import os
import requests
import streamlit as st
from pathlib import Path
import tempfile
from dotenv import load_dotenv
import time
from elevenlabs import ElevenLabs

load_dotenv()

def text_to_speech_elevenlabs(text_to_speak: str) -> str:
    """Generate audio from text using ElevenLabs TTS."""
    try:
        client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
        audio_stream = client.text_to_speech.convert_as_stream(
            text=text_to_speak,
            voice_id="IKne3meq5aSn9XLyUdCD",  # Charlotte voice
            model_id="eleven_multilingual_v2",
            
        )
        
        # Create a temporary file with a .mp3 extension
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            # Convert generator to bytes and write to file
            audio_bytes = b''.join(chunk for chunk in audio_stream)
            temp_file.write(audio_bytes)
            return temp_file.name
            
    except Exception as e:
        st.error(f"Error generating speech: {str(e)}")
        return None

def speech_to_text_assemblyai(audio_bytes) -> str:
    """Transcribe spoken responses to text using AssemblyAI."""
    assembly_api_key = os.getenv("ASSEMBLYAI_API_KEY")
    headers_auth = {"authorization": assembly_api_key}
    
    try:
        # Upload the audio
        upload_url = "https://api.assemblyai.com/v2/upload"
        upload_response = requests.post(
            upload_url,
            headers=headers_auth,
            data=audio_bytes
        )
        
        if upload_response.status_code != 200:
            st.error("Failed to upload audio file")
            return None
            
        audio_url = upload_response.json()["upload_url"]
        
        # Request transcription
        transcript_url = "https://api.assemblyai.com/v2/transcript"
        json_payload = {"audio_url": audio_url}
        
        response = requests.post(
            transcript_url,
            headers=headers_auth,
            json=json_payload
        )
        
        if response.status_code != 200:
            st.error("Failed to request transcription")
            return None
            
        transcript_id = response.json()["id"]
        
        # Poll for completion
        while True:
            polling_response = requests.get(
                f"{transcript_url}/{transcript_id}",
                headers=headers_auth
            )
            
            if polling_response.status_code != 200:
                st.error("Failed to get transcription status")
                return None
                
            status = polling_response.json()["status"]
            
            if status == "completed":
                return polling_response.json()["text"]
            elif status == "error":
                st.error("Transcription failed")
                return None
                
            time.sleep(1)
            
    except Exception as e:
        st.error(f"Error in speech to text conversion: {str(e)}")
        return None

def cleanup_audio_file(file_path: str):
    """Clean up temporary audio files."""
    try:
        if file_path and Path(file_path).exists():
            Path(file_path).unlink()
    except Exception as e:
        st.error(f"Error cleaning up audio file: {str(e)}") 