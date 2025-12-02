import os
import random
from pathlib import Path
from typing import Optional, List

ADS_DIR = Path("ads")

def get_ad_for_year(target_year: int) -> Optional[str]:
    """
    Finds a random ad file for the given year.
    If exact year not found, tries to find closest year folder.
    Returns relative path to the ad file (e.g. '1990/coke.mp4') or None.
    """
    if not ADS_DIR.exists():
        return None
        
    # Get all year folders
    try:
        years = [int(d.name) for d in ADS_DIR.iterdir() if d.is_dir() and d.name.isdigit()]
    except ValueError:
        return None
        
    if not years:
        return None
        
    # Find closest year
    closest_year = min(years, key=lambda x: abs(x - target_year))
    
    year_dir = ADS_DIR / str(closest_year)
    
    # Get video files
    extensions = {".mp4", ".mkv", ".avi", ".webm"}
    ads = [f for f in year_dir.iterdir() if f.is_file() and f.suffix.lower() in extensions]
    
    if not ads:
        return None
        
    selected_ad = random.choice(ads)
    return str(selected_ad.relative_to(ADS_DIR))

def validate_ads_exist() -> bool:
    """Checks if any ads exist in the ads directory."""
    if not ADS_DIR.exists():
        return False
    
    for year_dir in ADS_DIR.iterdir():
        if year_dir.is_dir():
            extensions = {".mp4", ".mkv", ".avi", ".webm"}
            if any(f.suffix.lower() in extensions for f in year_dir.iterdir()):
                return True
    return False
