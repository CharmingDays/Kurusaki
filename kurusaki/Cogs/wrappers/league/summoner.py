import asyncio
import typing

import aiohttp
from .base_api import BaseAPI


class Summoner(BaseAPI):
    def __init__(self,api_key) -> None:
        super().__init__(api_key=api_key)


    async def close_session(self) -> None:
        await self.session.close_all_sessions()


    async def get_user_by_riot_id(self,summoner_name:str,tag="NA1",continent="americas"):
        uri = f"/riot/account/v1/accounts/by-riot-id/{summoner_name}/{tag}"
        return await self.request(uri=uri,continent=continent)
    

    async def get_account_by_puuid(self,puuid:str,continent="americas"):
        uri = f"/riot/account/v1/accounts/by-puuid/{puuid}"
        return await self.request(uri=uri,continent=continent)
    
    async def get_summoner_by_puuid(self,puuid:str,region="na1"):
        uri = f"/lol/summoner/v4/summoners/by-puuid/{puuid}"
        return await self.request(uri=uri,region=region)
    

    async def get_summoner_by_account_id(self,account_id:str,region="na1"):
        uri = f"/lol/summoner/v4/summoners/by-account/{account_id}"
        return await self.request(uri=uri,region=region)
    
    async def get_summoner_by_summoner_id(self,summoner_id:str,region="na1"):
        uri = f"/lol/summoner/v4/summoners/{summoner_id}"
        return await self.request(uri=uri,region=region)
    

    async def verify_summoner(self,puuid:str,region:str,icon_id:int):
        current_info:typing.Dict = await self.get_summoner_by_puuid(puuid,region=region)
        await asyncio.sleep(60) # wait for user to change icon
        new_info:typing.Dict = await self.get_summoner_by_puuid(puuid,region=region)
        if current_info["profileIconId"] == new_info["profileIconId"]:
            return False
        
        return True



