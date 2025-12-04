import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime
from config import settings

class JellyfinClient:
    def __init__(self):
        self.base_url = settings.JELLYFIN_URL
        self.headers = {
            "X-Emby-Authorization": (
                'MediaBrowser Client="JellyfinTV", Device="Web", DeviceId="jellyfintv-server", Version="1.0.0"'
            )
        }
        if settings.JELLYFIN_TOKEN:
             self.headers["X-Emby-Token"] = settings.JELLYFIN_TOKEN

    async def login(self) -> bool:
        """Logs in and sets the token in settings/headers."""
        url = f"{self.base_url}/Users/AuthenticateByName"
        payload = {
            "Username": settings.JELLYFIN_USERNAME,
            "Pw": settings.JELLYFIN_PASSWORD
        }
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                token = data.get("AccessToken")
                user = data.get("User", {})
                user_id = user.get("Id")
                
                if token:
                    settings.JELLYFIN_TOKEN = token
                    if user_id:
                        settings.JELLYFIN_USER_ID = user_id
                    self.headers["X-Emby-Token"] = token
                    return True
            except Exception as e:
                print(f"Login failed: {e}")
                return False
        return False

    async def get_user_views(self) -> List[Dict[str, Any]]:
        """Gets top level user views (libraries)."""
        if not settings.JELLYFIN_TOKEN:
            return []
        
        url = f"{self.base_url}/Users/{self._get_user_id()}/Views"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json().get("Items", [])
        return []

    async def search_items(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for items based on criteria.
        criteria can include: genres, years, tags, item_types (Movie,Episode)
        """
        if not settings.JELLYFIN_TOKEN:
            return []
        
        user_id = self._get_user_id()
        url = f"{self.base_url}/Users/{user_id}/Items"
        
        params = {
            "Recursive": "true",
            "Recursive": "true",
            "Fields": "Overview,RunTimeTicks,ProductionYear,Genres,Tags,SeriesName,SeriesId,SeriesPrimaryImageTag,ImageTags",
            "IncludeItemTypes": ",".join(criteria.get("item_types", ["Movie", "Episode"])),
        }
        
        if criteria.get("genres"):
            params["Genres"] = "|".join(criteria.get("genres"))
            
        if criteria.get("years"):
            params["Years"] = ",".join(criteria.get("years"))
            
        if criteria.get("tags"):
            params["Tags"] = "|".join(criteria.get("tags"))
            
        if criteria.get("studios"):
            params["Studios"] = "|".join(criteria.get("studios"))
            
        if criteria.get("ratings"):
            params["OfficialRatings"] = "|".join(criteria.get("ratings"))

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, params=params)
            if response.status_code == 200:
                return response.json().get("Items", [])
        return []

    def _get_user_id(self) -> str:
        if settings.JELLYFIN_USER_ID:
            return settings.JELLYFIN_USER_ID
        return "me"
        
    async def get_me(self) -> Optional[str]:
        url = f"{self.base_url}/Users/Me"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json().get("Id")
        return None

    async def get_genres(self) -> List[str]:
        """Fetches all genres from the library."""
        if not settings.JELLYFIN_TOKEN:
            return []
        
        user_id = self._get_user_id()
        url = f"{self.base_url}/Genres"
        params = {
            "Recursive": "true",
            "IncludeItemTypes": "Movie,Series",
            "UserId": user_id
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, params=params)
            if response.status_code == 200:
                return [item["Name"] for item in response.json().get("Items", [])]
        return []

    async def get_library_stats(self) -> Dict[str, Any]:
        """Fetches min/max years and other stats."""
        # Jellyfin doesn't have a direct "min/max year" endpoint easily.
        # We'll do a broad search for items to find years.
        # To be efficient, we might just hardcode reasonable defaults or fetch a subset.
        # Let's try to fetch all items (lightweight) to get years.
        if not settings.JELLYFIN_TOKEN:
            return {"min_year": 1900, "max_year": datetime.now().year}
            
        user_id = self._get_user_id()
        url = f"{self.base_url}/Users/{user_id}/Items"
        params = {
            "Recursive": "true",
            "IncludeItemTypes": "Movie,Series",
            "Fields": "ProductionYear",
            "SortBy": "ProductionYear",
            "SortOrder": "Ascending",
            "Limit": 1
        }
        
        min_year = 1900
        max_year = datetime.now().year
        
        async with httpx.AsyncClient() as client:
            # Get Min
            res_min = await client.get(url, headers=self.headers, params=params)
            if res_min.status_code == 200:
                items = res_min.json().get("Items", [])
                if items:
                    min_year = items[0].get("ProductionYear", 1900)
            
            # Get Max
            params["SortOrder"] = "Descending"
            res_max = await client.get(url, headers=self.headers, params=params)
            if res_max.status_code == 200:
                items = res_max.json().get("Items", [])
                if items:
                    max_year = items[0].get("ProductionYear", max_year)
                    
        return {"min_year": min_year, "max_year": max_year}

    async def get_tags(self) -> List[str]:
        """Fetches all tags from the library."""
        if not settings.JELLYFIN_TOKEN:
            return []
        
        # Tags endpoint usually exists or we search items for tags
        # /Tags endpoint exists in Jellyfin
        url = f"{self.base_url}/Tags"
        params = {"Recursive": "true"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, params=params)
            if response.status_code == 200:
                return [item["Name"] for item in response.json().get("Items", [])]
        return []

    async def get_studios(self) -> List[str]:
        """Fetches all studios."""
        if not settings.JELLYFIN_TOKEN:
            return []
            
        url = f"{self.base_url}/Studios"
        params = {"Recursive": "true"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, params=params)
            if response.status_code == 200:
                return [item["Name"] for item in response.json().get("Items", [])]
        return []

    async def get_ratings(self) -> List[str]:
        """Fetches content ratings (PG, R, etc)."""
        # No direct endpoint for "all used ratings", so we might need to search or use /Localization/ParentalRatings
        # But /Localization/ParentalRatings gives all *possible* ratings, not just used ones.
        # Let's use that for now as it's cleaner.
        if not settings.JELLYFIN_TOKEN:
            return []
            
        url = f"{self.base_url}/Localization/ParentalRatings"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            if response.status_code == 200:
                return [item["Name"] for item in response.json()]
        return []

jellyfin = JellyfinClient()
