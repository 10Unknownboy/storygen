from fastapi import FastAPI, Request, HTTPException, Depends, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from datetime import datetime
import os

from config import IST_TZ, BASE_DIR, SECRET_KEY
from scheduler import start_scheduler, process_birthdays, process_single_birthday
from instagram_client import instagram_client
from logger import logger
from history import get_recent_uploads
from birthday_manager import get_todays_birthdays, get_next_birthday

# Global state
scheduler_ref = None
start_time = datetime.now(IST_TZ)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global scheduler_ref
    # Startup
    logger.info("Starting up FastAPI application...")
    scheduler_ref = start_scheduler()
    yield
    # Shutdown
    logger.info("Shutting down FastAPI application...")
    if scheduler_ref:
        scheduler_ref.shutdown()

app = FastAPI(lifespan=lifespan, title="Instagram Birthday Story Scheduler")

# Mount templates
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

def verify_secret(token: str):
    if not token or token != SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing secret token")

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    uptime = datetime.now(IST_TZ) - start_time
    
    # Get next run
    next_run = "Unknown"
    if scheduler_ref and scheduler_ref.get_job('daily_birthday_job'):
        job = scheduler_ref.get_job('daily_birthday_job')
        if job.next_run_time:
            next_run = job.next_run_time.strftime('%Y-%m-%d %H:%M:%S %Z')
            
    recent_uploads = get_recent_uploads(limit=5)
    todays_birthdays = get_todays_birthdays()
    next_birthday_info = get_next_birthday()
    
    session_exists = (BASE_DIR / "sessions" / "session.json").exists()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "uptime": str(uptime).split('.')[0],
            "current_time": datetime.now(IST_TZ).strftime('%Y-%m-%d %H:%M:%S %Z'),
            "next_run": next_run,
            "recent_uploads": recent_uploads,
            "todays_birthdays": todays_birthdays,
            "next_birthday_info": next_birthday_info,
            "session_exists": session_exists
        }
    )

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "uptime": str(datetime.now(IST_TZ) - start_time),
        "scheduler_running": scheduler_ref.running if scheduler_ref else False,
        "time": datetime.now(IST_TZ).isoformat()
    }

@app.post("/login")
async def manual_login(token: str):
    verify_secret(token)
    success = instagram_client.login()
    return {"success": success}

@app.post("/logout")
async def manual_logout(token: str):
    verify_secret(token)
    success = instagram_client.logout()
    return {"success": success}

@app.post("/test-story")
async def test_story(token: str, background_tasks: BackgroundTasks, username: str = "manglesh.__.ks"):
    """
    Manually triggers a delayed birthday story upload for a specific user.
    """
    verify_secret(token)
    logger.info(f"Manual /test-story triggered via API for {username}")
    
    def delayed_job():
        import time
        logger.info(f"Waiting 10 seconds before generating and uploading for {username}...")
        time.sleep(10)
        process_single_birthday(username, force_upload=True)
        
    background_tasks.add_task(delayed_job)
    
    return {"status": f"Test pipeline triggered for {username}. It will post in 10 seconds. Check logs for results."}
