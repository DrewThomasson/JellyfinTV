from typing import Optional, List
from datetime import datetime, timedelta
from sqlmodel import Field, SQLModel, Relationship, JSON
from pydantic import BaseModel

class Channel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    
    # Criteria for content selection (stored as JSON)
    # e.g. {"genres": ["Comedy"], "years": ["1990-1999"], "tags": ["Sitcom"]}
    criteria: str = Field(default="{}") 
    
    # Ad Settings
    ads_enabled: bool = Field(default=False)
    ad_interval_mins: int = Field(default=0) # 0 = between shows only
    ads_per_break: int = Field(default=1)
    
    schedules: List["ScheduleItem"] = Relationship(back_populates="channel")

class ScheduleItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    channel_id: int = Field(foreign_key="channel.id")
    
    # Jellyfin Item Details
    item_id: str
    item_name: str
    item_type: str # Movie, Episode
    duration_seconds: int
    
    # Timing
    start_time: datetime
    end_time: datetime
    
    # Ad / Playback Support
    is_ad: bool = Field(default=False)
    media_start_offset: int = Field(default=0) # Start playing from this second (for mid-rolls)
    
    channel: Channel = Relationship(back_populates="schedules")

# Helper model for Criteria
class ContentCriteria(BaseModel):
    genres: List[str] = []
    years: List[str] = [] # "1990", "1990-1999"
    tags: List[str] = []
    item_types: List[str] = ["Movie", "Episode"]
