import os
import json
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ChallengeRequired
from instagrapi.types import StoryMention, UserShort
from logger import logger, mask_secret
from config import INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD, INSTAGRAM_SESSION_ID, SESSIONS_DIR

SESSION_FILE = SESSIONS_DIR / "session.json"

class InstagramClient:
    def __init__(self):
        self.cl = Client()
        # Set timezone offset to India Standard Time (IST is +05:30 -> 19800 seconds)
        self.cl.timezone_offset = 19800
        
    def login(self):
        """
        Attempt to load session, otherwise login with credentials and save session.
        """
        logger.info(f"Attempting login for user: {INSTAGRAM_USERNAME}")
        
        session_loaded = False
        if SESSION_FILE.exists():
            try:
                self.cl.load_settings(SESSION_FILE)
                session_loaded = True
                logger.info("Session settings loaded from file.")
            except Exception as e:
                logger.error(f"Failed to load session from file: {e}")
                
        login_success = False
        if session_loaded:
            try:
                # Provide credentials just in case session is expired
                self.cl.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
                login_success = True
                logger.info("Successfully authenticated using saved session/credentials.")
            except LoginRequired:
                logger.warning("Session is invalid. Need to re-login.")
                login_success = False
            except ChallengeRequired:
                logger.error("Instagram challenge required. Please resolve it manually on a device.")
                login_success = False
            except Exception as e:
                logger.error(f"Error during session validation: {e}")
                login_success = False
                
        if not login_success:
            logger.info("Performing fresh login...")
            try:
                self.cl.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
                login_success = True
                logger.info("Fresh login successful.")
            except Exception as e:
                logger.error(f"Fresh login failed: {e}")
                if INSTAGRAM_SESSION_ID:
                    logger.info("Attempting login via fallback session ID from .env...")
                    try:
                        self.cl.login_by_sessionid(INSTAGRAM_SESSION_ID)
                        login_success = True
                        logger.info("Login via session ID successful.")
                    except Exception as e2:
                        logger.error(f"Login via fallback session ID also failed: {e2}")
                        raise e2
                else:
                    raise e
                
        if login_success:
            self.cl.dump_settings(SESSION_FILE)
            logger.info("Session settings dumped to file.")
            
        return login_success

    def upload_story(self, image_path, username_to_mention):
        """
        Uploads an image to story and mentions the user.
        """
        try:
            logger.info(f"Uploading story for @{username_to_mention}...")
            # We want to mention the user in the story.
            # instagrapi mentions require user_id.
            try:
                user = self.cl.user_info(self.cl.user_id_from_username(username_to_mention))
                user_short = UserShort(pk=user.pk, username=user.username)
                mentions = [
                    StoryMention(
                        user=user_short,
                        x=0.5,
                        y=0.8,
                        width=0.5,
                        height=0.1
                    )
                ]
            except Exception as e:
                logger.warning(f"Could not fetch user_id for {username_to_mention}: {e}. Uploading without interactive mention.")
                mentions = []

            media = self.cl.photo_upload_to_story(
                path=image_path,
                mentions=mentions
            )
            
            logger.info(f"Story uploaded successfully! Media ID: {media.pk}")
            return True, media.pk
        except Exception as e:
            logger.error(f"Failed to upload story: {e}")
            return False, str(e)

    def logout(self):
        """
        Logout and clear session.
        """
        try:
            self.cl.logout()
            if SESSION_FILE.exists():
                os.remove(SESSION_FILE)
            logger.info("Logged out and session cleared.")
            return True
        except Exception as e:
            logger.error(f"Logout failed: {e}")
            return False

# Global instance for easy reuse
instagram_client = InstagramClient()
