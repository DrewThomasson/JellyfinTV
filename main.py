from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select
from typing import List
import json
from datetime import datetime

from database import create_db_and_tables, get_session
from models import Channel, ScheduleItem, ContentCriteria
from config import settings
from jellyfin_client import jellyfin
from scheduler import fill_channel_schedule

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/ads", StaticFiles(directory="ads"), name="ads")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# --- API Routes ---

@app.post("/api/login")
async def login(credentials: dict):
    settings.JELLYFIN_URL = credentials.get("url")
    settings.JELLYFIN_USERNAME = credentials.get("username")
    settings.JELLYFIN_PASSWORD = credentials.get("password")
    
    # Re-init client with new URL if needed (or just rely on settings)
    jellyfin.base_url = settings.JELLYFIN_URL
    
    success = await jellyfin.login()
    if not success:
        raise HTTPException(status_code=401, detail="Login failed")
    return {"status": "success"}

@app.get("/api/channels", response_model=List[Channel])
def get_channels(session: Session = Depends(get_session)):
    channels = session.exec(select(Channel)).all()
    return channels

@app.post("/api/channels", response_model=Channel)
def create_channel(channel: Channel, background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    session.add(channel)
    session.commit()
    session.refresh(channel)
    background_tasks.add_task(fill_channel_schedule, channel.id)
    return channel

@app.put("/api/channels/{channel_id}", response_model=Channel)
def update_channel(channel_id: int, updated_channel: Channel, background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    channel = session.get(Channel, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
        
    channel.name = updated_channel.name
    channel.criteria = updated_channel.criteria
    channel.ads_enabled = updated_channel.ads_enabled
    channel.ad_interval_mins = updated_channel.ad_interval_mins
    channel.ads_per_break = updated_channel.ads_per_break
    
    session.add(channel)
    session.commit()
    session.refresh(channel)
    
    # Trigger refill to apply new settings (might take time to propagate if schedule is full)
    # Ideally we'd clear future schedule but let's keep it simple
    background_tasks.add_task(fill_channel_schedule, channel.id)
    return channel

@app.delete("/api/channels/{channel_id}")
def delete_channel(channel_id: int, session: Session = Depends(get_session)):
    channel = session.get(Channel, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    # Delete associated schedule items first (cascade usually handles this but let's be safe or rely on SQLModel)
    # SQLModel relationships with cascade delete would be ideal, but manual delete is fine for now
    items = session.exec(select(ScheduleItem).where(ScheduleItem.channel_id == channel_id)).all()
    for item in items:
        session.delete(item)
        
    session.delete(channel)
    session.commit()
    return {"status": "deleted"}

@app.get("/api/channels/{channel_id}/now", response_model=dict)
async def get_channel_now(channel_id: int, background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    # Find what's playing now
    now = datetime.now()
    statement = select(ScheduleItem).where(
        ScheduleItem.channel_id == channel_id,
        ScheduleItem.start_time <= now,
        ScheduleItem.end_time > now
    )
    item = session.exec(statement).first()
    
    if not item:
        # Channel is offline/empty. Refill immediately!
        print(f"Channel {channel_id} is offline. Refilling now...")
        await fill_channel_schedule(channel_id)
        
        # Re-query
        item = session.exec(statement).first()
        
        if not item:
            # Still nothing? Maybe no content matches criteria.
            return {"status": "offline"}
            
    # Check if we need to top up the schedule (if less than 5 items remaining)
    future_count = session.exec(select(ScheduleItem).where(
        ScheduleItem.channel_id == channel_id,
        ScheduleItem.start_time > now
    )).all()
    
    if len(future_count) < 5:
        print(f"Channel {channel_id} running low. Scheduling refill.")
        background_tasks.add_task(fill_channel_schedule, channel_id)
        
    # Calculate offset
    offset_seconds = (now - item.start_time).total_seconds()
    
    # Adjust offset for mid-rolls
    final_offset = offset_seconds + item.media_start_offset
    
    return {
        "status": "playing",
        "item": item,
        "offset_seconds": final_offset,
        "is_ad": item.is_ad,
        "jellyfin_url": settings.JELLYFIN_URL,
        "jellyfin_token": settings.JELLYFIN_TOKEN
    }

@app.get("/api/channels/{channel_id}/schedule")
def get_channel_schedule(channel_id: int, session: Session = Depends(get_session)):
    now = datetime.now()
    statement = select(ScheduleItem).where(
        ScheduleItem.channel_id == channel_id,
        ScheduleItem.end_time > now
    ).order_by(ScheduleItem.start_time).limit(20)
    items = session.exec(statement).all()
    return items

@app.post("/api/channels/{channel_id}/refill")
async def refill_channel(channel_id: int, background_tasks: BackgroundTasks):
    background_tasks.add_task(fill_channel_schedule, channel_id)
    return {"status": "scheduled"}

@app.get("/api/library/genres")
async def get_genres():
    return await jellyfin.get_genres()

@app.get("/api/library/stats")
async def get_stats():
    return await jellyfin.get_library_stats()

@app.get("/api/library/tags")
async def get_tags():
    return await jellyfin.get_tags()

@app.get("/api/library/studios")
async def get_studios():
    return await jellyfin.get_studios()

@app.get("/api/library/ratings")
async def get_ratings():
    return await jellyfin.get_ratings()

@app.post("/api/library/search")
async def search_library(criteria: dict):
    # Wrapper to search items based on UI filters
    items = await jellyfin.search_items(criteria)
    
    # Deduplicate: Group by SeriesId
    unique_map = {}
    final_items = []
    
    content_types = criteria.get("content_types", [])
    # If empty, assume all
    if not content_types:
        content_types = ["Movie", "Series"]
        
    for item in items:
        # If it's an episode, use SeriesId as key. If Movie, use Id.
        series_id = item.get("SeriesId")
        item_id = item.get("Id")
        
        if series_id:
            # It's an episode (or part of a series)
            if "Series" not in content_types:
                continue
                
            if series_id not in unique_map:
                # Create a "Show" entry based on this episode
                # We want the Series Name and Series Image
                show_entry = {
                    "Id": series_id,
                    "Name": item.get("SeriesName", item.get("Name")), # Fallback if SeriesName missing
                    "ProductionYear": item.get("ProductionYear"),
                    "Type": "TV Series",
                    "ImageTag": item.get("SeriesPrimaryImageTag"), # Use Series image
                    "IsSeries": True,
                    "EpisodeCount": 1
                }
                unique_map[series_id] = show_entry
                final_items.append(show_entry)
            else:
                # Increment count
                unique_map[series_id]["EpisodeCount"] += 1
        else:
            # It's a Movie or something else without SeriesId
            if "Movie" not in content_types:
                continue
                
            if item_id not in unique_map:
                item["ImageTag"] = item.get("ImageTags", {}).get("Primary")
                item["IsSeries"] = False
                item["Type"] = "Movie" # Explicitly set for UI
                unique_map[item_id] = item
                final_items.append(item)
                
    return final_items

# Serve index
from fastapi.responses import FileResponse
@app.get("/")
async def read_index():
    return FileResponse('static/index.html')

@app.get("/watch/{channel_id}")
async def watch_channel(channel_id: int):
    return FileResponse('static/channel.html')
