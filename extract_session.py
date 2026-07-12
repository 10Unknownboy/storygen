import os
from dotenv import load_dotenv
from instagrapi import Client

def main():
    print("Loading credentials from .env...")
    # Make sure we load the .env in the same directory
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    load_dotenv(env_path)
    
    username = os.getenv("INSTAGRAM_USERNAME")
    password = os.getenv("INSTAGRAM_PASSWORD")
    
    if not username or not password or username == "your_username_here":
        print("ERROR: Please set valid INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD in the .env file.")
        return
        
    print(f"Attempting to log in as {username}...")
    cl = Client()
    
    try:
        # Standard login
        cl.login(username, password)
        print("\n=== LOGIN SUCCESSFUL ===")
        
        settings = cl.get_settings()
        cookies = settings.get('authorization_data', {}).get('sessionid')
        
        # Fallback to direct attribute or cookie dict
        if not cookies:
            cookies = settings.get('cookies', {}).get('sessionid')
        if not cookies:
            cookies = getattr(cl, 'sessionid', None)
            
        print("\nYour Session ID is:")
        print("--------------------------------------------------")
        print(cookies)
        print("--------------------------------------------------")
        print("\nCopy the above string and paste it into your .env file as:")
        print(f"INSTAGRAM_SESSION_ID={cookies}")
        print("\n(Note: Never share this token! It grants full access to your account)")
        
    except Exception as e:
        print(f"\n[!] ERROR during login: {e}")
        print("\nInstagram often blocks automated logins with 'Challenge Required' or 'Login Required'.")
        print("If this happens, you have two options:")
        print("1. Open the Instagram app on your phone and click 'This Was Me' to approve the login, then run this script again.")
        print("2. Log into Instagram in your computer's web browser, press F12 to open Developer Tools, go to Application -> Cookies, copy the 'sessionid' value, and manually paste it into your .env file.")

if __name__ == "__main__":
    main()
