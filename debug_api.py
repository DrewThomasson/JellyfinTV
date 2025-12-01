import asyncio
from jellyfin_client import jellyfin
from config import settings

async def test_api():
    settings.JELLYFIN_URL = "https://yourmomsnetflix.com"
    jellyfin.base_url = settings.JELLYFIN_URL
    settings.JELLYFIN_USERNAME = "family"
    settings.JELLYFIN_PASSWORD = "familyiseverything"
    
    print(f"Logging in to {settings.JELLYFIN_URL}...")
    success = await jellyfin.login()
    print(f"Login success: {success}")
    
    if success:
        print("Fetching Genres...")
        genres = await jellyfin.get_genres()
        print(f"Found {len(genres)} genres: {genres[:5]}")
        
        print("Fetching Stats...")
        stats = await jellyfin.get_library_stats()
        print(f"Stats: {stats}")
        
        print("Searching Items (Comedy)...")
        items = await jellyfin.search_items({"genres": ["Comedy"]})
        print(f"Found {len(items)} items: {[i['Name'] for i in items[:5]]}")

if __name__ == "__main__":
    asyncio.run(test_api())
