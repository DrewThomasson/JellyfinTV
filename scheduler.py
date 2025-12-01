import json
import random
from datetime import datetime, timedelta
from sqlmodel import Session, select
from models import Channel, ScheduleItem, ContentCriteria
from jellyfin_client import jellyfin
from database import engine

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
            items = [i for i in items if i["Id"] in included_ids]
        
        if not items:
            print(f"No items found for channel {channel.name}")
            return

        current_time = start_time
        
        while current_time < target_end_time:
            # Pick a random item
            item = random.choice(items)
            
            # Duration is in ticks (1 tick = 100 nanoseconds) -> seconds = ticks / 10,000,000
            duration_ticks = item.get("RunTimeTicks", 0)
            duration_seconds = duration_ticks / 10000000
            
            if duration_seconds <= 0:
                continue # Skip invalid items
                
            end_time = current_time + timedelta(seconds=duration_seconds)
            
            schedule_item = ScheduleItem(
                channel_id=channel.id,
                item_id=item["Id"],
                item_name=item.get("Name", "Unknown"),
                item_type=item.get("Type", "Unknown"),
                duration_seconds=int(duration_seconds),
                start_time=current_time,
                end_time=end_time
            )
            
            session.add(schedule_item)
            current_time = end_time
            
        session.commit()
