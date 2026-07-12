import os
import random
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageOps
import glob
import shutil

from moviepy.editor import ImageClip, AudioFileClip, afx

from config import (
    STORIES_DIR, FONTS_DIR, FONT_PATH_REGULAR, FONT_PATH_BOLD, 
    BACKGROUND_GRADIENT_START, BACKGROUND_GRADIENT_END, IST_TZ,
    USE_CUSTOM_IMAGE, CUSTOM_IMAGE_PATH, AUTO_GENERATE_IF_MISSING,
    MUSIC_DIR, RANDOM_MUSIC, GENERATED_DIR, STORY_DURATION,
    VIDEO_FPS, VIDEO_CODEC
)
from logger import logger

def create_gradient_bg(width, height, color1, color2):
    """Create a vertical gradient background."""
    base = Image.new('RGB', (width, height), color1)
    top = Image.new('RGB', (width, height), color2)
    mask = Image.new('L', (width, height))
    mask_data = []
    for y in range(height):
        mask_data.extend([int(255 * (y / height))] * width)
    mask.putdata(mask_data)
    base.paste(top, (0, 0), mask)
    return base

def draw_confetti(draw, width, height, count=150):
    """Draw random confetti lines/circles on the image."""
    colors = ["#FFFFFF", "#FFD700", "#FF69B4", "#00FFFF", "#32CD32"]
    for _ in range(count):
        x = random.randint(0, width)
        y = random.randint(0, height)
        color = random.choice(colors)
        shape = random.choice(['circle', 'line'])
        size = random.randint(5, 20)
        
        if shape == 'circle':
            draw.ellipse([x, y, x + size, y + size], fill=color)
        else:
            angle_x = random.randint(-20, 20)
            angle_y = random.randint(10, 30)
            draw.line([x, y, x + angle_x, y + angle_y], fill=color, width=random.randint(2, 6))

def generate_fallback_image(username: str, output_path: Path) -> Path:
    """Generates the fallback birthday image."""
    width, height = 1080, 1920
    
    img = create_gradient_bg(width, height, BACKGROUND_GRADIENT_START, BACKGROUND_GRADIENT_END)
    draw = ImageDraw.Draw(img)
    
    draw_confetti(draw, width, height)
    
    try:
        font_large = ImageFont.truetype(str(FONT_PATH_BOLD), 120)
        font_medium = ImageFont.truetype(str(FONT_PATH_REGULAR), 80)
        font_small = ImageFont.truetype(str(FONT_PATH_REGULAR), 50)
    except Exception as e:
        logger.error(f"Error loading fonts: {e}. Falling back to default.")
        font_large = ImageFont.load_default()
        font_medium = font_large
        font_small = font_large

    text_hb = "Happy Birthday"
    bbox_hb = draw.textbbox((0, 0), text_hb, font=font_large)
    w_hb = bbox_hb[2] - bbox_hb[0]
    x_hb = (width - w_hb) / 2
    y_hb = 700
    
    draw.text((x_hb + 5, y_hb + 5), text_hb, font=font_large, fill=(0, 0, 0, 128))
    draw.text((x_hb, y_hb), text_hb, font=font_large, fill="white")
    
    text_user = f"@{username}"
    bbox_user = draw.textbbox((0, 0), text_user, font=font_medium)
    w_user = bbox_user[2] - bbox_user[0]
    x_user = (width - w_user) / 2
    y_user = y_hb + 180
    
    draw.text((x_user + 3, y_user + 3), text_user, font=font_medium, fill=(0, 0, 0, 128))
    draw.text((x_user, y_user), text_user, font=font_medium, fill="#FFD700")

    msg = "Hope you have a fantastic day!"
    bbox_msg = draw.textbbox((0, 0), msg, font=font_small)
    w_msg = bbox_msg[2] - bbox_msg[0]
    x_msg = (width - w_msg) / 2
    y_msg = y_user + 150
    draw.text((x_msg, y_msg), msg, font=font_small, fill="white")

    img.save(output_path, quality=95)
    return output_path

def resize_and_pad(image_path: Path, username: str, target_size=(1080, 1920)) -> Path:
    """Resizes and pads an image to fit exactly within the target size while preserving aspect ratio."""
    img = Image.open(image_path).convert("RGB")
    img = ImageOps.pad(img, target_size, method=Image.Resampling.LANCZOS, color=(0, 0, 0))
    
    # Draw username onto the custom image
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(str(FONTS_DIR / 'BrittanySignature.ttf'), 75)
    except Exception as e:
        logger.error(f"Error loading Brittany Signature font: {e}")
        font = ImageFont.load_default()
        
    text = f"@{username}"
    bbox = draw.textbbox((0, 0), text, font=font)
    w_user = bbox[2] - bbox[0]
    x_user = (target_size[0] - w_user) / 2
    
    # Y-coordinate calibrated to be below the dotted line and above the heart icon
    y_user = 1580
    
    draw.text((x_user + 2, y_user + 2), text, font=font, fill=(0, 0, 0, 128))
    draw.text((x_user, y_user), text, font=font, fill="white")
    
    # Save the processed image to a temp location before converting to video
    temp_img_path = GENERATED_DIR / f"temp_bg_{image_path.name}"
    img.save(temp_img_path, quality=95)
    return temp_img_path

def select_music() -> Path:
    """Scans MUSIC_DIR and returns a random audio track if available."""
    if not RANDOM_MUSIC:
        return None
        
    audio_files = []
    for ext in ['*.mp3', '*.wav', '*.m4a']:
        audio_files.extend(glob.glob(str(MUSIC_DIR / ext)))
        
    if not audio_files:
        return None
        
    return Path(random.choice(audio_files))

def generate_story(username: str) -> dict:
    """
    Generates an MP4 video story for the username.
    Returns a metadata dict.
    """
    timestamp = datetime.now(IST_TZ).strftime("%H-%M-%S_%d%m%Y")
    
    # 1. Image Selection
    base_image_path = None
    method = "Unknown"
    
    if USE_CUSTOM_IMAGE and CUSTOM_IMAGE_PATH.exists():
        logger.info("Custom image found. Using custom image.")
        base_image_path = resize_and_pad(CUSTOM_IMAGE_PATH, username)
        method = "Custom Image"
    elif AUTO_GENERATE_IF_MISSING:
        logger.info("Custom image missing. Generating fallback image.")
        temp_img = GENERATED_DIR / f"fallback_{username}_{timestamp}.jpg"
        base_image_path = generate_fallback_image(username, temp_img)
        method = "Auto Generated Fallback"
    else:
        raise Exception("Custom image not found and AUTO_GENERATE_IF_MISSING is False.")

    # 2. Setup Video Clip
    clip = ImageClip(str(base_image_path)).set_duration(STORY_DURATION)
    
    # 3. Audio Selection & Muxing
    music_path = select_music()
    music_name = "None"
    
    if music_path:
        logger.info(f"Music selected: {music_path.name}")
        music_name = music_path.name
        audio_clip = AudioFileClip(str(music_path))
        # Loop audio to match video duration
        audio_clip = afx.audio_loop(audio_clip, duration=STORY_DURATION)
        # Add audio fade out at the end so it doesn't cut abruptly
        audio_clip = audio_clip.audio_fadeout(1)
        clip = clip.set_audio(audio_clip)
    else:
        logger.info("No music found. Generating silent video.")

    # Apply fade in and out to the visual clip
    clip = clip.fadein(1).fadeout(1)

    # 4. Render Video
    output_mp4 = GENERATED_DIR / f"{username}_{timestamp}.mp4"
    logger.info(f"Rendering video to {output_mp4}...")
    
    # Mute moviepy logging output to keep our logs clean
    clip.write_videofile(
        str(output_mp4),
        fps=VIDEO_FPS,
        codec=VIDEO_CODEC,
        audio_codec="aac",
        threads=1,
        preset="ultrafast",
        logger=None # Suppresses progress bar in terminal
    )
    logger.info("Video rendered successfully.")

    # Cleanup temporary padded background image if we used one
    if base_image_path and base_image_path.exists():
        try:
            os.remove(base_image_path)
        except:
            pass
            
    # Also save a copy to the stories folder as requested
    final_story_path = STORIES_DIR / output_mp4.name
    try:
        shutil.copy(output_mp4, final_story_path)
        logger.info(f"Saved a copy to stories folder: {final_story_path}")
    except Exception as e:
        logger.error(f"Failed to copy to stories folder: {e}")

    return {
        "file_path": output_mp4,
        "method": method,
        "music": music_name,
        "duration": STORY_DURATION,
        "timestamp": timestamp,
        "username": username
    }
