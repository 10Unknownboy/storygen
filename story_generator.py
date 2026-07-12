import os
from PIL import Image, ImageDraw, ImageFont
import random
from pathlib import Path
from config import STORIES_DIR, FONT_PATH_REGULAR, FONT_PATH_BOLD, BACKGROUND_GRADIENT_START, BACKGROUND_GRADIENT_END, IST_TZ
from datetime import datetime
from logger import logger

def create_gradient_bg(width, height, color1, color2):
    """Create a vertical gradient background."""
    base = Image.new('RGB', (width, height), color1)
    top = Image.new('RGB', (width, height), color2)
    mask = Image.new('L', (width, height))
    mask_data = []
    for y in range(height):
        # Vertical gradient
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

def generate_story(username: str) -> Path:
    """
    Generates a 1080x1920 Instagram Story image for the given username.
    Returns the Path to the generated image.
    """
    width, height = 1080, 1920
    
    # 1. Background
    img = create_gradient_bg(width, height, BACKGROUND_GRADIENT_START, BACKGROUND_GRADIENT_END)
    draw = ImageDraw.Draw(img)
    
    # 2. Decorations
    draw_confetti(draw, width, height)
    
    # 3. Fonts
    try:
        font_large = ImageFont.truetype(str(FONT_PATH_BOLD), 120)
        font_medium = ImageFont.truetype(str(FONT_PATH_REGULAR), 80)
        font_small = ImageFont.truetype(str(FONT_PATH_REGULAR), 50)
    except Exception as e:
        logger.error(f"Error loading fonts: {e}. Falling back to default font.")
        font_large = ImageFont.load_default()
        font_medium = font_large
        font_small = font_large

    # 4. Text - "Happy Birthday"
    text_hb = "Happy Birthday"
    bbox_hb = draw.textbbox((0, 0), text_hb, font=font_large)
    w_hb = bbox_hb[2] - bbox_hb[0]
    x_hb = (width - w_hb) / 2
    y_hb = 700
    
    # Draw text with slight shadow for depth
    draw.text((x_hb + 5, y_hb + 5), text_hb, font=font_large, fill=(0, 0, 0, 128))
    draw.text((x_hb, y_hb), text_hb, font=font_large, fill="white")
    
    # 5. Text - Username
    text_user = f"@{username}"
    bbox_user = draw.textbbox((0, 0), text_user, font=font_medium)
    w_user = bbox_user[2] - bbox_user[0]
    x_user = (width - w_user) / 2
    y_user = y_hb + 180
    
    draw.text((x_user + 3, y_user + 3), text_user, font=font_medium, fill=(0, 0, 0, 128))
    draw.text((x_user, y_user), text_user, font=font_medium, fill="#FFD700")  # Gold

    # 6. Additional message
    msg = "Hope you have a fantastic day!"
    bbox_msg = draw.textbbox((0, 0), msg, font=font_small)
    w_msg = bbox_msg[2] - bbox_msg[0]
    x_msg = (width - w_msg) / 2
    y_msg = y_user + 150
    draw.text((x_msg, y_msg), msg, font=font_small, fill="white")

    # 7. Save
    # We use hyphens instead of colons because Windows does not allow colons in filenames
    timestamp = datetime.now(IST_TZ).strftime("%H-%M-%S_%d%m%Y")
    output_path = STORIES_DIR / f"{username}_{timestamp}.jpg"
    img.save(output_path, quality=95)
    logger.info(f"Generated story for {username} at {output_path}")
    
    return output_path
