from fastapi import FastAPI, Request, HTTPException, Depends
from apscheduler.triggers.date import DateTrigger
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
import scheduler

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

    scheduled_tasks = []
    if scheduler_ref:
        for job in scheduler_ref.get_jobs():
            if job.id.startswith('manual_'):
                scheduled_tasks.append({
                    "id": job.id,
                    "time": job.next_run_time.strftime('%Y-%m-%d %H:%M:%S %Z') if job.next_run_time else "Running now",
                    "username": job.args[0] if job.args else "Unknown"
                })

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "uptime": str(uptime).split('.')[0],
            "current_time": datetime.now(IST_TZ).strftime('%Y-%m-%d %H:%M:%S %Z'),
            "next_run": next_run,
            "scheduled_tasks": scheduled_tasks,
            "recent_uploads": recent_uploads,
            "todays_birthdays": todays_birthdays,
            "next_birthday_info": next_birthday_info,
            "last_generation_info": scheduler.last_generation_info,
            "session_exists": session_exists
        }
    )

@app.api_route("/health", methods=["GET", "HEAD"])
async def health_check():
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
async def test_story(token: str, username: str = "manglesh.__.ks", target_time: str = None):
    """
    Manually triggers a delayed birthday story upload for a specific user.
    target_time format: HH:MM-DD/MM/YYYY (e.g. 20:30-12/07/2026)
    """
    verify_secret(token)
    
    if target_time:
        try:
            dt = datetime.strptime(target_time, "%H:%M-%d/%m/%Y")
            dt = IST_TZ.localize(dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid target_time format. Use HH:MM-DD/MM/YYYY")
            
        if dt <= datetime.now(IST_TZ):
            raise HTTPException(status_code=400, detail="Target time must be in the future.")
            
        logger.info(f"Manual /test-story scheduled for {username} at {dt}")
        job_id = f"manual_{username}_{int(datetime.now().timestamp())}"
        scheduler_ref.add_job(
            scheduler.process_single_birthday,
            trigger=DateTrigger(run_date=dt, timezone=IST_TZ),
            args=[username, True],
            id=job_id
        )
        return {"status": f"Scheduled story upload for {username} exactly at {dt}"}
    else:
        logger.info(f"Manual /test-story triggered immediately for {username}")
        job_id = f"manual_{username}_immediate_{int(datetime.now().timestamp())}"
        scheduler_ref.add_job(
            scheduler.process_single_birthday,
            args=[username, True],
            id=job_id
        )
        return {"status": f"Test pipeline triggered immediately for {username}."}
