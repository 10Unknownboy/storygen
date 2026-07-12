import pandas as pd
from datetime import datetime
from pathlib import Path
from config import BASE_DIR, IST_TZ
from logger import logger
import re

CSV_PATH = BASE_DIR / "birthdays.csv"

def parse_birthday_string(date_str: str):
    """
    Parses a variety of birthday formats into a (month, day) tuple.
    Returns (None, None) if it can't be parsed.
    """
    if pd.isna(date_str) or not isinstance(date_str, str):
        return None, None
        
    s = str(date_str).lower().strip()
    
    # Months mapping
    months = {
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
        'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
    }
    
    # Check for month word
    found_month = None
    for m_str, m_num in months.items():
        if m_str in s:
            found_month = m_num
            break
            
    if found_month:
        match = re.search(r'(\d{1,2})', s)
        day = int(match.group(1)) if match else None
        return found_month, day
        
    # Numeric patterns like DD/MM, MM/DD
    match = re.search(r'(\d{1,2})[/\-\.~•](\d{1,2})', s)
    if match:
        n1, n2 = int(match.group(1)), int(match.group(2))
        if n1 > 12:
            return (n2, n1) # DD/MM
        elif n2 > 12:
            return (n1, n2) # MM/DD
        else:
            return (n2, n1) # Default to DD/MM
            
    return None, None

def get_todays_birthdays():
    """
    Reads the CSV fresh each time, preventing stale cache.
    Returns a list of dicts for users whose birthday is today (IST timezone).
    """
    if not CSV_PATH.exists():
        logger.error(f"Birthdays file not found at {CSV_PATH}")
        return []
        
    try:
        # We read the file every time this is called to handle dynamic updates.
        df = pd.read_csv(CSV_PATH)
    except Exception as e:
        logger.error(f"Failed to read CSV: {e}")
        return []
        
    today = datetime.now(IST_TZ)
    current_month = today.month
    current_day = today.day
    
    todays_bday_users = []
    
    for idx, row in df.iterrows():
        username = row.get('Username')
        bday_str = row.get('Birthday')
        
        if not username or pd.isna(username):
            continue
            
        m, d = parse_birthday_string(bday_str)
        if m == current_month and d == current_day:
            todays_bday_users.append({
                'username': username,
                'display_name': row.get('Display Name', ''),
                'confidence': row.get('Confidence', 'Unknown')
            })
            
    logger.info(f"Found {len(todays_bday_users)} birthdays for today ({today.strftime('%b %d')}).")
    return todays_bday_users

def get_next_birthday():
    """
    Finds the next upcoming birthday after today.
    Returns a dict with 'date' and 'users'.
    """
    if not CSV_PATH.exists():
        return {"date": "None", "users": []}
        
    try:
        df = pd.read_csv(CSV_PATH)
    except Exception as e:
        return {"date": "None", "users": []}
        
    today = datetime.now(IST_TZ)
    current_month = today.month
    current_day = today.day
    
    valid_bdays = []
    for idx, row in df.iterrows():
        username = row.get('Username')
        bday_str = row.get('Birthday')
        if not username or pd.isna(username):
            continue
            
        m, d = parse_birthday_string(bday_str)
        if m and d and m <= 12 and d <= 31:
            valid_bdays.append((m, d, username, bday_str))
            
    if not valid_bdays:
        return {"date": "None", "users": []}
        
    # Sort chronologically by month and day
    valid_bdays.sort(key=lambda x: (x[0], x[1]))
    
    # Find the next date strictly after today
    next_m, next_d = None, None
    for m, d, u, b_str in valid_bdays:
        if m > current_month or (m == current_month and d > current_day):
            next_m, next_d = m, d
            break
            
    # Wrap around to the start of the year if none found after today
    if not next_m:
        next_m, next_d = valid_bdays[0][0], valid_bdays[0][1]
        
    # Collect all users sharing this next birthday date
    users = []
    display_date = None
    for m, d, u, b_str in valid_bdays:
        if m == next_m and d == next_d:
            users.append(u)
            if not display_date:
                display_date = b_str
                
    return {"date": display_date, "users": users}
