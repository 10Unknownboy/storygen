from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import time

from config import DRY_RUN, IST_TZ, SCHEDULE_HOUR, SCHEDULE_MINUTE
from logger import logger
from birthday_manager import get_todays_birthdays
from story_generator import generate_story
from instagram_client import instagram_client
from history import has_uploaded_today, record_upload
from utils import exponential_backoff

# Retry wrapped upload function
@exponential_backoff()
def safe_upload(image_path, username):
    return instagram_client.upload_story(image_path, username)

def process_birthdays():
    """
    Main job that runs at midnight. 
    It fetches birthdays, checks history, generates stories, and posts them.
    """
    logger.info("Starting daily birthday check job...")
    
    # 1. Login or load session
    if not DRY_RUN:
        try:
            success = instagram_client.login()
            if not success:
                logger.error("Instagram login failed. Cannot post stories.")
                return
        except Exception as e:
            logger.error(f"Fatal error during login: {e}")
            return
            
    # 2. Get today's birthdays dynamically
    todays_birthdays = get_todays_birthdays()
    if not todays_birthdays:
        logger.info("No birthdays to process today.")
        return
        
    # 3. Process each birthday
    for user_data in todays_birthdays:
        username = user_data['username']
        birthday = str(datetime.now(IST_TZ).date())
        
        # Check if already processed today to prevent duplicates
        if has_uploaded_today(username):
            logger.info(f"Skipping {username}, already successfully uploaded today.")
            continue
            
        logger.info(f"Processing birthday for @{username}...")
        
        # Generate Story
        try:
            image_path = generate_story(username)
        except Exception as e:
            logger.error(f"Failed to generate story for {username}: {e}")
            record_upload(username, birthday, success=False, error_message=str(e))
            continue
            
        # Upload Story
        if DRY_RUN:
            logger.info(f"[DRY RUN] Would have uploaded {image_path} for @{username}")
            record_upload(username, birthday, success=True, media_id="dry-run", error_message="DRY RUN")
        else:
            try:
                success, result = safe_upload(image_path, username)
                if success:
                    record_upload(username, birthday, success=True, media_id=result)
                else:
                    record_upload(username, birthday, success=False, error_message=result)
            except Exception as e:
                logger.error(f"Failed to upload for {username} after retries: {e}")
                record_upload(username, birthday, success=False, error_message=str(e))
                
        # Slight pause between uploads to avoid spam flags
        if not DRY_RUN and len(todays_birthdays) > 1:
            time.sleep(10)

def process_single_birthday(username: str, force_upload: bool = False):
    """
    Manually triggers a birthday story upload for a single username.
    """
    logger.info(f"Manual single birthday check triggered for @{username}...")
    
    # Login or load session
    if not DRY_RUN or force_upload:
        try:
            success = instagram_client.login()
            if not success:
                logger.error("Instagram login failed. Cannot post story.")
                return
        except Exception as e:
            logger.error(f"Fatal error during login: {e}")
            return
            
    birthday = str(datetime.now(IST_TZ).date())
    
    logger.info(f"Processing birthday for @{username}...")
    
    # Generate Story
    try:
        image_path = generate_story(username)
    except Exception as e:
        logger.error(f"Failed to generate story for {username}: {e}")
        record_upload(username, birthday, success=False, error_message=str(e))
        return
        
    # Upload Story
    if DRY_RUN and not force_upload:
        logger.info(f"[DRY RUN] Would have uploaded {image_path} for @{username}")
        record_upload(username, birthday, success=True, media_id="dry-run", error_message="DRY RUN")
    else:
        try:
            success, result = safe_upload(image_path, username)
            if success:
                record_upload(username, birthday, success=True, media_id=result)
            else:
                record_upload(username, birthday, success=False, error_message=result)
        except Exception as e:
            logger.error(f"Failed to upload for {username} after retries: {e}")
            record_upload(username, birthday, success=False, error_message=str(e))

def start_scheduler():
    scheduler = BackgroundScheduler(timezone=IST_TZ)
    
    # Schedule the job to run every day at SCHEDULE_HOUR:SCHEDULE_MINUTE
    trigger = CronTrigger(hour=SCHEDULE_HOUR, minute=SCHEDULE_MINUTE, timezone=IST_TZ)
    scheduler.add_job(process_birthdays, trigger, id='daily_birthday_job', replace_existing=True)
    
    scheduler.start()
    logger.info(f"Scheduler started. Next run scheduled according to cron (daily at {SCHEDULE_HOUR:02d}:{SCHEDULE_MINUTE:02d} {IST_TZ}).")
    return scheduler
