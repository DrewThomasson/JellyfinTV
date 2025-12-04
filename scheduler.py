import json
import random
from datetime import datetime, timedelta
from sqlmodel import Session, select
from models import Channel, ScheduleItem, ContentCriteria
from jellyfin_client import jellyfin
from database import engine
from ad_manager import get_ad_for_year

async def fill_channel_schedule(channel_id: int, hours_to_fill: int = 24):
    """
    Fills the schedule for a channel for the next X hours.
    """
    with Session(engine) as session:
        channel = session.get(Channel, channel_id)
        if not channel:
            return

        # Get last scheduled item
        statement = select(ScheduleItem).where(ScheduleItem.channel_id == channel_id).order_by(ScheduleItem.end_time.desc())
        last_item = session.exec(statement).first()
        
        start_time = datetime.now()
        if last_item and last_item.end_time > start_time:
            start_time = last_item.end_time
            
        target_end_time = datetime.now() + timedelta(hours=hours_to_fill)
        
        if start_time >= target_end_time:
            return # Already filled

        # Parse criteria
        try:
            criteria_dict = json.loads(channel.criteria)
        except:
            criteria_dict = {}
        
        # Fetch items from Jellyfin
        items = await jellyfin.search_items(criteria_dict)
        
        # Filter by specific items if selected
        if criteria_dict.get("include_items"):
            included_ids = set(criteria_dict["include_items"])
            # Include if the Item ID is selected OR if the Item's Series ID is selected
            items = [
                i for i in items 
                if i["Id"] in included_ids or i.get("SeriesId") in included_ids
            ]
            
        # Filter by Content Type (Movie/Series)
        content_types = criteria_dict.get("content_types", [])
        if content_types:
            filtered_items = []
            for item in items:
                is_series = bool(item.get("SeriesId"))
                if is_series and "Series" in content_types:
                    filtered_items.append(item)
                elif not is_series and "Movie" in content_types:
                    filtered_items.append(item)
            items = filtered_items
        
        if not items:
            print(f"No items found for channel {channel.name}")
            return

        current_time = start_time
        
        while current_time < target_end_time:
            # Pick a random item
            item = random.choice(items)
            
            # Duration is in ticks (1 tick = 100 nanoseconds) -> seconds = ticks / 10,000,000
            duration_ticks = item.get("RunTimeTicks", 0)
            duration_seconds = int(duration_ticks / 10000000)
            
            if duration_seconds <= 0:
                continue # Skip invalid items
            
            item_year = item.get("ProductionYear", 2000)
            
            # --- Ad Logic ---
            if channel.ads_enabled:
                # 1. Pre-roll / Between Shows Ads
                # If interval is 0, we just play ads between shows.
                # If interval > 0, we might still play ads between shows? Let's assume yes.
                for _ in range(channel.ads_per_break):
                    ad_file = get_ad_for_year(item_year)
                    if ad_file:
                        # Assume ad is 30s for now if we can't get duration easily without ffprobe
                        # Ideally we'd store duration in filename or check it. 
                        # For simulation, let's assume 30s.
                        ad_duration = 30 
                        
                        ad_item = ScheduleItem(
                            channel_id=channel.id,
                            item_id=ad_file, # Use path as ID
                            item_name="Advertisement",
                            item_type="Ad",
                            duration_seconds=ad_duration,
                            start_time=current_time,
                            end_time=current_time + timedelta(seconds=ad_duration),
                            is_ad=True
                        )
                        session.add(ad_item)
                        current_time += timedelta(seconds=ad_duration)

            # 2. Main Content (with potential mid-rolls)
            if channel.ads_enabled and channel.ad_interval_mins > 0:
                # Split content into chunks
                interval_seconds = channel.ad_interval_mins * 60
                remaining_duration = duration_seconds
                offset = 0
                
                while remaining_duration > 0:
                    chunk_duration = min(remaining_duration, interval_seconds)
                    
                    # Add Content Chunk
                    schedule_item = ScheduleItem(
                        channel_id=channel.id,
                        item_id=item["Id"],
                        item_name=item.get("Name", "Unknown"),
                        item_type=item.get("Type", "Unknown"),
                        duration_seconds=chunk_duration,
                        start_time=current_time,
                        end_time=current_time + timedelta(seconds=chunk_duration),
                        media_start_offset=offset
                    )
                    session.add(schedule_item)
                    current_time += timedelta(seconds=chunk_duration)
                    
                    remaining_duration -= chunk_duration
                    offset += chunk_duration
                    
                    # If there is still content remaining, insert mid-roll ads
                    if remaining_duration > 0:
                        for _ in range(channel.ads_per_break):
                            ad_file = get_ad_for_year(item_year)
                            if ad_file:
                                ad_duration = 30
                                ad_item = ScheduleItem(
                                    channel_id=channel.id,
                                    item_id=ad_file,
                                    item_name="Advertisement",
                                    item_type="Ad",
                                    duration_seconds=ad_duration,
                                    start_time=current_time,
                                    end_time=current_time + timedelta(seconds=ad_duration),
                                    is_ad=True
                                )
                                session.add(ad_item)
                                current_time += timedelta(seconds=ad_duration)
            else:
                # No mid-rolls, just play the whole thing
                schedule_item = ScheduleItem(
                    channel_id=channel.id,
                    item_id=item["Id"],
                    item_name=item.get("Name", "Unknown"),
                    item_type=item.get("Type", "Unknown"),
                    duration_seconds=duration_seconds,
                    start_time=current_time,
                    end_time=current_time + timedelta(seconds=duration_seconds)
                )
                session.add(schedule_item)
                current_time += timedelta(seconds=duration_seconds)
            
        session.commit()
