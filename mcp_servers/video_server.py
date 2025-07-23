import os
import uuid
import logging
import base64
import requests
from io import BytesIO
from pydantic import BaseModel
from moviepy.editor import ImageSequenceClip, concatenate_videoclips, AudioFileClip
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
 
STATIC_DIR = "static"
AUDIO_TEMP_PATH = os.path.join(STATIC_DIR, "audio")
VIDEO_OUTPUT_PATH = os.path.join(STATIC_DIR, "videos")
IMAGE_OUTPUT_PATH = os.path.join(STATIC_DIR, "images")
 
# Ensure necessary directories exist
os.makedirs(AUDIO_TEMP_PATH, exist_ok=True)
os.makedirs(VIDEO_OUTPUT_PATH, exist_ok=True)
os.makedirs(IMAGE_OUTPUT_PATH, exist_ok=True)
 
# Load credentials securely from environment variables
APIFY_TOKEN = os.getenv("APIFY_TOKEN")
ACTOR_TASK_ID = os.getenv("ACTOR_TASK_ID")

if not APIFY_TOKEN or not ACTOR_TASK_ID:
    raise ValueError("APIFY_TOKEN and ACTOR_TASK_ID must be set in your .env file.")
 
# --- Pydantic Model ---
class VideoResult(BaseModel):
    intro_text: str
    video_url: str
 
def draw_subtitle_on_image(img: Image.Image, subtitle: str, width=1280, height=720) -> Image.Image:
    draw = ImageDraw.Draw(img)
    font_size = 40
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()
 
    def wrap_text(txt, f, max_width):
        lines = []
        words = txt.split()
        while words:
            line = ''
            while words and f.getlength(line + words[0] + ' ') <= max_width:
                line += (words.pop(0) + ' ')
            lines.append(line.strip())
        return lines
 
    lines = wrap_text(subtitle, font, width - 100)
    total_text_height = sum([font.getbbox(line)[3] for line in lines]) + (len(lines) - 1) * 5
    y = height - total_text_height - 30
 
    for line in lines:
        line_width = font.getbbox(line)[2]
        x = (width - line_width) // 2
        draw.text((x, y), line, font=font, fill=(255, 255, 255))
        y += font.getbbox(line)[3] + 5
 
    return img
 
def create_video_from_script(product_name: str, script: str) -> VideoResult:
    logging.info("Starting video generation process...")
    audio_path = None
    try:
        if "### Audio Script" in script and "### Visual Prompts" in script:
            parts = script.split("### Visual Prompts")
            audio_part = parts[0].replace("### Audio Script", "").strip()
            visual_part = parts[1].strip()
        else:
            raise ValueError("Script must contain both ### Audio Script and ### Visual Prompts sections.")
 
        audio_lines = [line.strip() for line in audio_part.split("\n") if line.strip()]
        visual_prompts = [line.strip() for line in visual_part.split("\n") if line.strip()]
 
        if not audio_lines or not visual_prompts:
            raise ValueError("Both audio and visual prompts must be provided in the script.")
            
        if len(audio_lines) != len(visual_prompts):
            raise ValueError("Number of audio lines and visual prompts must match.")
 
        tts = gTTS(text=audio_part, lang='en', slow=False)
        temp_audio_filename = f"temp_audio_{uuid.uuid4()}.mp3"
        audio_path = os.path.join(AUDIO_TEMP_PATH, temp_audio_filename)
        tts.save(audio_path)
        audio_clip = AudioFileClip(audio_path)
 
        image_paths = []
        for i, image_prompt in enumerate(visual_prompts):
            print(f"Generating image for prompt: {image_prompt}")
            payload = { "prompt": image_prompt.split(". ", 1)[-1], "width": 1024, "height": 768 }
            url = f"https://api.apify.com/v2/actor-tasks/{ACTOR_TASK_ID}/run-sync-get-dataset-items?token={APIFY_TOKEN}"
            res = requests.post(url, json=payload)

            # --- [THE FIX] ---
            # Accept both 200 (OK) and 201 (Created) as successful status codes.
            if res.status_code not in [200, 201]:
                raise ValueError(f"Apify API returned an error (Status {res.status_code}). Check your API Token and Task ID. Response: {res.text}")
            
            response_data = res.json()
            if not isinstance(response_data, list) or not response_data:
                raise ValueError(f"Apify API returned an empty or invalid result for prompt '{image_prompt}'. The response was: {response_data}")

            if 'image' not in response_data[0]:
                raise ValueError(f"Apify API response did not contain an 'image' key for prompt '{image_prompt}'.")
            # --- [END FIX] ---

            base64_data = response_data[0]['image'].split(",")[1]
            img_data = BytesIO(base64.b64decode(base64_data))
            img = Image.open(img_data).convert("RGB").resize((1280, 720))
            img_path = os.path.join(IMAGE_OUTPUT_PATH, f"scene_{i+1}.jpg")
            img.save(img_path)
            image_paths.append(img_path)
 
        slides = []
        for i, img_path in enumerate(image_paths):
            img = Image.open(img_path).convert("RGB")
            subtitled_img = draw_subtitle_on_image(img, audio_lines[i])
            slides.append(np.array(subtitled_img))
 
        duration_per_slide = audio_clip.duration / len(slides)
        clips = [ImageSequenceClip([frame], durations=[duration_per_slide]) for frame in slides]
        final_video = concatenate_videoclips(clips).set_audio(audio_clip)
        final_video.fps = 24
 
        video_filename = f"video_{uuid.uuid4()}.mp4"
        video_filepath = os.path.join(VIDEO_OUTPUT_PATH, video_filename)
        final_video.write_videofile(video_filepath, codec='libx264', audio_codec='aac', threads=4, preset='medium')
 
        video_url = f"/{STATIC_DIR}/videos/{video_filename}"
        logging.info(f"Video created successfully. URL: {video_url}")
 
        return VideoResult( intro_text=f"I've created this video for '{product_name}':", video_url=video_url )
 
    finally:
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)