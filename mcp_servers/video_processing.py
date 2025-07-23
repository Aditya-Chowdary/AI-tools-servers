# mcp_servers/video_processing.py
import os
from faster_whisper import WhisperModel

# --- Whisper Model Setup ---
# This line downloads and loads the model. It will be cached for future runs.
# "base" is a good balance of speed and accuracy. Other options: "tiny", "small", "medium", "large-v3"
print("Loading Whisper model 'base'...")
model = WhisperModel("base", device="cpu", compute_type="int8")
print("Whisper model loaded successfully.")


def extract_text_from_video(video_path: str) -> str:
    """
    Extracts audio from a video file and transcribes it to text using faster-whisper.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found at path: {video_path}")

    print(f"Processing video file with Whisper: {video_path}")
    
    try:
        # The transcribe method can take the video file path directly.
        # It handles the audio extraction in memory.
        segments, info = model.transcribe(video_path, beam_size=5)

        print(f"Detected language '{info.language}' with probability {info.language_probability}")

        # Join all the transcribed segments into a single string.
        full_transcript = " ".join(segment.text for segment in segments).strip()
        
        print("Transcription successful.")
        
    except Exception as e:
        print(f"An unexpected error occurred during Whisper transcription: {e}")
        # Return a specific error message that can be caught by the server
        return f"Transcription failed: {e}"
    
    return full_transcript