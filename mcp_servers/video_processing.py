# mcp_servers/video_processing.py
import speech_recognition as sr
from moviepy.editor import VideoFileClip
import os
from vosk import Model

# --- VOSK Model Setup ---
# IMPORTANT: Update this path to where you unzipped the Vosk model.
VOSK_MODEL_PATH = "vosk-model-small-en-us-0.15" 
if not os.path.exists(VOSK_MODEL_PATH):
    raise FileNotFoundError(
        f"Vosk model not found at '{VOSK_MODEL_PATH}'. "
        "Please download a model from https://alphacephei.com/vosk/models, "
        "unzip it, and set the correct path in mcp_servers/video_processing.py"
    )

recognizer = sr.Recognizer()
model = Model(VOSK_MODEL_PATH)

def extract_text_from_video(video_path: str) -> str:
    """
    Extracts audio from a video file, transcribes it to text using Vosk,
    and then cleans up temporary files.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found at path: {video_path}")

    print(f"Processing video file: {video_path}")
    video_clip = VideoFileClip(video_path)
    
    # Create a unique audio file path in the same directory
    audio_path = os.path.join(os.path.dirname(video_path), f"{os.path.basename(video_path)}.wav")
    
    # Extract audio with specific parameters for Vosk
    video_clip.audio.write_audiofile(audio_path, codec='pcm_s16le', fps=16000)
    video_clip.close()
    print(f"Temporary audio extracted to: {audio_path}")

    text = ""
    with sr.AudioFile(audio_path) as source:
        print("Transcribing audio...")
        audio_data = recognizer.record(source)
        try:
            # Use recognize_vosk for local transcription. It returns a JSON string.
            vosk_result_str = recognizer.recognize_vosk(audio_data)
            # The result is a dictionary string, e.g., {'text': '...'}. We need to parse it.
            import json
            text = json.loads(vosk_result_str).get("text", "")
            print("Transcription successful.")
        except sr.UnknownValueError:
            print("Vosk could not understand the audio.")
            text = "Transcription failed: The audio could not be understood."
        except Exception as e:
            print(f"An unexpected error occurred during transcription: {e}")
            text = f"Transcription failed: {e}"

    # --- Cleanup ---
    try:
        os.remove(audio_path)
        print(f"Cleaned up temporary audio file: {audio_path}")
        os.remove(video_path)
        print(f"Cleaned up source video file: {video_path}")
    except OSError as e:
        print(f"Error during cleanup: {e}")
    
    return text