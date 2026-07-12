import os
import pytz
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file if it exists
load_dotenv()

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
LOGS_DIR = BASE_DIR / 'logs'
SESSIONS_DIR = BASE_DIR / 'sessions'
FONTS_DIR = BASE_DIR / 'fonts'
ASSETS_DIR = BASE_DIR / 'assets'
STORIES_DIR = BASE_DIR / 'stories'
DB_DIR = BASE_DIR / 'database'
MUSIC_DIR = ASSETS_DIR / 'music'
GENERATED_DIR = ASSETS_DIR / 'generated'

# Ensure directories exist
for directory in [LOGS_DIR, SESSIONS_DIR, FONTS_DIR, ASSETS_DIR, STORIES_DIR, DB_DIR, MUSIC_DIR, GENERATED_DIR]:
    directory.mkdir(exist_ok=True)

# Timezone Configuration
TIMEZONE_STR = 'Asia/Kolkata'
IST_TZ = pytz.timezone(TIMEZONE_STR)

# Instagram Credentials
INSTAGRAM_USERNAME = os.getenv('INSTAGRAM_USERNAME', '')
INSTAGRAM_PASSWORD = os.getenv('INSTAGRAM_PASSWORD', '')
INSTAGRAM_SESSION_ID = os.getenv('INSTAGRAM_SESSION_ID', '')

# Application Mode
DRY_RUN = os.getenv('DRY_RUN', 'false').lower() == 'true'
TEST_MODE = os.getenv('TEST_MODE', 'false').lower() == 'true'

# Security
SECRET_KEY = os.getenv('SECRET_KEY', 'default-unsafe-secret-key')

# Upload & Retries
MAX_UPLOAD_RETRIES = int(os.getenv('MAX_UPLOAD_RETRIES', '3'))
UPLOAD_TIMEOUT = int(os.getenv('UPLOAD_TIMEOUT', '60'))  # seconds

# Database
DB_PATH = DB_DIR / 'history.sqlite'
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Scheduler config
SCHEDULE_HOUR = 0
SCHEDULE_MINUTE = 0

# Visuals / Story generator config
FONT_PATH_REGULAR = FONTS_DIR / 'Montserrat-Regular.ttf'
FONT_PATH_BOLD = FONTS_DIR / 'Montserrat-Bold.ttf'

BACKGROUND_GRADIENT_START = (245, 133, 41)  # Instagram-ish orange
BACKGROUND_GRADIENT_END = (221, 42, 123)    # Instagram-ish pink

# Video and Story Asset Config
STORY_DURATION = int(os.getenv('STORY_DURATION', '15'))
USE_CUSTOM_IMAGE = os.getenv('USE_CUSTOM_IMAGE', 'true').lower() == 'true'
CUSTOM_IMAGE_PATH = ASSETS_DIR / "bstory.png"
AUTO_GENERATE_IF_MISSING = os.getenv('AUTO_GENERATE_IF_MISSING', 'true').lower() == 'true'
RANDOM_MUSIC = os.getenv('RANDOM_MUSIC', 'true').lower() == 'true'
CLEANUP_GENERATED_FILES = os.getenv('CLEANUP_GENERATED_FILES', 'true').lower() == 'true'
VIDEO_FPS = int(os.getenv('VIDEO_FPS', '30'))
VIDEO_CODEC = os.getenv('VIDEO_CODEC', 'libx264')
