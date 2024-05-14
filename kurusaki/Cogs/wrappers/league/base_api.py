
import aiohttp
from ...aio_session import aioSessionHandler


class BaseAPI(object):
    def __init__(self, api_key: str,region="na1"):
        self.api_key = api_key
        self.lol_url = f"https://{region}.api.riotgames.com"
        self.riot_url = "https://americas.api.riotgames.com/riot"
        self.headers = {"X-Riot-Token": self.api_key, "Accept": "application/json; charset=utf-8"}
        self.session:aioSessionHandler = aioSessionHandler()

    async def close_session(self):
        await self.session.close_all_sessions()
    
    def set_lol_region(self,region:str):
        self.lol_url = f"https://{region}.api.riotgames.com"

    def set_riot_region(self,region:str):
        self.riot_url = f"https://{region}.api.riotgames.com/riot"


    async def request(self, **kwargs):
        uri = kwargs.get("uri",None)
        if not uri:
            raise ValueError("uri is required")
        if "region" in kwargs:
            region = kwargs.pop("region")
            url = f"https://{region}.api.riotgames.com{uri}"
        if 'continent' in kwargs:
            continent = kwargs.pop("continent")
            url = f"https://{continent}.api.riotgames.com/riot{uri}"
        async with self.session.request(url=url,headers=self.headers, **kwargs) as response:
            if response.status >= 400:
                raise aiohttp.ClientResponseError(request_info=response.request_info,headers=response.headers,status=response.status)
            return await response.json()
        
