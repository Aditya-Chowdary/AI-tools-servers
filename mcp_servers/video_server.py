# /Users/adi/AI-tools-servers/mcp_servers/video_server.py

import os
import uuid
import logging
from pydantic import BaseModel
from moviepy.editor import ImageSequenceClip, concatenate_videoclips, AudioFileClip
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# --- Configuration ---
# All paths are relative to the main project root (AI-TOOLS-SERVERS)
STATIC_DIR = "static"
AUDIO_TEMP_PATH = os.path.join(STATIC_DIR, "audio")
VIDEO_OUTPUT_PATH = os.path.join(STATIC_DIR, "videos")

# Ensure all necessary directories exist inside the 'static' folder
os.makedirs(AUDIO_TEMP_PATH, exist_ok=True)
os.makedirs(VIDEO_OUTPUT_PATH, exist_ok=True)

# --- Pydantic Model ---
class VideoResult(BaseModel):
    intro_text: str
    video_url: str

def _create_slide_image(text, slide_type="normal", width=1280, height=720):
    """Internal helper to create a single slide image."""
    # Define colors
    if slide_type == "title":
        bg_color, text_color = (46, 52, 64), (216, 222, 233) # Dark Nord Blue
    else:
        bg_color, text_color = (76, 86, 106), (236, 239, 244) # Nord Gray

    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # --- FIXED: Load default font directly, no file needed ---
    font_size = 60 if slide_type == "title" else 40
    try:
        font = ImageFont.load_default(size=font_size)
    except IOError:
        # Fallback if even default font loading fails (rare)
        font = ImageFont.load_default()


    def wrap_text(txt, f, max_width):
        lines = []
        words = txt.split()
        while words:
            line = ''
            while words and f.getlength(line + words[0]) <= max_width:
                line += (words.pop(0) + ' ')
            lines.append(line.strip())
        return lines

    lines = wrap_text(text, font, width - 150)
    # Calculate total text block height to center it
    total_text_height = sum([font.getbbox(line)[3] for line in lines]) + (len(lines) - 1) * 10
    y = (height - total_text_height) // 2

    for line in lines:
        line_bbox = draw.textbbox((0, 0), line, font=font)
        line_width = line_bbox[2] - line_bbox[0]
        draw.text(((width - line_width) // 2, y), line, font=font, fill=text_color)
        y += font.getbbox(line)[3] + 10
    
    return img

# --- Main Function ---
def create_video_from_script(product_name: str, script: str) -> VideoResult:
    """
    Generates a slideshow video from a script within the same server process.
    """
    logging.info("Starting video generation process...")
    audio_path = None
    try:
        # 1. Generate Voiceover
        tts = gTTS(text=script, lang='en', slow=False)
        temp_audio_filename = f"temp_audio_{uuid.uuid4()}.mp3"
        audio_path = os.path.join(AUDIO_TEMP_PATH, temp_audio_filename)
        tts.save(audio_path)
        audio_clip = AudioFileClip(audio_path)
        
        # 2. Generate Slides
        script_lines = [line.strip() for line in script.split("\n") if line.strip()]
        if not script_lines:
            raise ValueError("Script is empty after processing.")
            
        title_slide = _create_slide_image(product_name, "title")
        content_slides = [_create_slide_image(line, "normal") for line in script_lines]
        
        # 3. Assemble Video Clips
        title_duration = 3.0
        remaining_duration = audio_clip.duration - title_duration
        if remaining_duration <= 0 or len(content_slides) == 0:
             # Handle cases with very short audio or no content slides
            content_duration_per_slide = 2.0 
            remaining_duration = len(content_slides) * content_duration_per_slide
            # Recalculate audio to match new video duration
            audio_clip = audio_clip.set_duration(title_duration + remaining_duration)
        else:
            content_duration_per_slide = remaining_duration / len(content_slides)

        clips = []
        clips.append(ImageSequenceClip([np.array(title_slide)], durations=[title_duration]))
        for slide in content_slides:
            clips.append(ImageSequenceClip([np.array(slide)], durations=[content_duration_per_slide]))

        final_video = concatenate_videoclips(clips).set_audio(audio_clip)

        # --- FIXED: Explicitly set the framerate for the final clip ---
        final_video.fps = 24

        # 4. Write Final Video
        video_filename = f"video_{uuid.uuid4()}.mp4"
        video_filepath = os.path.join(VIDEO_OUTPUT_PATH, video_filename)
        final_video.write_videofile(video_filepath, codec='libx264', audio_codec='aac', threads=4, preset='medium')

        # 5. Return the result with a relative URL
        video_url = f"/{STATIC_DIR}/videos/{video_filename}"
        logging.info(f"Video created successfully. URL: {video_url}")
        
        return VideoResult(
            intro_text=f"I've created this video for '{product_name}':",
            video_url=video_url
        )
    finally:
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)