import os
import requests
import streamlit as st
from pathlib import Path
import tempfile
from dotenv import load_dotenv
import time
from elevenlabs import ElevenLabs
from google.cloud import texttospeech
from groq import Groq

load_dotenv()

def text_to_speech_elevenlabs(text_to_speak: str) -> str:
    """Generate audio from text using ElevenLabs TTS."""
    try:
        client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
        audio_stream = client.text_to_speech.convert_as_stream(
            text=text_to_speak,
            voice_id="56AoDkrOh6qfVPDXZ7Pt",  # Charlotte voice
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

def text_to_speech_gemini(text_to_speak: str) -> str:
    """Generate audio from text using Google Cloud Text-to-Speech API."""
    try:
        # Instantiate the client
        client = texttospeech.TextToSpeechClient()
        
        # Set the text input to be synthesized
        synthesis_input = texttospeech.SynthesisInput(text=text_to_speak)
        
        # Build the voice request
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US", 
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        )
        
        # Select the type of audio file
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        
        # Perform the text-to-speech request
        response = client.synthesize_speech(
            input=synthesis_input, 
            voice=voice, 
            audio_config=audio_config
        )
        
        # Create a temporary file with a .mp3 extension
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            # Write the response binary audio content to file
            temp_file.write(response.audio_content)
            return temp_file.name
            
    except Exception as e:
        st.error(f"Error generating speech with Google Cloud: {str(e)}")
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

def speech_to_text_groq(audio_bytes) -> str:
    """Transcribe spoken responses to text using Groq's Whisper model."""
    try:
        # Create a temporary file to store the audio
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            # Handle different input types (UploadedFile vs bytes)
            if hasattr(audio_bytes, 'read'):
                # If it's a file-like object (like UploadedFile)
                audio_content = audio_bytes.read()
                temp_file.write(audio_content)
            else:
                # If it's already bytes
                temp_file.write(audio_bytes)
                
            temp_file_path = temp_file.name
        
        # Initialize the Groq client
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        
        # Open the audio file and transcribe it
        with open(temp_file_path, "rb") as file:
            audio_content = file.read()
            
            # Create a transcription of the audio file
            # The API expects a tuple with (filename, content) where filename includes extension
            transcription = client.audio.transcriptions.create(
                file=(os.path.basename(temp_file_path), audio_content),  # Pass as (filename, content) tuple
                model="distil-whisper-large-v3-en",  # Model to use
                language="en",  # Language (English)
                response_format="json",  # Response format
                temperature=0.0  # Temperature (0 for most accurate)
            )
        
        # Cleanup the temp file
        cleanup_audio_file(temp_file_path)
        
        # Return the transcription text
        return transcription.text
        
    except Exception as e:
        st.error(f"Error in Groq speech to text conversion: {str(e)}")
        return None

def cleanup_audio_file(file_path: str):
    """Clean up temporary audio files."""
    try:
        if file_path and Path(file_path).exists():
            Path(file_path).unlink()
    except Exception as e:
        st.error(f"Error cleaning up audio file: {str(e)}") 